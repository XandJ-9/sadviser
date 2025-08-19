import os
import asyncio
import logging
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow.fs import LocalFileSystem

from .base_storage import BaseStorage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParquetArchive(BaseStorage):
    """Parquet归档组件，用于高效存储和查询股票历史大数据"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Parquet归档存储
        
        :param config: 配置字典，应包含archive_dir, partition_cols等
        """
        super().__init__(config)
        self.archive_dir = Path(config.get('archive_dir', './data/parquet_archive'))
        self.partition_cols = config.get('partition_cols', {'stock_daily': ['code', 'year']})
        self.file_system = LocalFileSystem()
        
        # 创建归档目录
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存已加载的数据集元数据
        self.dataset_metadata = {}
    
    async def connect(self) -> bool:
        """
        连接到Parquet归档存储（对于本地文件系统，只需验证目录是否存在）
        
        :return: 始终返回True
        """
        # 确保归档目录存在
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.connected = True
        logger.info(f"Parquet归档存储就绪，目录: {self.archive_dir}")
        return True
    
    async def disconnect(self) -> None:
        """断开连接（对于本地文件系统，无需实际操作）"""
        self.connected = False
        # 清除元数据缓存
        self.dataset_metadata.clear()
        logger.info("已关闭Parquet归档存储连接")
    
    def _get_table_path(self, table_name: str) -> Path:
        """
        获取表的归档路径
        
        :param table_name: 表名
        :return: 表的路径
        """
        return self.archive_dir / table_name
    
    def _get_partition_cols(self, table_name: str) -> List[str]:
        """
        获取表的分区列
        
        :param table_name: 表名
        :return: 分区列列表
        """
        return self.partition_cols.get(table_name, [])
    
    def _ensure_partition_columns(self, table_name: str, data: pd.DataFrame) -> pd.DataFrame:
        """
        确保数据包含分区列（如需要，自动生成）
        
        :param table_name: 表名
        :param data: 数据DataFrame
        :return: 包含分区列的DataFrame
        """
        partition_cols = self._get_partition_cols(table_name)
        for col in partition_cols:
            if col not in data.columns:
                if col == 'year' and 'date' in data.columns:
                    # 从日期列提取年份作为分区
                    data['year'] = pd.to_datetime(data['date']).dt.year
                elif col == 'month' and 'date' in data.columns:
                    # 从日期列提取月份作为分区
                    data['month'] = pd.to_datetime(data['date']).dt.month
                else:
                    logger.warning(f"数据缺少分区列 {col}，无法自动生成，将跳过该分区")
                    return None
        return data
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        插入单条数据（Parquet更适合批量操作，这里将单条数据转为批量插入）
        
        :param table_name: 表名
        :param data: 要插入的数据字典
        :return: 插入成功返回True，否则返回False
        """
        return await self.batch_insert(table_name, [data])
    
    async def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        批量插入数据到Parquet归档
        
        :param table_name: 表名
        :param data_list: 要插入的数据字典列表
        :return: 一个元组，包含(成功插入数量, 总数量)
        """
        if not data_list:
            return (0, 0)
            
        total = len(data_list)
        
        try:
            # 转换为DataFrame
            df = pd.DataFrame(data_list)
            
            # 添加时间戳
            timestamp = datetime.now().isoformat()
            if "created_at" not in df.columns:
                df["created_at"] = timestamp
            df["updated_at"] = timestamp
            
            # 确保包含分区列
            df = self._ensure_partition_columns(table_name, df)
            if df is None:
                return (0, total)
            
            # 获取表路径
            table_path = self._get_table_path(table_name)
            
            # 转换为PyArrow Table
            table = pa.Table.from_pandas(df)
            
            # 写入Parquet文件，使用分区
            partition_cols = self._get_partition_cols(table_name)
            pq.write_to_dataset(
                table,
                root_path=str(table_path),
                partition_cols=partition_cols,
                filesystem=self.file_system,
                existing_data_behavior="append"  # 追加模式
            )
            
            # 更新元数据缓存
            self._update_dataset_metadata(table_name)
            
            logger.info(f"成功将 {total} 条数据写入Parquet归档 {table_name}")
            return (total, total)
            
        except Exception as e:
            self._handle_exception(e, f"批量插入数据到Parquet归档 {table_name}")
            return (0, total)
    
    async def update(self, table_name: str, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """
        更新Parquet归档中的数据（Parquet不适合频繁更新，这里采用重写方式）
        
        :param table_name: 表名
        :param conditions: 更新条件
        :param data: 要更新的数据
        :return: 受影响的行数
        """
        # Parquet文件不支持高效的随机更新，这里实现方式是：
        # 1. 读取符合条件的数据
        # 2. 更新数据
        # 3. 删除原数据
        # 4. 写入更新后的数据
        
        table_path = self._get_table_path(table_name)
        if not table_path.exists():
            return 0
        
        try:
            # 1. 读取符合条件的数据
            dataset = pq.ParquetDataset(str(table_path), filesystem=self.file_system)
            table = dataset.read()
            df = table.to_pandas()
            
            # 2. 应用条件过滤
            mask = pd.Series([True] * len(df))
            for key, value in conditions.items():
                if isinstance(value, dict):
                    # 处理带操作符的条件，如{"date": {"$gte": "2023-01-01"}}
                    for op, val in value.items():
                        if op == "$gte":
                            mask &= df[key] >= val
                        elif op == "$lte":
                            mask &= df[key] <= val
                        elif op == "$gt":
                            mask &= df[key] > val
                        elif op == "$lt":
                            mask &= df[key] < val
                        elif op == "$eq":
                            mask &= df[key] == val
                        elif op == "$ne":
                            mask &= df[key] != val
                else:
                    # 简单等于条件
                    mask &= df[key] == value
            
            affected_count = mask.sum()
            if affected_count == 0:
                return 0
            
            # 3. 更新数据
            for key, value in data.items():
                df.loc[mask, key] = value
            
            # 更新时间戳
            df.loc[mask, "updated_at"] = datetime.now().isoformat()
            
            # 4. 删除原分区数据（只删除受影响的分区）
            partition_cols = self._get_partition_cols(table_name)
            if partition_cols:
                # 获取受影响的分区值
                affected_partitions = df.loc[mask, partition_cols].drop_duplicates()
                
                # 删除这些分区
                for _, partition_vals in affected_partitions.iterrows():
                    partition_path = table_path
                    for col, val in partition_vals.items():
                        partition_path /= f"{col}={val}"
                    
                    if partition_path.exists():
                        shutil.rmtree(partition_path)
                        logger.info(f"已删除分区 {partition_path} 以准备更新")
            
            # 5. 写入更新后的数据
            updated_table = pa.Table.from_pandas(df[mask])
            pq.write_to_dataset(
                updated_table,
                root_path=str(table_path),
                partition_cols=partition_cols,
                filesystem=self.file_system,
                existing_data_behavior="append"
            )
            
            # 更新元数据缓存
            self._update_dataset_metadata(table_name)
            
            return affected_count
            
        except Exception as e:
            self._handle_exception(e, f"更新Parquet归档 {table_name} 数据")
            return 0
    
    async def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """
        删除Parquet归档中的数据
        
        :param table_name: 表名
        :param conditions: 删除条件
        :return: 受影响的行数
        """
        table_path = self._get_table_path(table_name)
        if not table_path.exists():
            return 0
        
        try:
            # 1. 读取数据以确定受影响的分区
            dataset = pq.ParquetDataset(str(table_path), filesystem=self.file_system)
            # 只读取必要的列以提高效率
            columns = list(conditions.keys()) + self._get_partition_cols(table_name)
            table = dataset.read(columns=columns)
            df = table.to_pandas()
            
            # 2. 应用条件过滤
            mask = pd.Series([True] * len(df))
            for key, value in conditions.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        if op == "$gte":
                            mask &= df[key] >= val
                        elif op == "$lte":
                            mask &= df[key] <= val
                        elif op == "$gt":
                            mask &= df[key] > val
                        elif op == "$lt":
                            mask &= df[key] < val
                        elif op == "$eq":
                            mask &= df[key] == val
                        elif op == "$ne":
                            mask &= df[key] != val
                else:
                    mask &= df[key] == value
            
            affected_count = mask.sum()
            if affected_count == 0:
                return 0
            
            # 3. 删除受影响的分区
            partition_cols = self._get_partition_cols(table_name)
            if partition_cols and not df.empty:
                # 获取受影响的分区值
                affected_partitions = df.loc[mask, partition_cols].drop_duplicates()
                
                # 删除这些分区
                for _, partition_vals in affected_partitions.iterrows():
                    partition_path = table_path
                    for col, val in partition_vals.items():
                        partition_path /= f"{col}={val}"
                    
                    if partition_path.exists():
                        shutil.rmtree(partition_path)
                        logger.info(f"已删除分区 {partition_path}")
            
            # 更新元数据缓存
            self._update_dataset_metadata(table_name)
            
            return affected_count
            
        except Exception as e:
            self._handle_exception(e, f"删除Parquet归档 {table_name} 数据")
            return 0
            return 0
    
    async def query(self, 
                   table_name: str, 
                   conditions: Optional[Dict[str, Any]] = None,
                   fields: Optional[List[str]] = None,
                   sort: Optional[List[Tuple[str, int]]] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询Parquet归档中的数据
        
        :param table_name: 表名
        :param conditions: 查询条件
        :param fields: 要返回的字段列表，None表示返回所有字段
        :param sort: 排序条件，列表中的元组为(字段名, 排序方向)，1为升序，-1为降序
        :param limit: 返回结果的最大数量
        :param offset: 结果偏移量，用于分页
        :return: 查询结果列表
        """
        table_path = self._get_table_path(table_name)
        if not table_path.exists():
            return []
        
        try:
            # 构建查询条件，利用分区过滤提高效率
            partition_filters = []
            other_conditions = {}
            
            if conditions:
                partition_cols = self._get_partition_cols(table_name)
                for key, value in conditions.items():
                    if key in partition_cols:
                        # 分区列条件，可用于高效过滤
                        if isinstance(value, dict):
                            for op, val in value.items():
                                if op == "$eq":
                                    partition_filters.append((key, "=", val))
                                elif op == "$in":
                                    partition_filters.extend([(key, "=", v) for v in val])
                        else:
                            partition_filters.append((key, "=", value))
                    else:
                        # 非分区列条件
                        other_conditions[key] = value
            
            # 读取数据集，应用分区过滤
            dataset = pq.ParquetDataset(
                str(table_path),
                filesystem=self.file_system,
                filters=partition_filters
            )
            
            # 确定要读取的列
            read_columns = fields
            if not read_columns:
                # 如果没有指定字段，读取所有字段
                read_columns = dataset.schema.names
            elif not set(read_columns).issubset(dataset.schema.names):
                # 检查字段是否存在
                invalid_fields = set(read_columns) - set(dataset.schema.names)
                logger.warning(f"查询字段不存在: {invalid_fields}")
                read_columns = [f for f in read_columns if f in dataset.schema.names]
                if not read_columns:
                    return []
            
            # 读取数据
            table = dataset.read(columns=read_columns)
            df = table.to_pandas()
            
            # 应用非分区列条件过滤
            if other_conditions:
                mask = pd.Series([True] * len(df))
                for key, value in other_conditions.items():
                    if key not in df.columns:
                        continue
                        
                    if isinstance(value, dict):
                        for op, val in value.items():
                            if op == "$gte":
                                mask &= df[key] >= val
                            elif op == "$lte":
                                mask &= df[key] <= val
                            elif op == "$gt":
                                mask &= df[key] > val
                            elif op == "$lt":
                                mask &= df[key] < val
                            elif op == "$eq":
                                mask &= df[key] == val
                            elif op == "$ne":
                                mask &= df[key] != val
                            elif op == "$in":
                                mask &= df[key].isin(val)
                            elif op == "$nin":
                                mask &= ~df[key].isin(val)
                    else:
                        mask &= df[key] == value
                
                df = df[mask]
            
            # 应用排序
            if sort:
                sort_columns = [col for col, _ in sort]
                ascending = [dir == 1 for _, dir in sort]
                # 只对存在的列进行排序
                valid_sort_columns = [col for col in sort_columns if col in df.columns]
                if valid_sort_columns:
                    valid_ascending = [ascending[i] for i, col in enumerate(sort_columns) 
                                      if col in df.columns]
                    df = df.sort_values(by=valid_sort_columns, ascending=valid_ascending)
            
            # 应用分页
            if offset and offset > 0:
                df = df.iloc[offset:]
            if limit and limit > 0:
                df = df.iloc[:limit]
            
            # 转换为字典列表并返回
            return df.to_dict('records')
            
        except Exception as e:
            self._handle_exception(e, f"查询Parquet归档 {table_name} 数据")
            return []
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """
        创建Parquet归档表（实际是创建目录和元数据）
        
        :param table_name: 表名
        :param schema: 表结构定义，例如:
                       {
                           "columns": {
                               "code": "string",
                               "date": "date",
                               "open": "float",
                               "high": "float",
                               "low": "float",
                               "close": "float",
                               "volume": "int64"
                           },
                           "partition_cols": ["code", "year"]
                       }
        :return: 创建成功返回True，否则返回False
        """
        try:
            # 创建表目录
            table_path = self._get_table_path(table_name)
            table_path.mkdir(parents=True, exist_ok=True)
            
            # 保存分区列配置
            if "partition_cols" in schema:
                self.partition_cols[table_name] = schema["partition_cols"]
            
            # 创建一个空的Parquet文件来定义 schema
            if "columns" in schema:
                # 转换为PyArrow schema
                pa_fields = []
                for col_name, col_type in schema["columns"].items():
                    if col_type == "string":
                        pa_type = pa.string()
                    elif col_type == "int64":
                        pa_type = pa.int64()
                    elif col_type == "float":
                        pa_type = pa.float64()
                    elif col_type == "date":
                        pa_type = pa.date32()
                    elif col_type == "datetime":
                        pa_type = pa.timestamp('ms')
                    else:
                        pa_type = pa.string()  # 默认类型
                    
                    pa_fields.append(pa.field(col_name, pa_type))
                
                # 添加默认的时间戳列
                if "created_at" not in schema["columns"]:
                    pa_fields.append(pa.field("created_at", pa.string()))
                if "updated_at" not in schema["columns"]:
                    pa_fields.append(pa.field("updated_at", pa.string()))
                
                pa_schema = pa.schema(pa_fields)
                
                # 创建空表并写入
                empty_table = pa.Table.from_pylist([], schema=pa_schema)
                pq.write_to_dataset(
                    empty_table,
                    root_path=str(table_path),
                    filesystem=self.file_system
                )
            
            logger.info(f"Parquet归档表 {table_name} 创建成功")
            return True
            
        except Exception as e:
            self._handle_exception(e, f"创建Parquet归档表 {table_name}")
            return False
    
    async def exists(self, table_name: str, conditions: Dict[str, Any]) -> bool:
        """
        检查Parquet归档中是否存在符合条件的记录
        
        :param table_name: 表名
        :param conditions: 检查条件
        :return: 存在返回True，否则返回False
        """
        # 简单实现：查询一条记录看是否存在
        results = await self.query(
            table_name,
            conditions=conditions,
            limit=1
        )
        return len(results) > 0
    
    def _update_dataset_metadata(self, table_name: str) -> None:
        """更新数据集元数据缓存"""
        table_path = self._get_table_path(table_name)
        if table_path.exists():
            try:
                dataset = pq.ParquetDataset(str(table_path), filesystem=self.file_system)
                self.dataset_metadata[table_name] = {
                    "num_row_groups": sum(1 for _ in dataset.pieces),
                    "schema": dataset.schema,
                    "last_updated": datetime.now().isoformat()
                }
            except Exception as e:
                logger.warning(f"更新Parquet数据集 {table_name} 元数据失败: {str(e)}")
    
    async def get_metadata(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        获取表的元数据
        
        :param table_name: 表名
        :return: 元数据字典，或None如果表不存在
        """
        if table_name in self.dataset_metadata:
            return self.dataset_metadata[table_name]
        
        # 元数据不在缓存中，尝试加载
        self._update_dataset_metadata(table_name)
        return self.dataset_metadata.get(table_name)


# 创建股票历史数据归档表
async def create_stock_archive_tables(archive: ParquetArchive) -> bool:
    """创建股票历史数据归档表"""
    # 股票日线历史数据归档表
    daily_schema = {
        "columns": {
            "code": "string",
            "date": "date",
            "open": "float",
            "high": "float",
            "low": "float",
            "close": "float",
            "volume": "int64",
            "amount": "float",
            "change": "float",
            "change_pct": "float"
        },
        "partition_cols": ["code", "year"]  # 按股票代码和年份分区
    }
    
    # 股票分钟线历史数据归档表（按股票代码、年份、月份分区）
    minute_schema = {
        "columns": {
            "code": "string",
            "datetime": "datetime",
            "open": "float",
            "high": "float",
            "low": "float",
            "close": "float",
            "volume": "int64"
        },
        "partition_cols": ["code", "year", "month"]
    }
    
    # 创建表
    success = True
    if not await archive.create_table("stock_daily_archive", daily_schema):
        success = False
    if not await archive.create_table("stock_minute_archive", minute_schema):
        success = False
        
    return success


# 测试代码
async def test_parquet_archive():
    """测试Parquet归档组件"""
    # 配置
    config = {
        "archive_dir": "./test_parquet_archive",
        "partition_cols": {
            "stock_daily_archive": ["code", "year"]
        }
    }
    
    # 创建归档实例
    archive = ParquetArchive(config)
    
    # 连接归档存储
    if not await archive.connect():
        print("连接Parquet归档存储失败")
        return
    
    try:
        # 创建测试表
        await create_stock_archive_tables(archive)
        
        # 生成测试数据
        import numpy as np
        dates = pd.date_range(start="2022-01-01", end="2023-12-31", freq="B")  # 工作日
        test_data = []
        
        for date in dates:
            test_data.append({
                "code": "sh600000",
                "date": date.strftime("%Y-%m-%d"),
                "open": round(8.0 + np.random.normal(0, 0.5), 2),
                "high": round(8.2 + np.random.normal(0, 0.5), 2),
                "low": round(7.8 + np.random.normal(0, 0.5), 2),
                "close": round(8.0 + np.random.normal(0, 0.5), 2),
                "volume": int(np.random.normal(10000000, 5000000)),
                "amount": round(np.random.normal(80000000, 40000000), 2),
                "change": round(np.random.normal(0, 0.2), 2),
                "change_pct": round(np.random.normal(0, 2), 2)
            })
        
        # 批量插入数据
        success_count, total_count = await archive.batch_insert("stock_daily_archive", test_data)
        print(f"批量插入数据: 成功 {success_count}/{total_count}")
        
        # 查询元数据
        metadata = await archive.get_metadata("stock_daily_archive")
        print("表元数据:")
        print(f"分区数: {metadata['num_row_groups']}")
        print(f" schema: {metadata['schema']}")
        
        # 查询2023年的数据
        results = await archive.query(
            "stock_daily_archive",
            conditions={
                "code": "sh600000",
                "year": 2023,
                "date": {"$gte": "2023-01-01", "$lte": "2023-01-31"}
            },
            fields=["code", "date", "open", "close", "change_pct"],
            sort=[("date", 1)],
            limit=10
        )
        print(f"\n查询到 {len(results)} 条2023年1月的数据:")
        for item in results[:5]:  # 只显示前5条
            print(item)
        
        # 更新数据（例如修正某一天的收盘价）
        update_count = await archive.update(
            "stock_daily_archive",
            conditions={
                "code": "sh600000",
                "date": "2023-01-05"
            },
            data={"close": 9.0, "change_pct": 2.5}
        )
        print(f"\n更新数据行数: {update_count}")
        
        # 验证更新
        updated_data = await archive.query(
            "stock_daily_archive",
            conditions={
                "code": "sh600000",
                "date": "2023-01-05"
            }
        )
        print("更新后的数据:")
        print(updated_data)
        
        # 检查记录是否存在
        exists = await archive.exists(
            "stock_daily_archive",
            conditions={"code": "sh600000", "date": "2023-01-05"}
        )
        print(f"记录是否存在: {exists}")
        
        # 删除2022年的数据
        delete_count = await archive.delete(
            "stock_daily_archive",
            conditions={"code": "sh600000", "year": 2022}
        )
        print(f"删除2022年数据行数: {delete_count}")
        
    finally:
        # 断开连接
        await archive.disconnect()
        
        # 清理测试数据
        if os.path.exists(config["archive_dir"]):
            shutil.rmtree(config["archive_dir"])

if __name__ == "__main__":
    asyncio.run(test_parquet_archive())
