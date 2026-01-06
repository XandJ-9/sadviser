"""
任务管理API接口 - 管理所有数据任务
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from service.api.dependencies import get_task_service
from service.services.task_service import TaskService
from data.crawler.akshare_crawler import AkshareCrawler
from service.core.container import container
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="task_api",
    log_level=logging.INFO,
)

router = APIRouter(prefix='/tasks', tags=['tasks'])


# ==================== Pydantic 模型 ====================

class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""
    task_type: str  # fetch_history, fetch_realtime, fetch_stocklist
    meta: Dict[str, Any]


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str
    task_type: Optional[str] = None
    progress: Optional[int] = None
    total: Optional[int] = None
    success: Optional[int] = None
    failed: Optional[int] = None


class FetchHistoryRequest(BaseModel):
    """获取历史数据请求模型"""
    symbols: List[str]
    start_date: str
    end_date: str
    source: str = "akshare"


# ==================== 后台任务函数 ====================

async def fetch_history_background_task(
    task_id: str,
    symbols: List[str],
    start_date: str,
    end_date: str,
    source: str
):
    """
    后台任务：获取历史数据并存储

    Args:
        task_id: 任务ID
        symbols: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        source: 数据源
    """
    import asyncio

    task_service = container.get_task_service()
    storage = container.get_storage()

    try:
        logger.info(f"开始执行任务: {task_id}")

        # 更新任务状态为运行中
        await task_service.update_task(
            task_id,
            {
                "status": "running",
                "message": "正在获取数据"
            }
        )

        # 初始化crawler
        if source == "akshare":
            crawler = AkshareCrawler()
        else:
            raise ValueError(f"不支持的数据源: {source}")

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
                        data = {
                            "symbol": record.get("symbol", symbol),
                            "date": record.get("date"),
                            "open": float(record.get("open", 0)),
                            "high": float(record.get("high", 0)),
                            "low": float(record.get("low", 0)),
                            "close": float(record.get("close", 0)),
                            "volume": float(record.get("volume", 0)),
                            "amount": float(record.get("amount", 0)),
                            "source": source
                        }
                        await storage.insert("stock_daily_data", data)
                    except Exception as e:
                        logger.error(f"插入数据失败 {symbol} {record.get('date')}: {e}")

                success_count += 1

                # 更新进度
                progress = int((i + 1) / len(symbols) * 100)
                await task_service.update_task(
                    task_id,
                    {
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

        # 更新任务状态为完成
        await task_service.update_task(
            task_id,
            {
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
            await task_service.update_task(
                task_id,
                {
                    "status": "failed",
                    "message": str(e)
                }
            )
        except:
            pass


# ==================== 固定路径（优先匹配） ====================

@router.get("/stats")
async def get_task_statistics(
    service: TaskService = Depends(get_task_service)
):
    """
    获取任务统计信息

    Returns:
        任务统计数据
    """
    try:
        stats = await service.get_task_stats()
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status(
    service: TaskService = Depends(get_task_service)
):
    """
    获取系统状态

    Returns:
        系统状态信息
    """
    try:
        status = await service.get_system_status()
        return status
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_tasks_endpoint(
    limit: int = 10,
    service: TaskService = Depends(get_task_service)
):
    """
    获取最近的任务

    Args:
        limit: 返回数量

    Returns:
        最近的任务列表
    """
    try:
        tasks = await service.get_recent_tasks(limit)
        return {
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        logger.error(f"获取最近任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/history")
async def create_fetch_history_task(
    request: FetchHistoryRequest,
    background_tasks: BackgroundTasks,
    service: TaskService = Depends(get_task_service)
):
    """
    创建历史数据获取任务（后台执行）

    Args:
        request: 获取历史数据请求
        background_tasks: 后台任务
        service: 任务服务

    Returns:
        任务信息
    """
    try:
        logger.info(f"创建历史数据获取任务: {len(request.symbols)}只股票")

        # 创建任务
        meta = {
            "symbols": request.symbols,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "source": request.source
        }

        task_data = await service.create_task("fetch_history", meta)

        # 添加后台任务
        background_tasks.add_task(
            fetch_history_background_task,
            task_data["id"],
            request.symbols,
            request.start_date,
            request.end_date,
            request.source
        )

        return TaskResponse(
            task_id=task_data["id"],
            status=task_data["status"],
            message=f"历史数据获取任务已创建，共{len(request.symbols)}只股票",
            task_type=task_data["type"],
            progress=task_data["progress"],
            total=task_data["total"]
        )

    except Exception as e:
        logger.error(f"创建历史数据获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/realtime")
async def fetch_realtime_quotes(
    symbols: str = Query(..., description="股票代码列表，逗号分隔，例如: 000001,000002"),
    source: str = "akshare",
    store: bool = True
):
    """
    获取实时行情并存储

    Args:
        symbols: 股票代码列表（逗号分隔的字符串）
        source: 数据源
        store: 是否存储到数据库

    Returns:
        实时行情数据
    """
    # 解析股票代码列表
    symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

    if not symbol_list:
        raise HTTPException(status_code=400, detail="至少需要一个股票代码")

    storage = container.get_storage()

    try:
        logger.info(f"获取实时行情: {symbol_list}, 数据源: {source}")

        # 根据数据源选择crawler
        if source == "akshare":
            crawler = AkshareCrawler()
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据源: {source}")

        # 获取实时行情
        quotes = await crawler.fetch_realtime_quote(symbol_list)

        if not quotes:
            raise HTTPException(status_code=404, detail="未获取到行情数据")

        # 如果需要存储
        if store:
            for symbol, quote in quotes.items():
                try:
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
async def fetch_stock_list(
    source: str = "akshare",
    store: bool = False
):
    """
    获取股票列表并存储

    Args:
        source: 数据源
        store: 是否存储到数据库

    Returns:
        股票列表
    """
    storage = container.get_storage()

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


@router.get("")
async def get_all_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: TaskService = Depends(get_task_service)
):
    """
    获取任务列表

    Args:
        status: 任务状态过滤 (pending, running, completed, failed)
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        任务列表
    """
    try:
        tasks = await service.get_tasks(status, limit, offset)
        return {
            "tasks": tasks,
            "count": len(tasks),
            "status": status,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_task(
    request: TaskCreateRequest,
    service: TaskService = Depends(get_task_service)
):
    """
    创建新任务

    Args:
        request: 任务创建请求
        service: 任务服务

    Returns:
        创建的任务信息
    """
    try:
        task_data = await service.create_task(request.task_type, request.meta)
        return TaskResponse(
            task_id=task_data["id"],
            status=task_data["status"],
            message="任务已创建",
            task_type=task_data["type"],
            progress=task_data["progress"],
            total=task_data["total"]
        )
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 参数路径（后匹配） ====================

@router.get("/{task_id}")
async def get_task_by_id(
    task_id: str,
    service: TaskService = Depends(get_task_service)
):
    """
    获取指定任务信息

    Args:
        task_id: 任务ID
        service: 任务服务

    Returns:
        任务信息
    """
    try:
        task = await service.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
