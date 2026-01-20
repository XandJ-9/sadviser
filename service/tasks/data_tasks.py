"""
数据获取任务模块

提供异步数据获取方法，供 API 层调用
遵循异步非阻塞原则
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from data.crawler.akshare_crawler import AkshareCrawler
from data.storage.postgres_storage import PostgreSQLStorage
from service.crud.task_crud import TaskCRUD
from utils.custom_logger import CustomLogger

logger = CustomLogger(
    name="data_tasks",
    log_level=logging.INFO,
)


class DataTasks:
    """数据获取任务类 - 封装所有数据获取逻辑"""

    def __init__(self, storage: PostgreSQLStorage):
        """
        初始化数据任务

        Args:
            storage: 数据库存储实例
        """
        self.storage = storage
        self._crawler_cache: Dict[str, Any] = {}

    def _get_crawler(self, source: str) -> Any:
        """
        获取crawler实例（带缓存）

        Args:
            source: 数据源名称

        Returns:
            Crawler实例
        """
        if source not in self._crawler_cache:
            if source == "akshare":
                self._crawler_cache[source] = AkshareCrawler()
            else:
                raise ValueError(f"不支持的数据源: {source}")
        return self._crawler_cache[source]

    async def fetch_history_data(
        self,
        task_id: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        source: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        异步获取历史数据

        Args:
            task_id: 任务ID（用于日志追踪）
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源
            progress_callback: 进度回调函数

        Returns:
            执行结果字典
        """
        logger.info(f"[{task_id}] 开始获取历史数据: {len(symbols)}只股票")

        try:
            crawler = self._get_crawler(source)

            success_count = 0
            failed_count = 0
            results = []

            for i, symbol in enumerate(symbols):
                try:
                    # 获取历史数据
                    df = await crawler.fetch_daily_data(symbol, start_date, end_date)

                    if df.empty:
                        logger.warning(f"[{task_id}] 未获取到数据: {symbol}")
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
                            await self.storage.insert("stock_daily_data", data)
                        except Exception as e:
                            logger.error(f"[{task_id}] 插入数据失败 {symbol} {record.get('date')}: {e}")

                    success_count += 1
                    results.append({"symbol": symbol, "status": "success", "count": len(records)})

                    # 更新进度
                    progress = int((i + 1) / len(symbols) * 100)
                    if progress_callback:
                        await progress_callback(
                            task_id,
                            progress=progress,
                            success=success_count,
                            failed=failed_count,
                            message=f"已完成 {i+1}/{len(symbols)} 只股票"
                        )

                    # 避免请求过快
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"[{task_id}] 获取数据失败 {symbol}: {e}")
                    failed_count += 1
                    results.append({"symbol": symbol, "status": "failed", "error": str(e)})

            logger.info(f"[{task_id}] 任务完成，成功: {success_count}, 失败: {failed_count}")

            return {
                "success": True,
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results
            }

        except Exception as e:
            logger.error(f"[{task_id}] 历史数据获取任务失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "success_count": 0,
                "failed_count": len(symbols)
            }

    async def fetch_realtime_data(
        self,
        symbols: List[str],
        source: str,
        store: bool = True
    ) -> Dict[str, Any]:
        """
        异步获取实时行情数据

        Args:
            symbols: 股票代码列表
            source: 数据源
            store: 是否存储到数据库

        Returns:
            实时行情数据
        """
        logger.info(f"获取实时行情: {symbols}, 数据源: {source}")

        try:
            crawler = self._get_crawler(source)

            # 获取实时行情
            quotes = await crawler.fetch_realtime_quote(symbols)

            if not quotes:
                return {
                    "success": False,
                    "quotes": {},
                    "message": "未获取到行情数据"
                }

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
                            "date": quote.get("update_time", datetime.now().strftime("%Y-%m-%d")),
                            "time": quote.get("update_time", datetime.now().strftime("%H:%M:%S")),
                            "source": source
                        }
                        await self.storage.insert("stock_quotes", data)
                    except Exception as e:
                        logger.error(f"存储实时行情失败 {symbol}: {e}")

            return {
                "success": True,
                "quotes": quotes,
                "count": len(quotes),
                "stored": store
            }

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "quotes": {}
            }

    async def fetch_stock_list(
        self,
        source: str,
        store: bool = False
    ) -> Dict[str, Any]:
        """
        异步获取股票列表

        Args:
            source:
            store: 是否存储到数据库

        Returns:
            股票列表数据
        """
        logger.info(f"获取股票列表，数据源: {source}")

        try:
            crawler = self._get_crawler(source)

            # 获取股票列表
            stock_list = await crawler.fetch_stock_list()

            if stock_list.empty:
                return {
                    "success": False,
                    "stocks": [],
                    "message": "未获取到股票列表"
                }

            # 转换为字典列表
            stocks = stock_list.to_dict('records')

            # 如果需要存储
            stored_count = 0
            if store:
                for stock in stocks:
                    try:
                        data = {
                            "symbol": stock.get("code", ""),
                            "name": stock.get("name", ""),
                            "source": source
                        }
                        await self.storage.insert("stock_list", data)
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"存储股票失败 {stock.get('code')}: {e}")

                logger.info(f"成功存储{stored_count}只股票信息")

            return {
                "success": True,
                "stocks": stocks,
                "count": len(stocks),
                "stored": store,
                "stored_count": stored_count
            }

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "stocks": []
            }

    async def update_daily_market_data(self):
        """更新所有股票的日线市场数据"""
        logger.info("开始更新日线市场数据...")
        # 实现占位符
        await asyncio.sleep(1)
        logger.info("日线市场数据更新完成")

    async def update_historical_data(self):
        """更新历史数据"""
        logger.info("开始更新历史数据...")
        await asyncio.sleep(1)
        logger.info("历史数据更新完成")

    async def fetch_history_background_task(
        self,
        task_id: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        source: str
    ) -> Dict[str, Any]:
        """
        后台任务：获取历史数据并存储（完整任务流程）

        这个方法封装了完整的后台任务逻辑，包括：
        - 更新任务状态为运行中
        - 调用数据获取方法
        - 更新任务进度
        - 更新任务最终状态

        Args:
            task_id: 任务ID
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            source: 数据源

        Returns:
            任务执行结果
        """
        crud = TaskCRUD(self.storage)

        try:
            logger.info(f"开始执行任务: {task_id}")

            # 更新任务状态为运行中
            await crud.update_task(
                task_id,
                {
                    "status": "running",
                    "message": "正在获取数据"
                }
            )

            # 定义进度回调函数
            async def progress_callback(
                task_id: str,
                progress: int,
                success: int,
                failed: int,
                message: str
            ):
                """更新任务进度"""
                await crud.update_task(
                    task_id,
                    {
                        "progress": progress,
                        "success": success,
                        "failed": failed,
                        "message": message
                    }
                )

            # 调用数据获取方法
            result = await self.fetch_history_data(
                task_id=task_id,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                source=source,
                progress_callback=progress_callback
            )

            # 更新任务状态为完成
            if result["success"]:
                await crud.update_task(
                    task_id,
                    {
                        "status": "completed",
                        "message": f"任务完成，成功{result['success_count']}只，失败{result['failed_count']}只",
                        "success": result["success_count"],
                        "failed": result["failed_count"],
                        "progress": 100,
                        "completed_at": datetime.now()
                    }
                )
                logger.info(f"任务完成: {task_id}, 成功: {result['success_count']}, 失败: {result['failed_count']}")
            else:
                await crud.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "message": f"任务失败: {result.get('error', '未知错误')}",
                        "error": result.get("error"),
                        "completed_at": datetime.now()
                    }
                )

            return result

        except Exception as e:
            logger.error(f"任务执行失败: {task_id}, 错误: {e}")
            try:
                await crud.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "message": str(e),
                        "error": str(e),
                        "completed_at": datetime.now()
                    }
                )
            except:
                pass

            return {
                "success": False,
                "error": str(e)
            }

    async def fetch_realtime_background_task(
        self,
        task_id: str,
        symbols: List[str],
        source: str,
        store: bool = True
    ) -> Dict[str, Any]:
        """
        后台任务：获取实时行情数据（完整任务流程）

        Args:
            task_id: 任务ID
            symbols: 股票代码列表
            source: 数据源
            store: 是否存储到数据库

        Returns:
            任务执行结果
        """
        crud = TaskCRUD(self.storage)

        try:
            logger.info(f"开始执行实时行情任务: {task_id}")

            # 更新任务状态为运行中
            await crud.update_task(
                task_id,
                {
                    "status": "running",
                    "message": f"正在获取{len(symbols)}只股票的实时行情"
                }
            )

            # 调用数据获取方法
            result = await self.fetch_realtime_data(
                symbols=symbols,
                source=source,
                store=store
            )

            # 更新任务状态为完成
            if result["success"]:
                await crud.update_task(
                    task_id,
                    {
                        "status": "completed",
                        "message": f"实时行情获取完成，共{result['count']}只股票",
                        "success": result["count"],
                        "failed": 0,
                        "progress": 100,
                        "completed_at": datetime.now()
                    }
                )
                logger.info(f"实时行情任务完成: {task_id}, 数量: {result['count']}")
            else:
                await crud.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "message": f"任务失败: {result.get('error', '未知错误')}",
                        "error": result.get("error"),
                        "completed_at": datetime.now()
                    }
                )

            return result

        except Exception as e:
            logger.error(f"实时行情任务执行失败: {task_id}, 错误: {e}")
            try:
                await crud.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "message": str(e),
                        "error": str(e),
                        "completed_at": datetime.now()
                    }
                )
            except:
                pass

            return {
                "success": False,
                "error": str(e)
            }

    async def fetch_stocklist_background_task(
        self,
        task_id: str,
        source: str,
        store: bool = False
    ) -> Dict[str, Any]:
        """
        后台任务：获取股票列表（完整任务流程）

        Args:
            task_id: 任务ID
            source: 数据源
            store: 是否存储到数据库

        Returns:
            任务执行结果
        """
        crud = TaskCRUD(self.storage)

        try:
            logger.info(f"开始执行股票列表获取任务: {task_id}")

            # 更新任务状态为运行中
            await crud.update_task(
                task_id,
                {
                    "status": "running",
                    "message": "正在获取股票列表"
                }
            )

            # 调用数据获取方法
            result = await self.fetch_stock_list(
                source=source,
                store=store
            )

            # 更新任务状态为完成
            if result["success"]:
                await crud.update_task(
                    task_id,
                    {
                        "status": "completed",
                        "message": f"股票列表获取完成，共{result['count']}只股票",
                        "success": result["count"],
                        "failed": 0,
                        "progress": 100,
                        "completed_at": datetime.now()
                    }
                )
                logger.info(f"股票列表任务完成: {task_id}, 数量: {result['count']}")
            else:
                await crud.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "message": f"任务失败: {result.get('error', '未知错误')}",
                        "error": result.get("error"),
                        "completed_at": datetime.now()
                    }
                )

            return result

        except Exception as e:
            logger.error(f"股票列表任务执行失败: {task_id}, 错误: {e}")
            try:
                await crud.update_task(
                    task_id,
                    {
                        "status": "failed",
                        "message": str(e),
                        "error": str(e),
                        "completed_at": datetime.now()
                    }
                )
            except:
                pass

            return {
                "success": False,
                "error": str(e)
            }
