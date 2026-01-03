"""
数据管理API接口
用于控制数据获取和存储
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from data.crawler.akshare_crawler import AkshareCrawler
from data.storage.postgres_storage import PostgreSQLStorage
from utils.custom_logger import CustomLogger
import logging
import asyncio

router = APIRouter(prefix='/data', tags=['data'])

logger = CustomLogger(
    name="data_api",
    log_level=logging.INFO,
    format_style="simple"
)


# Pydantic模型
class DataFetchRequest(BaseModel):
    """数据获取请求模型"""
    symbols: List[str]
    start_date: str
    end_date: str
    source: str = "akshare"  # 数据源：akshare, sina, tushare


class DataStoreRequest(BaseModel):
    """数据存储请求模型"""
    table_name: str
    data: List[Dict[str, Any]]


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str


# 全局存储实例
storage_instance: Optional[PostgreSQLStorage] = None


def get_storage() -> PostgreSQLStorage:
    """获取存储实例"""
    global storage_instance
    if storage_instance is None:
        from config.base import DATA_STORAGE
        storage_instance = PostgreSQLStorage(DATA_STORAGE["postgresql"])
    return storage_instance


async def initialize_storage():
    """初始化存储连接"""
    logger.info("初始化数据管理API")
    storage = get_storage()
    if not storage.connected:
        await storage.connect()
    logger.info("PostgreSQL存储已连接")


async def cleanup_storage():
    """清理存储连接"""
    logger.info("关闭数据管理API")
    global storage_instance
    if storage_instance and storage_instance.connected:
        await storage_instance.disconnect()


@router.post("/fetch/history")
async def fetch_and_store_history(
    request: DataFetchRequest,
    background_tasks: BackgroundTasks,
    create_table: bool = True
):
    """
    获取历史数据并存储到PostgreSQL

    Args:
        request: 数据获取请求
        background_tasks: 后台任务
        create_table: 是否自动创建表

    Returns:
        任务信息
    """
    task_id = f"task_{datetime.now().timestamp()}"
    storage = get_storage()

    try:
        logger.info(f"创建数据获取任务: {task_id}")
        logger.info(f"股票代码: {request.symbols}")
        logger.info(f"日期范围: {request.start_date} 到 {request.end_date}")
        logger.info(f"数据源: {request.source}")

        # 创建任务记录
        task_data = {
            "id": task_id,
            "type": "fetch_history",
            "status": "pending",
            "message": "任务已创建",
            "progress": 0,
            "total": len(request.symbols),
            "success": 0,
            "failed": 0,
            "meta": {
                "symbols": request.symbols,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "source": request.source
            }
        }
        
        await storage.insert("tasks", task_data)

        # 添加后台任务
        background_tasks.add_task(
            fetch_history_task,
            task_id,
            request.symbols,
            request.start_date,
            request.end_date,
            create_table
        )

        return TaskResponse(
            task_id=task_id,
            status="pending",
            message=f"数据获取任务已创建，共{len(request.symbols)}只股票"
        )

    except Exception as e:
        logger.error(f"创建数据获取任务失败: {e}")
        # 尝试记录失败状态（如果任务ID还没创建成功可能无法记录，这里简单处理）
        try:
            await storage.insert("tasks", {
                "id": task_id,
                "type": "fetch_history",
                "status": "failed",
                "message": str(e),
                "progress": 0,
                "total": len(request.symbols)
            })
        except:
            pass
            
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/realtime")
async def fetch_and_store_realtime(
    symbols: List[str],
    source: str = "akshare",
    store: bool = True
):
    """
    获取实时行情并存储到PostgreSQL

    Args:
        symbols: 股票代码列表
        source: 数据源
        store: 是否存储到数据库

    Returns:
        实时行情数据
    """
    try:
        logger.info(f"获取实时行情: {symbols}, 数据源: {source}")

        # 根据数据源选择crawler
        if source == "akshare":
            crawler = AkshareCrawler()
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据源: {source}")

        # 获取实时行情
        quotes = await crawler.fetch_realtime_quote(symbols)

        if not quotes:
            raise HTTPException(status_code=404, detail="未获取到行情数据")

        # 如果需要存储
        if store:
            storage = get_storage()
            for symbol, quote in quotes.items():
                try:
                    # 准备数据
                    data = {
                        "symbol": symbol,
                        "name": quote.get("name", ""),
                        "price": quote.get("price", 0),
                        "open": quote.get("open", 0),
                        "high": quote.get("high", 0),
                        "low": quote.get("low", 0),
                        "prev_close": quote.get("prev_close", 0),
                        "volume": quote.get("volume", 0),
                        "amount": quote.get("amount", 0),
                        "change": quote.get("change", 0),
                        "change_percent": quote.get("change_percent", 0),
                        "date": quote.get("date", datetime.now().strftime("%Y-%m-%d")),
                        "time": quote.get("time", datetime.now().strftime("%H:%M:%S")),
                        "source": source
                    }

                    # 插入数据库
                    await storage.insert("stock_quotes", data)

                except Exception as e:
                    logger.error(f"存储实时行情失败 {symbol}: {e}")

        return {
            "quotes": quotes,
            "count": len(quotes),
            "timestamp": datetime.now().isoformat(),
            "stored": store
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fetch/stocklist")
async def fetch_and_store_stocklist(
    source: str = "akshare",
    store: bool = False
):
    """
    获取股票列表并存储到PostgreSQL

    Args:
        source: 数据源
        store: 是否存储到数据库

    Returns:
        股票列表
    """
    try:
        logger.info(f"获取股票列表，数据源: {source}")

        if source == "akshare":
            crawler = AkshareCrawler()
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据源: {source}")

        # 获取股票列表
        stock_list = await crawler.fetch_stock_list()

        if stock_list.empty:
            raise HTTPException(status_code=404, detail="未获取到股票列表")

        # 转换为字典列表
        stocks = stock_list.to_dict('records')

        # 如果需要存储
        if store:
            storage = get_storage()
            count = 0

            for stock in stocks:
                try:
                    data = {
                        "symbol": stock.get("code", ""),
                        "name": stock.get("name", ""),
                        "source": source
                    }

                    await storage.insert("stock_list", data)
                    count += 1

                except Exception as e:
                    logger.error(f"存储股票失败 {stock.get('code')}: {e}")

            logger.info(f"成功存储{count}只股票信息")

        return {
            "stocks": stocks[:10],  # 只返回前10个用于预览
            "count": len(stocks),
            "timestamp": datetime.now().isoformat(),
            "stored": store
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_all_tasks():
    """
    获取所有任务列表

    Returns:
        任务列表
    """
    storage = get_storage()
    
    try:
        # 查询任务列表，按创建时间倒序
        tasks = await storage.query(
            "tasks",
            sort=[("created_at", -1)],
            limit=50  # 限制最近50条
        )
        return tasks
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        # 如果表不存在或查询失败，返回空列表
        return []


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    查询任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务状态
    """
    storage = get_storage()
    
    tasks = await storage.query("tasks", conditions={"id": task_id})
    if not tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    return tasks[0]


