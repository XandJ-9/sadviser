"""
Stock CRUD operations

Provides database operations for stock-related data.
Replaces the StockRepository with direct CRUD functions.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from data.storage.postgres_storage import PostgreSQLStorage
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="stock_crud",
    log_level=logging.INFO
)


class StockCRUD:
    """
    Stock CRUD operations

    This class provides methods for performing database operations
    on stock-related tables. It replaces the repository pattern with
    a simpler, more direct approach.
    """

    def __init__(self, storage: PostgreSQLStorage):
        """
        Initialize StockCRUD with storage instance

        Args:
            storage: Database storage instance
        """
        self.storage = storage
        self.logger = logger

    async def get_stock_list_count(self) -> int:
        """
        Get total count of stocks

        Returns:
            Total number of stocks
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()
            result = await conn.fetchval("SELECT COUNT(*) FROM stock_list")
            await self.storage.pool.release(conn)
            return result or 0
        except Exception as e:
            self.logger.error(f"Failed to get stock list count: {e}")
            raise

    async def get_stock_list(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get paginated stock list

        Args:
            limit: Number of records to return
            offset: Number of records to skip

        Returns:
            List of stocks
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()
            query = """
                SELECT symbol, name, source
                FROM stock_list
                ORDER BY symbol
                LIMIT $1 OFFSET $2
            """
            rows = await conn.fetch(query, limit, offset)
            await self.storage.pool.release(conn)
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get stock list: {e}")
            raise

    async def get_stock_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock information by symbol

        Args:
            symbol: Stock symbol

        Returns:
            Stock information or None if not found
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()
            query = """
                SELECT symbol, name, source
                FROM stock_list
                WHERE symbol = $1
            """
            row = await conn.fetchrow(query, symbol)
            await self.storage.pool.release(conn)
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get stock {symbol}: {e}")
            raise

    async def get_stock_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get latest daily data for a stock

        Args:
            symbol: Stock symbol

        Returns:
            Latest daily data or None
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()
            query = """
                SELECT date, open, high, low, close, volume
                FROM stock_daily_data
                WHERE symbol = $1
                ORDER BY date DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, symbol)
            await self.storage.pool.release(conn)
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get latest data for {symbol}: {e}")
            raise

    async def get_stock_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical daily data for a stock

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum records to return

        Returns:
            List of daily data
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            # Build query conditions
            conditions = ["symbol = $1"]
            params = [symbol]
            param_count = 1

            if start_date:
                param_count += 1
                conditions.append(f"date >= ${param_count}")
                params.append(start_date)

            if end_date:
                param_count += 1
                conditions.append(f"date <= ${param_count}")
                params.append(end_date)

            query = f"""
                SELECT date, open, high, low, close, volume
                FROM stock_daily_data
                WHERE {' AND '.join(conditions)}
                ORDER BY date DESC
                LIMIT ${param_count + 1}
            """
            params.append(limit)

            rows = await conn.fetch(query, *params)
            await self.storage.pool.release(conn)
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get daily data for {symbol}: {e}")
            raise

    async def search_stocks(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search stocks by symbol or name

        Args:
            keyword: Search keyword
            limit: Maximum results to return

        Returns:
            List of matching stocks
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()
            query = """
                SELECT symbol, name, source
                FROM stock_list
                WHERE symbol ILIKE $1 OR name ILIKE $1
                LIMIT $2
            """
            search_pattern = f"%{keyword}%"
            rows = await conn.fetch(query, search_pattern, limit)
            await self.storage.pool.release(conn)
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to search stocks: {e}")
            raise

    async def get_market_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market overview statistics

        Args:
            date: Specific date (YYYY-MM-DD), uses latest if None

        Returns:
            Market statistics
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            # Get latest date if not provided
            date_obj = None
            if not date:
                date_obj = await conn.fetchval(
                    "SELECT MAX(date) FROM stock_daily_data"
                )
                if not date_obj:
                    await self.storage.pool.release(conn)
                    return self._empty_market_stats()
            else:
                # Parse date string to date object
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()

            # Get market data for the date
            query = """
                SELECT
                    COUNT(*) as total_stocks,
                    SUM(volume) as total_volume,
                    SUM(CASE WHEN close > open THEN 1 ELSE 0 END) as up,
                    SUM(CASE WHEN close < open THEN 1 ELSE 0 END) as down,
                    SUM(CASE WHEN close = open THEN 1 ELSE 0 END) as flat,
                    SUM(CASE WHEN ((close - open) / open * 100) >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                    SUM(CASE WHEN ((close - open) / open * 100) <= -9.9 THEN 1 ELSE 0 END) as limit_down
                FROM stock_daily_data
                WHERE date = $1
            """
            row = await conn.fetchrow(query, date_obj)
            await self.storage.pool.release(conn)

            return {
                "date": str(date_obj),  # Convert to string for Pydantic
                "total_stocks": row.get("total_stocks", 0) or 0,
                "total_volume": float(row.get("total_volume", 0) or 0),
                "up": row.get("up", 0) or 0,
                "down": row.get("down", 0) or 0,
                "flat": row.get("flat", 0) or 0,
                "limit_up": row.get("limit_up", 0) or 0,
                "limit_down": row.get("limit_down", 0) or 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get market stats: {e}")
            raise

    async def get_hot_stocks(
        self,
        date: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get hot stocks by volume

        Args:
            date: Specific date (YYYY-MM-DD), uses latest if None
            limit: Maximum results to return

        Returns:
            List of hot stocks
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            # Get latest date if not provided
            date_obj = None
            if not date:
                date_obj = await conn.fetchval(
                    "SELECT MAX(date) FROM stock_daily_data"
                )
                if not date_obj:
                    await self.storage.pool.release(conn)
                    return []
            else:
                # Parse date string to date object
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()

            # Get top stocks by volume
            query = """
                SELECT
                    s.symbol,
                    s.name,
                    d.close,
                    d.open,
                    d.volume
                FROM stock_daily_data d
                LEFT JOIN stock_list s ON d.symbol = s.symbol
                WHERE d.date = $1
                ORDER BY d.volume DESC
                LIMIT $2
            """
            rows = await conn.fetch(query, date_obj, limit)
            await self.storage.pool.release(conn)

            results = []
            for row in rows:
                close = float(row.get("close", 0) or 0)
                open_price = float(row.get("open", 0) or 0)

                # Calculate change percent
                if open_price > 0:
                    change_percent = ((close - open_price) / open_price) * 100
                else:
                    change_percent = 0.0

                results.append({
                    "symbol": row.get("symbol"),
                    "name": row.get("name", ""),
                    "price": close,
                    "change_percent": round(change_percent, 2),
                    "volume": float(row.get("volume", 0) or 0),
                    "reason": "成交量大" if float(row.get("volume", 0) or 0) > 100000000 else "活跃"
                })

            return results
        except Exception as e:
            self.logger.error(f"Failed to get hot stocks: {e}")
            raise

    async def _ensure_connection(self) -> None:
        """Ensure database connection is established"""
        if not self.storage.connected:
            await self.storage.connect()

    def _empty_market_stats(self) -> Dict[str, Any]:
        """Return empty market statistics"""
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
