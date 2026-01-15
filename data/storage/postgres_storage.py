import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime

import asyncpg
from asyncpg import Connection, Pool

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from data.storage.base_storage import BaseStorage



class PostgreSQLStorage(BaseStorage):
    """PostgreSQL存储组件，用于存储结构化的股票数据"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化PostgreSQL存储
        
        :param config: 配置字典，应包含host, port, user, password, database等
        """
        super().__init__(config)
        self.pool: Optional[Pool] = None
        self.min_size = config.get('min_size', 5)
        self.max_size = config.get('max_size', 20)
    
    async def connect(self) -> bool:
        """
        连接到PostgreSQL数据库，创建连接池
        
        :return: 连接成功返回True，否则返回False
        """
        if self.connected and self.pool:
            return True
            
        try:
            # 创建连接池
            self.pool = await asyncpg.create_pool(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', ''),
                database=self.config.get('database', 'stock_db'),
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.config.get('timeout', 60)
            )
            
            if self.pool:
                self.connected = True
                self.logger.info(f"成功连接到PostgreSQL数据库: {self.config.get('host')}:{self.config.get('port')}/{self.config.get('database')}")
                return True
            else:
                self.logger.error("创建PostgreSQL连接池失败")
                return False
                
        except Exception as e:
            self._handle_exception(e, "连接PostgreSQL")
            return False
    
    async def disconnect(self) -> None:
        """断开与PostgreSQL数据库的连接，关闭连接池"""
        if self.pool:
            try:
                await self.pool.close()
                self.logger.info("已关闭PostgreSQL连接池")
            except Exception as e:
                self._handle_exception(e, "关闭PostgreSQL连接")
        
        self.connected = False
        self.pool = None
    
    async def _get_connection(self) -> Optional[Connection]:
        """获取一个数据库连接"""
        if not self.connected or not self.pool:
            # 如果未连接，则尝试重新连接
            if not await self.connect():
                return None
                
        try:
            return await self.pool.acquire()
        except Exception as e:
            self._handle_exception(e, "获取PostgreSQL连接")
            return None
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        插入单条数据
        
        :param table_name: 表名
        :param data: 要插入的数据字典
        :return: 插入成功返回True，否则返回False
        """
        # 添加时间戳
        data = self._add_timestamps(data)
        
        # 构建SQL语句
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(data))])
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        conn = await self._get_connection()
        if not conn:
            return False
            
        try:
            await conn.execute(sql, *data.values())
            return True
        except Exception as e:
            self._handle_exception(e, f"插入数据到表 {table_name}")
            return False
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        批量插入数据
        
        :param table_name: 表名
        :param data_list: 要插入的数据字典列表
        :return: 一个元组，包含(成功插入数量, 总数量)
        """
        if not data_list:
            return (0, 0)
            
        total = len(data_list)
        success = 0
        
        # 为每条数据添加时间戳
        processed_data = [self._add_timestamps(data) for data in data_list]
        
        # 获取所有列名（假设所有数据的列结构相同）
        columns = processed_data[0].keys()
        columns_str = ", ".join(columns)
        
        # 构建批量插入的SQL
        placeholders = []
        values = []
        
        for i, data in enumerate(processed_data):
            row_placeholders = [f"${i*len(columns) + j + 1}" for j in range(len(columns))]
            placeholders.append(f"({', '.join(row_placeholders)})")
            values.extend(data.values())
        
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES {', '.join(placeholders)}"
        self.logger.debug(f"批量插入SQL: {sql} with values {values}")
        conn = await self._get_connection()
        if not conn:
            return (0, total)
            
        try:
            result = await conn.execute(sql, *values)
            # 解析结果，获取插入的行数
            # 例如: "INSERT 0 5" 表示插入了5行
            success = int(result.split()[-1])
            return (success, total)
        except Exception as e:
            self._handle_exception(e, f"批量插入数据到表 {table_name}")
            return (0, total)
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def update(self, table_name: str, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """
        更新数据
        
        :param table_name: 表名
        :param conditions: 更新条件
        :param data: 要更新的数据
        :return: 受影响的行数
        """
        if not data:
            return 0
            
        # 添加更新时间戳
        data = self._add_timestamps(data)
        # 处理条件
        conditions = self._validate_conditions(conditions)
        
        # 构建UPDATE语句
        set_clause = ", ".join([f"{key} = ${i+1}" for i, key in enumerate(data.keys())])
        where_clause, where_params = self._build_where_clause(conditions, len(data))
        
        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + where_params
        
        conn = await self._get_connection()
        if not conn:
            return 0
            
        try:
            result = await conn.execute(sql, *params)
            # 解析结果，获取更新的行数
            # 例如: "UPDATE 5" 表示更新了5行
            return int(result.split()[-1])
        except Exception as e:
            self._handle_exception(e, f"更新表 {table_name} 数据")
            return 0
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """
        删除数据
        
        :param table_name: 表名
        :param conditions: 删除条件
        :return: 受影响的行数
        """
        conditions = self._validate_conditions(conditions)
        
        # 构建DELETE语句
        where_clause, where_params = self._build_where_clause(conditions, 0)
        sql = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        conn = await self._get_connection()
        if not conn:
            return 0
            
        try:
            result = await conn.execute(sql, *where_params)
            # 解析结果，获取删除的行数
            # 例如: "DELETE 5" 表示删除了5行
            return int(result.split()[-1])
        except Exception as e:
            self._handle_exception(e, f"删除表 {table_name} 数据")
            return 0
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def query(self, 
                   table_name: str, 
                   conditions: Optional[Dict[str, Any]] = None,
                   fields: Optional[List[str]] = None,
                   sort: Optional[List[Tuple[str, int]]] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        :param table_name: 表名
        :param conditions: 查询条件
        :param fields: 要返回的字段列表，None表示返回所有字段
        :param sort: 排序条件，列表中的元组为(字段名, 排序方向)，1为升序，-1为降序
        :param limit: 返回结果的最大数量
        :param offset: 结果偏移量，用于分页
        :return: 查询结果列表
        """
        conditions = self._validate_conditions(conditions or {})
        
        # 构建SELECT语句
        fields_str = "*"
        if fields:
            fields_str = ", ".join(fields)
            
        where_clause, where_params = self._build_where_clause(conditions, 0)
        
        sql_parts = [f"SELECT {fields_str} FROM {table_name}"]
        if where_clause:
            sql_parts.append(f"WHERE {where_clause}")
            
        # 处理排序
        if sort:
            sort_parts = []
            for field, direction in sort:
                sort_dir = "ASC" if direction == 1 else "DESC"
                sort_parts.append(f"{field} {sort_dir}")
            sql_parts.append(f"ORDER BY {', '.join(sort_parts)}")
            
        # 处理分页
        if limit is not None:
            sql_parts.append(f"LIMIT {limit}")
        if offset is not None:
            sql_parts.append(f"OFFSET {offset}")
            
        sql = " ".join(sql_parts)
        
        conn = await self._get_connection()
        if not conn:
            return []
            
        try:
            rows = await conn.fetch(sql, *where_params)
            # 将Record对象转换为字典
            return [dict(row) for row in rows]
        except Exception as e:
            self._handle_exception(e, f"查询表 {table_name} 数据")
            return []
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """
        创建表
        
        :param table_name: 表名
        :param schema: 表结构定义，例如:
                       {
                           "id": "SERIAL PRIMARY KEY",
                           "code": "VARCHAR(20) NOT NULL",
                           "date": "DATE NOT NULL",
                           "open": "NUMERIC(10, 2)",
                           "high": "NUMERIC(10, 2)",
                           "low": "NUMERIC(10, 2)",
                           "close": "NUMERIC(10, 2)",
                           "volume": "BIGINT",
                           "created_at": "TIMESTAMPTZ",
                           "updated_at": "TIMESTAMPTZ"
                       }
        :return: 创建成功返回True，否则返回False
        """
        # 构建CREATE TABLE语句
        columns = [f"{name} {type_def}" for name, type_def in schema.items()]
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
        
        # 添加索引定义
        if "indexes" in self.config:
            indexes = self.config["indexes"].get(table_name, [])
            for index in indexes:
                index_name = index.get("name", f"idx_{table_name}_{'_'.join(index['columns'])}")
                columns_str = ", ".join(index["columns"])
                unique = "UNIQUE" if index.get("unique", False) else ""
                sql += f"; CREATE {unique} INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
        
        conn = await self._get_connection()
        if not conn:
            return False
            
        try:
            await conn.execute(sql)
            self.logger.info(f"表 {table_name} 创建成功或已存在")
            return True
        except Exception as e:
            self._handle_exception(e, f"创建表 {table_name}")
            return False
        finally:
            if conn:
                await self.pool.release(conn)
    
    async def exists(self, table_name: str, conditions: Dict[str, Any]) -> bool:
        """
        检查是否存在符合条件的记录
        
        :param table_name: 表名
        :param conditions: 检查条件
        :return: 存在返回True，否则返回False
        """
        conditions = self._validate_conditions(conditions)
        
        # 构建EXISTS查询
        where_clause, where_params = self._build_where_clause(conditions, 0)
        sql = f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE {where_clause})"
        
        conn = await self._get_connection()
        if not conn:
            return False
            
        try:
            result = await conn.fetchval(sql, *where_params)
            return result
        except Exception as e:
            self._handle_exception(e, f"检查表 {table_name} 记录存在性")
            return False
        finally:
            if conn:
                await self.pool.release(conn)
    
    def _build_where_clause(self, conditions: Dict[str, Any], param_start_index: int) -> Tuple[str, List[Any]]:
        """
        构建WHERE子句和对应的参数列表
        
        :param conditions: 查询条件字典
        :param param_start_index: 参数起始索引（用于SQL占位符）
        :return: 一个元组，包含(where子句字符串, 参数列表)
        """
        if not conditions:
            return ("1=1", [])  # 恒真条件
        
        where_parts = []
        params = []
        param_index = param_start_index
        
        for key, value in conditions.items():
            if isinstance(value, dict):
                # 处理带操作符的条件，如{"date": {"$gte": "2023-01-01", "$lte": "2023-12-31"}}
                for op, val in value.items():
                    sql_op = self._map_operator(op)
                    if sql_op:
                        param_index += 1
                        where_parts.append(f"{key} {sql_op} ${param_index}")
                        params.append(val)
            else:
                # 处理简单等于条件
                param_index += 1
                where_parts.append(f"{key} = ${param_index}")
                params.append(value)
        
        return (" AND ".join(where_parts), params)
    
    def _map_operator(self, op: str) -> Optional[str]:
        """
        将通用操作符映射为PostgreSQL的操作符
        
        :param op: 通用操作符，如$gte, $lte等
        :return: PostgreSQL操作符字符串，或None如果不支持
        """
        op_map = {
            "$eq": "=",
            "$ne": "<>",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
            "$in": "IN",
            "$nin": "NOT IN"
        }
        return op_map.get(op)


# 股票相关表的创建函数
async def create_stock_tables(storage: PostgreSQLStorage) -> bool:
    """创建股票相关的表结构"""
    # 股票基本信息表
    stock_info_schema = {
        "id": "SERIAL PRIMARY KEY",
        "code": "VARCHAR(20) NOT NULL UNIQUE",  # 股票代码，如sh600000
        "name": "VARCHAR(100) NOT NULL",  # 股票名称
        "exchange": "VARCHAR(10) NOT NULL",  # 交易所，如SH, SZ
        "industry": "VARCHAR(100)",  # 所属行业
        "market_cap": "NUMERIC(20, 2)",  # 市值
        "is_active": "BOOLEAN DEFAULT TRUE",  # 是否活跃
        "created_at": "TIMESTAMPTZ DEFAULT NOW()",
        "updated_at": "TIMESTAMPTZ DEFAULT NOW()"
    }
    
    # 股票日线数据表
    stock_daily_schema = {
        "id": "SERIAL PRIMARY KEY",
        "code": "VARCHAR(20) NOT NULL",  # 股票代码
        "date": "VARCHAR(20) NOT NULL",  # 日期
        "open": "NUMERIC(10, 2)",  # 开盘价
        "high": "NUMERIC(10, 2)",  # 最高价
        "low": "NUMERIC(10, 2)",  # 最低价
        "close": "NUMERIC(10, 2)",  # 收盘价
        "volume": "BIGINT",  # 成交量
        "amount": "NUMERIC(20, 2)",  # 成交额
        "change": "NUMERIC(10, 2)",  # 涨跌幅
        "change_pct": "NUMERIC(10, 2)",  # 涨跌幅百分比
        "created_at": "TIMESTAMPTZ DEFAULT NOW()",
        "updated_at": "TIMESTAMPTZ DEFAULT NOW()",
        "UNIQUE (code, date)": ""  # 唯一约束：同一股票同一天只有一条记录
    }
    
    # 股票分钟线数据表
    stock_minute_schema = {
        "id": "SERIAL PRIMARY KEY",
        "code": "VARCHAR(20) NOT NULL",  # 股票代码
        "datetime": "TIMESTAMPTZ NOT NULL",  # 日期时间
        "open": "NUMERIC(10, 2)",  # 开盘价
        "high": "NUMERIC(10, 2)",  # 最高价
        "low": "NUMERIC(10, 2)",  # 最低价
        "close": "NUMERIC(10, 2)",  # 收盘价
        "volume": "BIGINT",  # 成交量
        "created_at": "TIMESTAMPTZ DEFAULT NOW()",
        "updated_at": "TIMESTAMPTZ DEFAULT NOW()",
        "UNIQUE (code, datetime)": ""  # 唯一约束：同一股票同一时间只有一条记录
    }
    
    # 创建表
    success = True
    if not await storage.create_table("stock_info", stock_info_schema):
        success = False
    if not await storage.create_table("stock_daily", stock_daily_schema):
        success = False
    if not await storage.create_table("stock_minute", stock_minute_schema):
        success = False
        
    return success


# 测试代码
async def test_postgres_storage():
    """测试PostgreSQL存储组件"""
    # 配置
    config = {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "postgres",
        "database": "stock_test",
        "indexes": {
            "stock_daily": [
                {"columns": ["code", "date"], "unique": True},
                {"columns": ["date"]}
            ]
        }
    }
    
    # 创建存储实例
    storage = PostgreSQLStorage(config)
    
    # 连接数据库
    if not await storage.connect():
        print("连接数据库失败")
        return
    
    try:
        # 创建测试表
        create_success = await create_stock_tables(storage)
        print(f"创建表{'成功' if create_success else '失败'}")
        # 插入测试数据
        stock_info = {
            "code": "sh600000",
            "name": "浦发银行",
            "exchange": "SH",
            "industry": "银行业"
        }
        await storage.insert("stock_info", stock_info)
        
        # 批量插入日线数据
        daily_data = [
            {
                "code": "sh600000",
                "date": "2023-10-09",
                "open": 8.50,
                "high": 8.65,
                "low": 8.45,
                "close": 8.60,
                "volume": 12500000,
                "amount": 107500000.00,
                "change": 0.10,
                "change_pct": 1.17
            },
            {
                "code": "sh600000",
                "date": "2023-10-10",
                "open": 8.62,
                "high": 8.70,
                "low": 8.58,
                "close": 8.65,
                "volume": 15000000,
                "amount": 129750000.00,
                "change": 0.05,
                "change_pct": 0.58
            }
        ]
        success_count, total_count = await storage.batch_insert("stock_daily", daily_data)
        print(f"批量插入结果: 成功 {success_count}/{total_count}")
        
        # 查询数据
        results = await storage.query(
            "stock_daily",
            conditions={"code": "sh600000"},
            sort=[("date", -1)],
            limit=10
        )
        print("查询结果:")
        for row in results:
            print(row)
            
        # 更新数据
        update_count = await storage.update(
            "stock_info",
            conditions={"code": "sh600000"},
            data={"market_cap": 350000000000.00}
        )
        print(f"更新行数: {update_count}")
        
        # 检查记录是否存在
        exists = await storage.exists(
            "stock_daily",
            conditions={"code": "sh600000", "date": "2023-10-09"}
        )
        print(f"记录是否存在: {exists}")
        
    finally:
        # 清理测试数据
        await storage.delete("stock_daily", {"code": "sh600000"})
        await storage.delete("stock_info", {"code": "sh600000"})
        
        # 断开连接
        await storage.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_postgres_storage())
