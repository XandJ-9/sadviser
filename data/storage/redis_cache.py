import asyncio
import logging
import json
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime, timedelta

import aioredis
from aioredis import Redis, ConnectionPool

from .base_storage import BaseStorage

# 配置日志
logger = logging.getLogger(__name__)

class RedisCache(BaseStorage):
    """Redis缓存组件，用于缓存高频访问的股票数据"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Redis缓存
        
        :param config: 配置字典，应包含url, default_ttl等
        """
        super().__init__(config)
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
        self.default_ttl = config.get('default_ttl', 3600)  # 默认过期时间，单位：秒
        
        # 缓存键前缀，避免不同应用之间的键冲突
        self.key_prefix = config.get('key_prefix', 'stock:')
    
    async def connect(self) -> bool:
        """
        连接到Redis服务器
        
        :return: 连接成功返回True，否则返回False
        """
        if self.connected and self.client:
            return True
            
        try:
            # 创建连接池
            self.pool = aioredis.ConnectionPool.from_url(
                self.config.get('url', 'redis://localhost:6379/0'),
                max_connections=self.config.get('max_connections', 10)
            )
            
            # 创建客户端
            self.client = aioredis.Redis(connection_pool=self.pool)
            
            # 测试连接
            await self.client.ping()
            
            self.connected = True
            logger.info(f"成功连接到Redis服务器: {self.config.get('url')}")
            return True
            
        except Exception as e:
            self._handle_exception(e, "连接Redis")
            self.client = None
            self.pool = None
            return False
    
    async def disconnect(self) -> None:
        """断开与Redis服务器的连接"""
        if self.pool:
            try:
                await self.pool.disconnect()
                logger.info("已关闭Redis连接池")
            except Exception as e:
                self._handle_exception(e, "关闭Redis连接")
        
        self.connected = False
        self.client = None
        self.pool = None
    
    def _get_key(self, table_name: str, key: str) -> str:
        """
        生成带前缀的Redis键名
        
        :param table_name: 表/集合名称，用于分类
        :param key: 原始键名
        :return: 带前缀的完整键名
        """
        return f"{self.key_prefix}{table_name}:{key}"
    
    def _serialize(self, data: Any) -> bytes:
        """
        序列化数据为Redis存储格式
        
        :param data: 要序列化的数据
        :return: 序列化后的字节数据
        """
        try:
            # 将数据转换为JSON字符串，再编码为bytes
            return json.dumps(data, ensure_ascii=False).encode('utf-8')
        except Exception as e:
            self._handle_exception(e, "数据序列化")
            raise
    
    def _deserialize(self, data: Optional[bytes]) -> Any:
        """
        反序列化Redis存储的数据
        
        :param data: 从Redis获取的字节数据
        :return: 反序列化后的数据
        """
        if data is None:
            return None
            
        try:
            # 将bytes解码为字符串，再解析为JSON
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            self._handle_exception(e, "数据反序列化")
            return None
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        插入单条数据到缓存
        
        :param table_name: 表/集合名称，用于分类
        :param data: 要插入的数据字典，必须包含"id"字段作为键
        :return: 插入成功返回True，否则返回False
        """
        if "id" not in data:
            logger.error("Redis缓存插入失败：数据必须包含'id'字段作为键")
            return False
            
        key = self._get_key(table_name, data["id"])
        
        # 获取过期时间，优先使用data中的ttl，否则使用默认值
        ttl = data.get("ttl", self.default_ttl)
        
        # 移除ttl字段，避免序列化存储
        if "ttl" in data:
            del data["ttl"]
        
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return False
        
        try:
            # 序列化数据
            serialized_data = self._serialize(data)
            
            # 存储数据
            await self.client.set(key, serialized_data, ex=ttl)
            return True
        except Exception as e:
            self._handle_exception(e, f"插入数据到Redis缓存 {table_name}")
            return False
    
    async def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        批量插入数据到缓存
        
        :param table_name: 表/集合名称，用于分类
        :param data_list: 要插入的数据字典列表，每条数据必须包含"id"字段作为键
        :return: 一个元组，包含(成功插入数量, 总数量)
        """
        if not data_list:
            return (0, 0)
            
        total = len(data_list)
        success = 0
        
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return (0, total)
        
        try:
            # 使用pipeline批量操作
            pipe = self.client.pipeline()
            
            for data in data_list:
                if "id" not in data:
                    logger.warning("Redis缓存批量插入跳过：数据必须包含'id'字段作为键")
                    continue
                
                key = self._get_key(table_name, data["id"])
                ttl = data.get("ttl", self.default_ttl)
                
                # 移除ttl字段
                if "ttl" in data:
                    del data["ttl"]
                
                # 序列化数据并添加到管道
                serialized_data = self._serialize(data)
                pipe.set(key, serialized_data, ex=ttl)
                success += 1
            
            # 执行批量操作
            await pipe.execute()
            return (success, total)
        except Exception as e:
            self._handle_exception(e, f"批量插入数据到Redis缓存 {table_name}")
            return (0, total)
    
    async def update(self, table_name: str, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """
        更新缓存中的数据
        
        :param table_name: 表/集合名称，用于分类
        :param conditions: 更新条件，Redis中只支持通过id更新，条件格式应为{"id": "xxx"}
        :param data: 要更新的数据
        :return: 受影响的行数
        """
        if "id" not in conditions:
            logger.warning("Redis缓存更新失败：条件必须包含'id'字段")
            return 0
            
        key = self._get_key(table_name, conditions["id"])
        
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return 0
        
        try:
            # 先获取现有数据
            existing_data = await self.client.get(key)
            if not existing_data:
                return 0
            
            # 反序列化并更新数据
            deserialized_data = self._deserialize(existing_data)
            deserialized_data.update(data)
            
            # 移除ttl字段（如果存在）
            if "ttl" in deserialized_data:
                ttl = deserialized_data["ttl"]
                del deserialized_data["ttl"]
            else:
                ttl = self.default_ttl
            
            # 重新序列化并存储
            serialized_data = self._serialize(deserialized_data)
            await self.client.set(key, serialized_data, ex=ttl)
            return 1
        except Exception as e:
            self._handle_exception(e, f"更新Redis缓存 {table_name} 数据")
            return 0
    
    async def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """
        删除缓存中的数据
        
        :param table_name: 表/集合名称，用于分类
        :param conditions: 删除条件，可以是{"id": "xxx"}或{"pattern": "xxx*"}
        :return: 受影响的行数
        """
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return 0
        
        try:
            if "id" in conditions:
                # 删除单个键
                key = self._get_key(table_name, conditions["id"])
                result = await self.client.delete(key)
                return result
            elif "pattern" in conditions:
                # 按模式删除多个键
                pattern = self._get_key(table_name, conditions["pattern"])
                keys = await self.client.keys(pattern)
                if keys:
                    result = await self.client.delete(*keys)
                    return result
                return 0
            else:
                logger.warning("Redis缓存删除失败：条件必须包含'id'或'pattern'字段")
                return 0
        except Exception as e:
            self._handle_exception(e, f"删除Redis缓存 {table_name} 数据")
            return 0
    
    async def query(self, 
                   table_name: str, 
                   conditions: Optional[Dict[str, Any]] = None,
                   fields: Optional[List[str]] = None,
                   sort: Optional[List[Tuple[str, int]]] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询缓存中的数据
        
        :param table_name: 表/集合名称，用于分类
        :param conditions: 查询条件，可以是{"id": "xxx"}或{"pattern": "xxx*"}
        :param fields: 要返回的字段列表，None表示返回所有字段
        :param sort: 排序条件（Redis中不支持复杂排序，仅作占位）
        :param limit: 返回结果的最大数量
        :param offset: 结果偏移量，用于分页
        :return: 查询结果列表
        """
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return []
        
        try:
            results = []
            
            if not conditions or ("id" in conditions and conditions["id"] == "*"):
                # 查询指定表的所有数据
                pattern = self._get_key(table_name, "*")
                keys = await self.client.keys(pattern)
            elif "id" in conditions:
                # 查询单个键
                key = self._get_key(table_name, conditions["id"])
                keys = [key] if await self.client.exists(key) else []
            elif "pattern" in conditions:
                # 按模式查询
                pattern = self._get_key(table_name, conditions["pattern"])
                keys = await self.client.keys(pattern)
            else:
                logger.warning("Redis缓存查询失败：条件必须包含'id'或'pattern'字段")
                return []
            
            # 应用分页偏移
            if offset and offset > 0 and len(keys) > offset:
                keys = keys[offset:]
            else:
                offset = 0
            
            # 应用数量限制
            if limit and limit > 0 and len(keys) > limit:
                keys = keys[:limit]
            
            # 获取数据
            for key in keys:
                data = await self.client.get(key)
                if data:
                    deserialized_data = self._deserialize(data)
                    # 过滤字段
                    if fields:
                        filtered_data = {k: v for k, v in deserialized_data.items() if k in fields}
                        results.append(filtered_data)
                    else:
                        results.append(deserialized_data)
            
            # Redis不支持复杂排序，简单排序仅作演示
            if sort and results:
                for field, direction in sort:
                    results.sort(key=lambda x: x.get(field, ""), reverse=(direction == -1))
            
            return results
        except Exception as e:
            self._handle_exception(e, f"查询Redis缓存 {table_name} 数据")
            return []
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """
        Redis不需要创建表，此方法仅作兼容接口
        
        :param table_name: 表/集合名称
        :param schema: 表结构定义（Redis中忽略）
        :return: 始终返回True
        """
        # Redis是无模式的，不需要创建表
        logger.info(f"Redis缓存不需要创建表：{table_name}")
        return True
    
    async def exists(self, table_name: str, conditions: Dict[str, Any]) -> bool:
        """
        检查缓存中是否存在符合条件的记录
        
        :param table_name: 表/集合名称，用于分类
        :param conditions: 检查条件，必须包含"id"字段
        :return: 存在返回True，否则返回False
        """
        if "id" not in conditions:
            logger.warning("Redis缓存存在性检查失败：条件必须包含'id'字段")
            return False
            
        key = self._get_key(table_name, conditions["id"])
        
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            self._handle_exception(e, f"检查Redis缓存 {table_name} 记录存在性")
            return False
    
    async def get_ttl(self, table_name: str, id: str) -> int:
        """
        获取指定键的剩余过期时间（秒）
        
        :param table_name: 表/集合名称
        :param id: 数据ID
        :return: 剩余过期时间（秒），-1表示永不过期，-2表示键不存在
        """
        key = self._get_key(table_name, id)
        
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return -2
        
        try:
            return await self.client.ttl(key)
        except Exception as e:
            self._handle_exception(e, f"获取Redis缓存 {table_name} 过期时间")
            return -2
    
    async def expire(self, table_name: str, id: str, ttl: int) -> bool:
        """
        设置指定键的过期时间
        
        :param table_name: 表/集合名称
        :param id: 数据ID
        :param ttl: 过期时间（秒）
        :return: 操作成功返回True，否则返回False
        """
        key = self._get_key(table_name, id)
        
        if not self.connected or not self.client:
            # 尝试重新连接
            if not await self.connect():
                return False
        
        try:
            return await self.client.expire(key, ttl)
        except Exception as e:
            self._handle_exception(e, f"设置Redis缓存 {table_name} 过期时间")
            return False


# 测试代码
async def test_redis_cache():
    """测试Redis缓存组件"""
    # 配置
    config = {
        "url": "redis://localhost:6379/0",
        "default_ttl": 300,  # 默认5分钟过期
        "key_prefix": "stock_test:"
    }
    
    # 创建缓存实例
    cache = RedisCache(config)
    
    # 连接Redis
    if not await cache.connect():
        print("连接Redis失败")
        return
    
    try:
        # 插入单条数据
        stock_data = {
            "id": "sh600000",
            "code": "sh600000",
            "name": "浦发银行",
            "price": 8.60,
            "change_pct": 1.17,
            "ttl": 600  # 10分钟过期
        }
        success = await cache.insert("stock_quote", stock_data)
        print(f"插入单条数据: {'成功' if success else '失败'}")
        
        # 批量插入数据
        batch_data = [
            {
                "id": "sz000001",
                "code": "sz000001",
                "name": "平安银行",
                "price": 12.35,
                "change_pct": 0.82
            },
            {
                "id": "sz002594",
                "code": "sz002594",
                "name": "比亚迪",
                "price": 250.60,
                "change_pct": 2.35
            }
        ]
        success_count, total_count = await cache.batch_insert("stock_quote", batch_data)
        print(f"批量插入数据: 成功 {success_count}/{total_count}")
        
        # 查询单条数据
        single_result = await cache.query(
            "stock_quote",
            conditions={"id": "sh600000"}
        )
        print("查询单条数据:")
        print(single_result)
        
        # 按模式查询
        pattern_results = await cache.query(
            "stock_quote",
            conditions={"pattern": "sz*"},
            sort=[("price", 1)],  # 按价格升序
            limit=10
        )
        print("按模式查询数据:")
        for item in pattern_results:
            print(item)
        
        # 更新数据
        update_count = await cache.update(
            "stock_quote",
            conditions={"id": "sh600000"},
            data={"price": 8.65, "change_pct": 1.74}
        )
        print(f"更新数据行数: {update_count}")
        
        # 检查记录是否存在
        exists = await cache.exists(
            "stock_quote",
            conditions={"id": "sh600000"}
        )
        print(f"记录是否存在: {exists}")
        
        # 查看过期时间
        ttl = await cache.get_ttl("stock_quote", "sh600000")
        print(f"剩余过期时间: {ttl}秒")
        
    finally:
        # 清理测试数据
        await cache.delete("stock_quote", conditions={"pattern": "*"})
        
        # 断开连接
        await cache.disconnect()

if __name__ == "__main__":
    asyncio.run(test_redis_cache())