@router.post("/store/batch")
async def batch_store_data(request: DataStoreRequest):
    """
    批量存储数据到PostgreSQL

    Args:
        request: 数据存储请求

    Returns:
        存储结果
    """
    try:
        logger.info(f"批量存储数据到表: {request.table_name}, 数据量: {len(request.data)}")

        storage = get_storage()

        # 批量插入
        success_count = 0
        failed_count = 0

        for data in request.data:
            try:
                await storage.insert(request.table_name, data)
                success_count += 1
            except Exception as e:
                logger.error(f"插入数据失败: {e}")
                failed_count += 1

        return {
            "table": request.table_name,
            "success": success_count,
            "failed": failed_count,
            "total": len(request.data)
        }

    except Exception as e:
        logger.error(f"批量存储失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query")
async def query_data(
    table_name: str,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """
    查询PostgreSQL中的数据

    Args:
        table_name: 表名
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        limit: 返回数量限制

    Returns:
        查询结果
    """
    try:
        logger.info(f"查询数据: table={table_name}, symbol={symbol}, limit={limit}")

        storage = get_storage()

        # 构建查询条件
        conditions = {}
        if symbol:
            conditions["symbol"] = symbol
        if start_date:
            conditions["date >="] = start_date
        if end_date:
            conditions["date <="] = end_date

        # 查询数据
        results = await storage.query(
            table_name=table_name,
            conditions=conditions,
            limit=limit
        )

        return {
            "table": table_name,
            "data": results,
            "count": len(results) if results else 0
        }

    except Exception as e:
        logger.error(f"查询数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def fetch_history_task(
    task_id: str,
    symbols: List[str],
    start_date: str,
    end_date: str,
    create_table: bool
):
    """
    后台任务：获取历史数据并存储

    Args:
        task_id: 任务ID
        symbols: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        create_table: 是否创建表
    """
    storage = get_storage()
    
    try:
        logger.info(f"开始执行任务: {task_id}")

        # 更新任务状态
        await storage.update(
            "tasks",
            conditions={"id": task_id},
            data={"status": "running", "message": "正在获取数据"}
        )

        # 初始化crawler
        crawler = AkshareCrawler()

        # 如果需要，创建表
        if create_table:
            logger.info("创建数据表")
            # 注意：这里简化处理，生产环境应该使用migration工具
            # await create_stock_history_table(storage)

        # 获取并存储数据
        success_count = 0
        failed_count = 0

        for i, symbol in enumerate(symbols):
            try:
                # 获取历史数据
                df = await crawler.fetch_daily_data(symbol, start_date, end_date)

                if df.empty:
                    logger.warning(f"未获取到数据: {symbol}")
                    failed_count += 1
                    continue

                # 转换为字典列表
                records = df.to_dict('records')

                # 存储到数据库
                for record in records:
                    try:
                        # 准备数据
                        data = {
                            "symbol": record.get("symbol", symbol),
                            "date": record.get("date"),
                            "open": float(record.get("open", 0)),
                            "high": float(record.get("high", 0)),
                            "low": float(record.get("low", 0)),
                            "close": float(record.get("close", 0)),
                            "volume": float(record.get("volume", 0)),
                            "amount": float(record.get("amount", 0)),
                            "source": "akshare"
                        }

                        # 插入数据库
                        await storage.insert("stock_daily_data", data)

                    except Exception as e:
                        logger.error(f"插入数据失败 {symbol} {record.get('date')}: {e}")

                success_count += 1

                # 更新进度
                progress = int((i + 1) / len(symbols) * 100)
                await storage.update(
                    "tasks",
                    conditions={"id": task_id},
                    data={
                        "progress": progress,
                        "success": success_count,
                        "failed": failed_count,
                        "message": f"已完成 {i+1}/{len(symbols)} 只股票"
                    }
                )

                # 避免请求过快
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"获取数据失败 {symbol}: {e}")
                failed_count += 1

        # 更新任务状态
        await storage.update(
            "tasks",
            conditions={"id": task_id},
            data={
                "status": "completed",
                "message": f"任务完成，成功{success_count}只，失败{failed_count}只",
                "success": success_count,
                "failed": failed_count,
                "progress": 100
            }
        )

        logger.info(f"任务完成: {task_id}, 成功: {success_count}, 失败: {failed_count}")

    except Exception as e:
        logger.error(f"任务执行失败: {task_id}, 错误: {e}")
        try:
            await storage.update(
                "tasks",
                conditions={"id": task_id},
                data={
                    "status": "failed",
                    "message": str(e)
                }
            )
        except:
            pass


@router.get("/status")
async def get_system_status():
    """
    获取数据管理系统状态

    Returns:
        系统状态信息
    """
    try:
        storage = get_storage()

        # 统计信息
        # 查询进行中的任务
        running_tasks = await storage.query("tasks", conditions={"status": "running"})
        # 查询完成的任务（最近24小时？）这里简单统计总数可能太慢，暂时先不改查询逻辑，只改数据源
        # 实际生产中应该用count查询，这里storage.query不支持count
        # 暂时先用查询所有记录来统计（注意性能问题，后续应优化）
        
        # 优化：只查最近的任务
        recent_tasks = await storage.query("tasks", limit=100, sort=[("created_at", -1)])
        
        running_count = sum(1 for t in recent_tasks if t.get("status") == "running")
        completed_count = sum(1 for t in recent_tasks if t.get("status") == "completed")

        return {
            "storage_connected": storage.connected,
            "active_tasks": running_count,
            "completed_tasks": completed_count,
            "total_tasks": len(recent_tasks), # 暂时返回最近任务数
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        # 如果出错，返回默认状态
        return {
            "storage_connected": False,
            "active_tasks": 0,
            "completed_tasks": 0,
            "total_tasks": 0,
            "timestamp": datetime.now().isoformat()
        }
