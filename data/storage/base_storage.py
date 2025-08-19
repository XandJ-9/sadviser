import abc
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseStorage(metaclass=abc.ABCMeta):
    """存储基类，定义所有存储组件的通用接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化存储组件
        
        :param config: 存储配置字典
        """
        self.config = config
        self.connected = False
        
    @abc.abstractmethod
    async def connect(self) -> bool:
        """
        连接到存储系统
        
        :return: 连接成功返回True，否则返回False
        """
        pass
    
    @abc.abstractmethod
    async def disconnect(self) -> None:
        """断开与存储系统的连接"""
        pass
    
    @abc.abstractmethod
    async def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        插入单条数据
        
        :param table_name: 表/集合名称
        :param data: 要插入的数据字典
        :return: 插入成功返回True，否则返回False
        """
        pass
    
    @abc.abstractmethod
    async def batch_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        批量插入数据
        
        :param table_name: 表/集合名称
        :param data_list: 要插入的数据字典列表
        :return: 一个元组，包含(成功插入数量, 总数量)
        """
        pass
    
    @abc.abstractmethod
    async def update(self, table_name: str, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """
        更新数据
        
        :param table_name: 表/集合名称
        :param conditions: 更新条件
        :param data: 要更新的数据
        :return: 受影响的行数
        """
        pass
    
    @abc.abstractmethod
    async def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """
        删除数据
        
        :param table_name: 表/集合名称
        :param conditions: 删除条件
        :return: 受影响的行数
        """
        pass
    
    @abc.abstractmethod
    async def query(self, 
                   table_name: str, 
                   conditions: Optional[Dict[str, Any]] = None,
                   fields: Optional[List[str]] = None,
                   sort: Optional[List[Tuple[str, int]]] = None,  # 例如[("date", 1), ("code", -1)]
                   limit: Optional[int] = None,
                   offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        :param table_name: 表/集合名称
        :param conditions: 查询条件
        :param fields: 要返回的字段列表，None表示返回所有字段
        :param sort: 排序条件，列表中的元组为(字段名, 排序方向)，1为升序，-1为降序
        :param limit: 返回结果的最大数量
        :param offset: 结果偏移量，用于分页
        :return: 查询结果列表
        """
        pass
    
    @abc.abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """
        创建表/集合
        
        :param table_name: 表/集合名称
        :param schema: 表结构定义
        :return: 创建成功返回True，否则返回False
        """
        pass
    
    @abc.abstractmethod
    async def exists(self, table_name: str, conditions: Dict[str, Any]) -> bool:
        """
        检查是否存在符合条件的记录
        
        :param table_name: 表/集合名称
        :param conditions: 检查条件
        :return: 存在返回True，否则返回False
        """
        pass
    
    def _add_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        为数据添加时间戳字段
        
        :param data: 原始数据
        :return: 添加了时间戳的数据
        """
        timestamp = datetime.now().isoformat()
        if "created_at" not in data:
            data["created_at"] = timestamp
        data["updated_at"] = timestamp
        return data
    
    def _validate_conditions(self, conditions: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证并处理查询条件
        
        :param conditions: 原始查询条件
        :return: 处理后的查询条件
        """
        if conditions is None:
            return {}
        
        # 转换日期字符串为datetime对象（如果需要）
        processed_conditions = {}
        for key, value in conditions.items():
            # 处理时间范围查询，如{"date": {"$gte": "2023-01-01", "$lte": "2023-12-31"}}
            if isinstance(value, dict):
                processed_value = {}
                for op, val in value.items():
                    if op in ["$gte", "$lte", "$gt", "$lt"] and isinstance(val, str):
                        # 尝试将字符串转换为datetime对象
                        try:
                            processed_val = datetime.fromisoformat(val)
                        except ValueError:
                            processed_val = val
                    else:
                        processed_val = val
                    processed_value[op] = processed_val
                processed_conditions[key] = processed_value
            else:
                processed_conditions[key] = value
                
        return processed_conditions
    
    def _handle_exception(self, e: Exception, operation: str) -> None:
        """
        统一处理异常
        
        :param e: 异常对象
        :param operation: 正在执行的操作名称
        """
        logger.error(f"存储操作 '{operation}' 失败: {str(e)}")
        # 在生产环境中，这里可以添加更复杂的错误处理，如自动重连等
