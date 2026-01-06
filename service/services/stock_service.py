"""
股票业务逻辑层 Service
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.custom_logger import CustomLogger
import logging


class StockService:
    """
    股票业务逻辑服务
    负责处理股票相关的业务逻辑，不直接处理 HTTP 请求
    """

    def __init__(self, stock_repository):
        """
        初始化服务

        Args:
            stock_repository: 股票数据仓库实例
        """
        self.repository = stock_repository
        self.logger = CustomLogger(
            name="StockService",
            log_level=logging.INFO,
            
        )

    async def get_stock_list(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取股票列表（包含最新价格）

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            股票列表数据
        """
        try:
            self.logger.info(f"获取股票列表: limit={limit}, offset={offset}")
            result = await self.repository.get_stocks_with_latest_prices(
                limit=limit,
                offset=offset
            )

            # 添加模拟指标数据（实际应从技术指标表获取）
            for stock in result.get("stocks", []):
                price = stock.get("price", 0)
                stock["indicators"] = {
                    "ma5": price * 0.99 if price > 0 else 0,
                    "ma10": price * 0.98 if price > 0 else 0,
                    "ma20": price * 0.97 if price > 0 else 0,
                }

            return {
                "stocks": result.get("stocks", []),
                "total": result.get("total", 0),
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            raise

    async def get_stock_detail(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票详情

        Args:
            symbol: 股票代码

        Returns:
            股票详细信息
        """
        try:
            self.logger.info(f"获取股票详情: {symbol}")

            # 获取股票基本信息和最新价格
            stock_data = await self.repository.get_stock_with_latest_price(symbol)
            if not stock_data:
                return None

            price = stock_data.get("price", 0)

            # 构建返回数据
            return {
                "symbol": stock_data.get("symbol"),
                "name": stock_data.get("name", ""),
                "price": price,
                "open": stock_data.get("open", 0),
                "high": stock_data.get("high", 0),
                "low": stock_data.get("low", 0),
                "changePercent": 0.0,  # 需要计算
                "volume": stock_data.get("volume", 0),
                "marketCap": 1000000000,  # 需要计算
                "pe": 15.5,  # 需要从数据库获取
                "indicators": {
                    "ma5": price * 0.99 if price > 0 else 0,
                    "ma10": price * 0.98 if price > 0 else 0,
                    "ma20": price * 0.97 if price > 0 else 0,
                    "rsi": 55.0,
                    "macd": 0.0025
                }
            }
        except Exception as e:
            self.logger.error(f"获取股票详情失败: {symbol}, error={e}")
            raise

    async def get_stock_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 返回数据条数

        Returns:
            历史数据
        """
        try:
            self.logger.info(f"获取股票历史数据: {symbol}, start={start_date}, end={end_date}, limit={limit}")

            data = await self.repository.get_stock_daily_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )

            return {
                "symbol": symbol,
                "data": data if data else [],
                "total": len(data) if data else 0
            }
        except Exception as e:
            self.logger.error(f"获取历史数据失败: {symbol}, error={e}")
            raise

    async def get_stock_quote(self, symbols: List[str]) -> Dict[str, Any]:
        """
        获取实时行情（从数据库最新数据）

        Args:
            symbols: 股票代码列表

        Returns:
            实时行情数据
        """
        try:
            self.logger.info(f"获取实时行情: {symbols}")

            quotes = {}
            for symbol in symbols:
                stock_data = await self.repository.get_stock_with_latest_price(symbol)
                if stock_data:
                    latest_data = await self.repository.get_stock_latest_daily_data(symbol)

                    if latest_data:
                        quotes[symbol] = {
                            "symbol": symbol,
                            "name": stock_data.get("name", ""),
                            "price": stock_data.get("price", 0),
                            "open": stock_data.get("open", 0),
                            "high": stock_data.get("high", 0),
                            "low": stock_data.get("low", 0),
                            "volume": stock_data.get("volume", 0),
                            "date": latest_data.get("date"),
                            "source": "database"
                        }

            return {
                "quotes": quotes,
                "count": len(quotes),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取实时行情失败: {e}")
            raise

    async def get_hot_stocks(self, limit: int = 20) -> Dict[str, Any]:
        """
        获取热门股票

        Args:
            limit: 返回数量

        Returns:
            热门股票列表
        """
        try:
            self.logger.info(f"获取热门股票: limit={limit}")

            stocks = await self.repository.get_hot_stocks(limit=limit)

            return {
                "stocks": stocks,
                "count": len(stocks),
                "date": stocks[0].get("date") if stocks else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取热门股票失败: {e}")
            raise

    async def search_stocks(
        self,
        keyword: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            搜索结果
        """
        try:
            self.logger.info(f"搜索股票: keyword={keyword}, limit={limit}")

            stocks = await self.repository.search_stocks(keyword=keyword, limit=limit)

            return {
                "stocks": stocks,
                "count": len(stocks),
                "keyword": keyword
            }
        except Exception as e:
            self.logger.error(f"搜索股票失败: {keyword}, error={e}")
            raise

    async def get_market_overview(self) -> Dict[str, Any]:
        """
        获取市场概览

        Returns:
            市场统计数据
        """
        try:
            self.logger.info("获取市场概览")

            data = await self.repository.get_market_overview_data()

            return {
                **data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取市场概览失败: {e}")
            raise
