"""
基础 Repository 类 - 封装数据库查询逻辑
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from data.storage.postgres_storage import PostgreSQLStorage
from utils.custom_logger import CustomLogger
import logging


class BaseRepository(ABC):
    """
    数据库访问层基类，封装通用的数据库操作
    """

    def __init__(self, storage: PostgreSQLStorage):
        """
        初始化 Repository

        Args:
            storage: PostgreSQL 存储实例
        """
        self.storage = storage
        self.logger = CustomLogger(
            name=self.__class__.__name__,
            log_level=logging.INFO,
            
        )

    async def _ensure_connection(self):
        """确保数据库连接已建立"""
        if not self.storage.connected:
            await self.storage.connect()

    async def find_one(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        查询单条记录

        Args:
            table_name: 表名
            conditions: 查询条件，如 {"symbol": "000001"}

        Returns:
            单条记录，如果不存在返回 None
        """
        try:
            await self._ensure_connection()
            results = await self.storage.query(
                table_name=table_name,
                conditions=conditions,
                limit=1
            )
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"查询单条记录失败: {table_name}, conditions={conditions}, error={e}")
            raise

    async def find_many(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询多条记录

        Args:
            table_name: 表名
            conditions: 查询条件
            sort: 排序规则，如 [("date", -1), ("volume", -1)]
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            记录列表
        """
        try:
            await self._ensure_connection()
            return await self.storage.query(
                table_name=table_name,
                conditions=conditions,
                sort=sort,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            self.logger.error(f"查询多条记录失败: {table_name}, error={e}")
            raise

    async def count(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计记录数量

        Args:
            table_name: 表名
            conditions: 查询条件

        Returns:
            记录数量
        """
        try:
            # 使用 query 方法获取所有结果，然后计数
            # 注意：对于大数据量，这不够高效，后续可以优化为直接 SQL COUNT 查询
            results = await self.find_many(
                table_name=table_name,
                conditions=conditions,
                limit=100000  # 设置一个较大的限制
            )
            return len(results)
        except Exception as e:
            self.logger.error(f"统计记录数量失败: {table_name}, error={e}")
            raise

    async def aggregate(
        self,
        table_name: str,
        date_column: str,
        value_columns: List[str],
        conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        聚合查询（求和、平均值等）

        Args:
            table_name: 表名
            date_column: 日期列名（用于筛选最新数据）
            value_columns: 需要聚合的数值列名
            conditions: 额外的查询条件

        Returns:
            聚合结果字典
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            # 构建查询
            sum_clauses = [f"COALESCE(SUM({col}), 0) as {col}_sum" for col in value_columns]
            avg_clauses = [f"COALESCE(AVG({col}), 0) as {col}_avg" for col in value_columns]
            count_clause = f"COUNT(*) as count"

            query = f"""
                SELECT {', '.join(sum_cluses)}, {', '.join(avg_clauses)}, {count_clause}
                FROM {table_name}
            """

            params = []
            if conditions:
                where_clauses = []
                for key, value in conditions.items():
                    if ' ' in key:
                        where_clauses.append(f"{key} ${len(params) + 1}")
                    else:
                        where_clauses.append(f"{key} = ${len(params) + 1}")
                    params.append(value)
                query += " WHERE " + " AND ".join(where_clauses)

            result = await conn.fetch(query, *params)
            await self.storage.pool.release(conn)

            if result:
                row = result[0]
                return {
                    **{f"{col}_sum": row[f"{col}_sum"] for col in value_columns},
                    **{f"{col}_avg": row[f"{col}_avg"] for col in value_columns},
                    "count": row["count"]
                }

            return {}
        except Exception as e:
            self.logger.error(f"聚合查询失败: {table_name}, error={e}")
            raise

    async def get_latest_date(self, table_name: str, date_column: str = "date") -> Optional[str]:
        """
        获取表中最新日期

        Args:
            table_name: 表名
            date_column: 日期列名

        Returns:
            最新日期字符串
        """
        try:
            await self._ensure_connection()
            results = await self.storage.query(
                table_name=table_name,
                sort=[(date_column, -1)],
                limit=1
            )
            return results[0].get(date_column) if results else None
        except Exception as e:
            self.logger.error(f"获取最新日期失败: {table_name}, error={e}")
            raise
