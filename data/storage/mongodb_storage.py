import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from .base_storage import BaseStorage

# 配置日志
logger = logging.getLogger(__name__)

class MongoDBStorage(BaseStorage):
    """MongoDB存储组件，用于存储非结构化和半结构化的股票数据"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MongoDB存储
        
        :param config: 配置字典，应包含uri, database等
        """
        super().__init__(config)
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.database_name = config.get('database', 'stock_db')
    
    async def connect(self) -> bool:
        """
        连接到MongoDB数据库
        
        :return: 连接成功返回True，否则返回False
        """
        if self.connected and self.client and self.db:
            return True
            
        try:
            # 创建客户端
            self.client = AsyncIOMotorClient(
                self.config.get('uri', 'mongodb://localhost:27017/'),
                serverSelectionTimeoutMS=self.config.get('timeout', 5000)
            )
            
            # 获取数据库
            self.db = self.client[self.database_name]
            
            # 验证连接
            await self.client.admin.command('ping')
            
            self.connected = True
            logger.info(f"成功连接到MongoDB数据库: {self.database_name}")
            return True
            
        except Exception as e:
            self._handle_exception(e, "连接MongoDB")
            self.client = None
            self.db = None
            return False
    
    async def disconnect(self) -> None:
        """断开与MongoDB数据库的连接"""
        if self.client:
            try:
                self.client.close()
                logger.info("已关闭MongoDB连接")
            except Exception as e:
                self._handle_exception(e, "关闭MongoDB连接")
        
        self.connected = False
        self.client = None
        self.db = None
    
    def _get_collection(self, collection_name: str) -> Optional[AsyncIOMotorCollection]:
        """
        获取集合对象
        
        :param collection_name: 集合名称
        :return: 集合对象，或None如果未连接
        """
        if not self.connected or not self.db:
            return None
        return self.db[collection_name]
    
    async def insert(self, collection_name: str, data: Dict[str, Any]) -> bool:
        """
        插入单条数据
        
        :param collection_name: 集合名称
        :param data: 要插入的数据字典
        :return: 插入成功返回True，否则返回False
        """
        collection = self._get_collection(collection_name)
        if not collection:
            # 尝试重新连接
            if not await self.connect():
                return False
            collection = self._get_collection(collection_name)
            if not collection:
                return False
        
        # 添加时间戳
        data = self._add_timestamps(data)
        
        try:
            result = await collection.insert_one(data)
            return result.acknowledged
        except Exception as e:
            self._handle_exception(e, f"插入数据到集合 {collection_name}")
            return False
    
    async def batch_insert(self, collection_name: str, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        批量插入数据
        
        :param collection_name: 集合名称
        :param data_list: 要插入的数据字典列表
        :return: 一个元组，包含(成功插入数量, 总数量)
        """
        if not data_list:
            return (0, 0)
            
        total = len(data_list)
        
        collection = self._get_collection(collection_name)
        if not collection:
            # 尝试重新连接
            if not await self.connect():
                return (0, total)
            collection = self._get_collection(collection_name)
            if not collection:
                return (0, total)
        
        # 为每条数据添加时间戳
        processed_data = [self._add_timestamps(data) for data in data_list]
        
        try:
            result = await collection.insert_many(processed_data)
            return (len(result.inserted_ids), total)
        except Exception as e:
            self._handle_exception(e, f"批量插入数据到集合 {collection_name}")
            return (0, total)
    
    async def update(self, collection_name: str, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """
        更新数据
        
        :param collection_name: 集合名称
        :param conditions: 更新条件
        :param data: 要更新的数据
        :return: 受影响的行数
        """
        collection = self._get_collection(collection_name)
        if not collection:
            # 尝试重新连接
            if not await self.connect():
                return 0
            collection = self._get_collection(collection_name)
            if not collection:
                return 0
        
        # 添加更新时间戳
        data = self._add_timestamps(data)
        # 处理条件
        conditions = self._validate_conditions(conditions)
        
        # 构建更新数据（使用$set操作符）
        update_data = {"$set": data}
        
        try:
            result = await collection.update_many(conditions, update_data)
            return result.modified_count
        except Exception as e:
            self._handle_exception(e, f"更新集合 {collection_name} 数据")
            return 0
    
    async def delete(self, collection_name: str, conditions: Dict[str, Any]) -> int:
        """
        删除数据
        
        :param collection_name: 集合名称
        :param conditions: 删除条件
        :return: 受影响的行数
        """
        collection = self._get_collection(collection_name)
        if not collection:
            # 尝试重新连接
            if not await self.connect():
                return 0
            collection = self._get_collection(collection_name)
            if not collection:
                return 0
        
        conditions = self._validate_conditions(conditions)
        
        try:
            result = await collection.delete_many(conditions)
            return result.deleted_count
        except Exception as e:
            self._handle_exception(e, f"删除集合 {collection_name} 数据")
            return 0
    
    async def query(self, 
                   collection_name: str, 
                   conditions: Optional[Dict[str, Any]] = None,
                   fields: Optional[List[str]] = None,
                   sort: Optional[List[Tuple[str, int]]] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        :param collection_name: 集合名称
        :param conditions: 查询条件
        :param fields: 要返回的字段列表，None表示返回所有字段
        :param sort: 排序条件，列表中的元组为(字段名, 排序方向)，1为升序，-1为降序
        :param limit: 返回结果的最大数量
        :param offset: 结果偏移量，用于分页
        :return: 查询结果列表
        """
        collection = self._get_collection(collection_name)
        if not collection:
            # 尝试重新连接
            if not await self.connect():
                return []
            collection = self._get_collection(collection_name)
            if not collection:
                return []
        
        conditions = self._validate_conditions(conditions or {})
        
        # 构建查询
        query = collection.find(conditions)
        
        # 处理字段过滤
        if fields:
            projection = {field: 1 for field in fields}
            projection["_id"] = 0  # 默认不返回_id字段
            query = query projection(projection)
        
        # 处理排序
        if sort:
            query = query.sort(sort)
        
        # 处理分页
        if offset is not None and offset > 0:
            query = query.skip(offset)
        if limit is not None and limit > 0:
            query = query.limit(limit)
        
        try:
            # 执行查询并转换为列表
            results = await query.to_list(length=limit)
            return results
        except Exception as e:
            self._handle_exception(e, f"查询集合 {collection_name} 数据")
            return []
    
    async def create_table(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """
        创建集合和索引
        
        :param collection_name: 集合名称
        :param schema: 集合结构定义，主要用于创建索引
                       例如:
                       {
                           "indexes": [
                               {"keys": {"code": 1, "date": 1}, "unique": True},
                               {"keys": {"indicator_name": 1}}
                           ]
                       }
        :return: 创建成功返回True，否则返回False
        """
        collection = self._get_collection(collection_name)
        if not collection:
            # 尝试重新连接
            if not await self.connect():
                return False
            collection = self._get_collection(collection_name)
            if not collection:
                return False
        
        try:
            # MongoDB不需要预先定义文档结构，这里主要用于创建索引
            if "indexes" in schema:
                for index in schema["indexes"]:
                    keys = index["keys"]
                    unique = index.get("unique", False)
                    index_name = index.get("name")
                    
                    # 创建索引
                    await collection.create_index(
                        keys,
                        unique=unique,
                        name=index_name
                    )
                    logger.info(f"在集合 {collection_name} 上创建索引: {keys}")
            
            logger.info(f"集合 {collection_name} 准备就绪")
            return True
        except Exception as e:
            self._handle_exception(e, f"创建集合 {collection_name}")
            return False
    
    async def exists(self, collection_name: str, conditions: Dict[str, Any]) -> bool:
        """
        检查是否存在符合条件的记录
        
        :param collection_name: 集合名称
        :param conditions: 检查条件
        :return: 存在返回True，否则返回False
        """
        collection = self._get_collection(collection_name)
        if not collection:
            # 尝试重新连接
            if not await self.connect():
                return False
            collection = self._get_collection(collection_name)
            if not collection:
                return False
        
        conditions = self._validate_conditions(conditions)
        
        try:
            count = await collection.count_documents(conditions, limit=1)
            return count > 0
        except Exception as e:
            self._handle_exception(e, f"检查集合 {collection_name} 记录存在性")
            return False


# 创建股票相关集合和索引的函数
async def create_stock_collections(storage: MongoDBStorage) -> bool:
    """创建股票相关的集合和索引"""
    # 技术指标计算结果集合
    indicator_results_schema = {
        "indexes": [
            {"keys": {"code": 1, "date": 1, "indicator_name": 1}, "unique": True, "name": "idx_code_date_indicator"},
            {"keys": {"date": 1}},
            {"keys": {"indicator_name": 1}}
        ]
    }
    
    # 策略筛选结果集合
    strategy_results_schema = {
        "indexes": [
            {"keys": {"strategy_name": 1, "date": 1, "code": 1}, "unique": True, "name": "idx_strategy_date_code"},
            {"keys": {"date": 1}},
            {"keys": {"strategy_name": 1}}
        ]
    }
    
    # 回测结果集合
    backtest_results_schema = {
        "indexes": [
            {"keys": {"strategy_name": 1, "start_date": 1, "end_date": 1}, "unique": True, "name": "idx_strategy_date_range"},
            {"keys": {"strategy_name": 1}}
        ]
    }
    
    # 新闻和舆情数据集合
    news_sentiment_schema = {
        "indexes": [
            {"keys": {"code": 1, "publish_time": -1}, "name": "idx_code_publishtime"},
            {"keys": {"publish_time": -1}},
            {"keys": {"sentiment": 1}}
        ]
    }
    
    # 创建集合和索引
    success = True
    if not await storage.create_table("indicator_results", indicator_results_schema):
        success = False
    if not await storage.create_table("strategy_results", strategy_results_schema):
        success = False
    if not await storage.create_table("backtest_results", backtest_results_schema):
        success = False
    if not await storage.create_table("news_sentiment", news_sentiment_schema):
        success = False
        
    return success


# 测试代码
async def test_mongodb_storage():
    """测试MongoDB存储组件"""
    # 配置
    config = {
        "uri": "mongodb://localhost:27017/",
        "database": "stock_test"
    }
    
    # 创建存储实例
    storage = MongoDBStorage(config)
    
    # 连接数据库
    if not await storage.connect():
        print("连接数据库失败")
        return
    
    try:
        # 创建测试集合
        await create_stock_collections(storage)
        
        # 插入技术指标数据
        indicator_data = {
            "code": "sh600000",
            "date": "2023-10-09",
            "indicator_name": "MACD",
            "values": {
                "macd": 0.12,
                "signal": 0.08,
                "hist": 0.04
            }
        }
        success = await storage.insert("indicator_results", indicator_data)
        print(f"插入技术指标数据: {'成功' if success else '失败'}")
        
        # 批量插入策略结果
        strategy_data = [
            {
                "strategy_name": "trend_following",
                "date": "2023-10-09",
                "code": "sh600000",
                "score": 85,
                "signal": "buy",
                "params": {
                    "ma_period": 20,
                    "rsi_threshold": 50
                }
            },
            {
                "strategy_name": "trend_following",
                "date": "2023-10-09",
                "code": "sz000001",
                "score": 72,
                "signal": "hold",
                "params": {
                    "ma_period": 20,
                    "rsi_threshold": 50
                }
            }
        ]
        success_count, total_count = await storage.batch_insert("strategy_results", strategy_data)
        print(f"批量插入策略结果: 成功 {success_count}/{total_count}")
        
        # 查询数据
        results = await storage.query(
            "strategy_results",
            conditions={"strategy_name": "trend_following", "date": "2023-10-09"},
            sort=[("score", -1)],
            limit=10
        )
        print("查询策略结果:")
        for row in results:
            print(row)
            
        # 更新数据
        update_count = await storage.update(
            "indicator_results",
            conditions={"code": "sh600000", "date": "2023-10-09", "indicator_name": "MACD"},
            data={"values": {"macd": 0.15, "signal": 0.10, "hist": 0.05}}
        )
        print(f"更新技术指标数据行数: {update_count}")
        
        # 检查记录是否存在
        exists = await storage.exists(
            "indicator_results",
            conditions={"code": "sh600000", "date": "2023-10-09", "indicator_name": "MACD"}
        )
        print(f"技术指标记录是否存在: {exists}")
        
    finally:
        # 清理测试数据
        await storage.delete("indicator_results", {"code": "sh600000"})
        await storage.delete("strategy_results", {"strategy_name": "trend_following", "date": "2023-10-09"})
        
        # 断开连接
        await storage.disconnect()

if __name__ == "__main__":
    asyncio.run(test_mongodb_storage())
