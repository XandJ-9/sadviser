"""
股票数据 Repository - 封装所有股票相关的数据库查询
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_repository import BaseRepository


class StockRepository(BaseRepository):
    """
    股票数据仓库，处理所有与股票相关的数据库操作
    """

    async def get_stock_list_count(self) -> int:
        """
        获取股票列表总数

        Returns:
            股票总数
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()
            result = await conn.fetchval("SELECT COUNT(*) FROM stock_list")
            await self.storage.pool.release(conn)
            return result or 0
        except Exception as e:
            self.logger.error(f"获取股票列表总数失败: {e}")
            raise

    async def get_stock_list(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取股票列表

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            股票列表
        """
        return await self.find_many(
            table_name="stock_list",
            limit=limit,
            offset=offset
        )

    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            股票信息，如果不存在返回 None
        """
        return await self.find_one(
            table_name="stock_list",
            conditions={"symbol": symbol}
        )

    async def get_stock_latest_daily_data(
        self,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取股票最新日K数据

        Args:
            symbol: 股票代码

        Returns:
            最新日K数据
        """
        results = await self.find_many(
            table_name="stock_daily_data",
            conditions={"symbol": symbol},
            sort=[("date", -1)],
            limit=1
        )
        return results[0] if results else None

    async def get_stock_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取股票历史日K数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 返回数量限制

        Returns:
            历史数据列表
        """
        conditions = {"symbol": symbol}
        if start_date:
            conditions["date >="] = start_date
        if end_date:
            conditions["date <="] = end_date

        return await self.find_many(
            table_name="stock_daily_data",
            conditions=conditions,
            sort=[("date", -1)],
            limit=limit
        )

    async def get_stocks_by_date(
        self,
        date: str,
        sort_by: Optional[str] = None,
        sort_order: int = -1,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取指定日期的所有股票数据

        Args:
            date: 日期 (YYYY-MM-DD)
            sort_by: 排序字段
            sort_order: 排序方向 (1: 升序, -1: 降序)
            limit: 返回数量限制

        Returns:
            股票数据列表
        """
        conditions = {"date": date}
        sort = [(sort_by, sort_order)] if sort_by else None

        return await self.find_many(
            table_name="stock_daily_data",
            conditions=conditions,
            sort=sort,
            limit=limit
        )

    async def search_stocks(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索股票（按代码或名称）

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            搜索结果
        """
        # 获取所有股票，然后在内存中过滤
        # TODO: 优化为使用数据库的 LIKE 查询
        all_stocks = await self.find_many(
            table_name="stock_list",
            limit=10000  # 假设股票总数不超过10000
        )

        keyword_lower = keyword.lower()
        filtered = [
            stock for stock in all_stocks
            if keyword_lower in stock.get("symbol", "").lower()
            or keyword_lower in stock.get("name", "").lower()
        ]

        return filtered[:limit]

    async def get_market_overview_data(
        self,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取市场概览数据

        Args:
            date: 指定日期，如果为 None 则使用最新日期

        Returns:
            市场统计数据
        """
        await self._ensure_connection()
        conn = await self.storage._get_connection()

        # 如果没有指定日期，获取最新日期
        if not date:
            date_result = await conn.fetchval(
                "SELECT MAX(date) FROM stock_daily_data"
            )
            date = date_result

        if not date:
            await self.storage.pool.release(conn)
            return {
                "date": None,
                "total_volume": 0,
                "total_stocks": 0,
                "limit_up": 0,
                "limit_down": 0,
                "up": 0,
                "down": 0,
                "flat": 0
            }

        # 获取该日期的所有股票数据
        query = """
            SELECT
                symbol,
                open,
                high,
                low,
                close,
                volume
            FROM stock_daily_data
            WHERE date = $1
        """
        rows = await conn.fetch(query, date)
        await self.storage.pool.release(conn)

        # 统计数据
        total_volume = 0
        limit_up = 0  # 涨停
        limit_down = 0  # 跌停
        up = 0
        down = 0
        flat = 0

        for row in rows:
            close = float(row.get("close", 0))
            open_price = float(row.get("open", 0))
            volume = float(row.get("volume", 0))

            total_volume += volume

            # 计算涨跌幅
            if open_price > 0:
                change_percent = ((close - open_price) / open_price) * 100
            else:
                change_percent = 0

            # 判断涨跌
            if change_percent >= 9.9:
                limit_up += 1
            elif change_percent <= -9.9:
                limit_down += 1
            elif change_percent > 0:
                up += 1
            elif change_percent < 0:
                down += 1
            else:
                flat += 1

        return {
            "date": date,
            "total_volume": round(total_volume, 2),
            "total_stocks": len(rows),
            "limit_up": limit_up,
            "limit_down": limit_down,
            "up": up,
            "down": down,
            "flat": flat
        }

    async def get_hot_stocks(
        self,
        date: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取热门股票（基于成交量）

        Args:
            date: 指定日期，如果为 None 则使用最新日期
            limit: 返回数量限制

        Returns:
            热门股票列表
        """
        await self._ensure_connection()
        conn = await self.storage._get_connection()

        # 如果没有指定日期，获取最新日期
        if not date:
            date_result = await conn.fetchval(
                "SELECT MAX(date) FROM stock_daily_data"
            )
            date = date_result

        if not date:
            await self.storage.pool.release(conn)
            return []

        # 获取成交量最高的股票
        query = """
            SELECT
                symbol,
                close,
                volume,
                open
            FROM stock_daily_data
            WHERE date = $1
            ORDER BY volume DESC
            LIMIT $2
        """
        rows = await conn.fetch(query, date, limit)
        await self.storage.pool.release(conn)

        # 获取股票名称
        result = []
        for row in rows:
            symbol = row.get("symbol")
            stock_info = await self.get_stock_info(symbol)
            name = stock_info.get("name", "") if stock_info else ""

            close = float(row.get("close", 0))
            open_price = float(row.get("open", 0))

            # 计算涨跌幅
            if open_price > 0:
                change_percent = ((close - open_price) / open_price) * 100
            else:
                change_percent = 0.0

            result.append({
                "symbol": symbol,
                "name": name,
                "price": close,
                "change_percent": round(change_percent, 2),
                "volume": float(row.get("volume", 0)),
                "reason": "成交量大" if float(row.get("volume", 0)) > 100000000 else "活跃"
            })

        return result

    async def get_stock_with_latest_price(
        self,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取股票信息及其最新价格

        Args:
            symbol: 股票代码

        Returns:
            包含最新价格的股票信息
        """
        # 获取基本信息
        stock_info = await self.get_stock_info(symbol)
        if not stock_info:
            return None

        # 获取最新价格
        latest_data = await self.get_stock_latest_daily_data(symbol)

        return {
            "symbol": stock_info.get("symbol"),
            "name": stock_info.get("name", ""),
            "source": stock_info.get("source", ""),
            "price": float(latest_data.get("close", 0)) if latest_data else 0,
            "volume": float(latest_data.get("volume", 0)) if latest_data else 0,
            "open": float(latest_data.get("open", 0)) if latest_data else 0,
            "high": float(latest_data.get("high", 0)) if latest_data else 0,
            "low": float(latest_data.get("low", 0)) if latest_data else 0,
        }

    async def get_stocks_with_latest_prices(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取股票列表及其最新价格

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            股票列表和总数
        """
        # 获取总数
        total = await self.get_stock_list_count()

        # 获取股票列表
        stocks = await self.get_stock_list(limit=limit, offset=offset)

        # 为每只股票添加最新价格
        result = []
        for stock in stocks:
            symbol = stock.get("symbol")
            stock_with_price = await self.get_stock_with_latest_price(symbol)
            if stock_with_price:
                result.append(stock_with_price)

        return {
            "stocks": result,
            "total": total
        }
