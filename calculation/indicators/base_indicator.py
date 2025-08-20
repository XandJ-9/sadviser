import logging
import pandas as pd
from typing import Dict, List, Optional, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseIndicator:
    """技术指标计算基类，定义所有指标计算类的统一接口"""
    
    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        """
        初始化指标计算类
        
        :param name: 指标名称 
        :param params: 指标参数字典，如{"window": 20}
        """
        self.name = name
        self.params = params or {}
        self.validate_params()  # 验证参数有效性
        
        # 存储计算结果
        self.results: Optional[pd.DataFrame] = None
        z
        # 指标所需的基础数据列
        self.required_columns = ["open", "high", "low", "close", "volume"]
    
    def validate_params(self) -> None:
        """
        验证指标参数的有效性，子类应根据自身需求重写此方法
        
        :raises ValueError: 当参数无效时抛出异常
        """
        # 基类仅做基础验证，子类应实现具体验证逻辑
        for param_name, value in self.params.items():
            if isinstance(value, (int, float)) and value <= 0:
                raise ValueError(f"指标参数 {param_name} 必须为正数，当前值: {value}")
    
    def check_required_data(self, data: pd.DataFrame) -> bool:
        """
        检查输入数据是否包含计算指标所需的所有列
        
        :param data: 输入数据，包含股票价格和成交量等基础数据
        :return: 包含所有必要列返回True，否则返回False
        """
        missing_columns = [col for col in self.required_columns if col not in data.columns]
        
        if missing_columns:
            logger.error(f"计算指标 {self.name} 缺少必要的数据列: {missing_columns}")
            return False
        
        # 检查是否有缺失值
        if data[self.required_columns].isnull().any().any():
            logger.warning(f"输入数据包含缺失值，可能影响指标 {self.name} 的计算结果")
        
        return True
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算指标的主方法，子类必须实现
        
        :param data: 输入数据，包含至少["open", "high", "low", "close", "volume"]列
        :return: 包含计算出的指标列的DataFrame
        :raises NotImplementedError: 如果子类未实现此方法则抛出异常
        """
        raise NotImplementedError("子类必须实现calculate方法")
    
    def get_results(self) -> Optional[pd.DataFrame]:
        """
        获取计算结果
        
        :return: 包含指标计算结果的DataFrame，或None如果尚未计算
        """
        return self.results
    
    def explain(self) -> Dict[str, Any]:
        """
        解释指标的含义、计算方法和参数说明
        
        :return: 包含指标解释信息的字典
        """
        return {
            "name": self.name,
            "description": "未提供指标描述",
            "params": self.params,
            "interpretation": "未提供指标解读方法"
        }
    
    def __str__(self) -> str:
        """返回指标的字符串表示"""
        return f"{self.name}({', '.join([f'{k}={v}' for k, v in self.params.items()])})"
    
    def __repr__(self) -> str:
        """返回指标的详细字符串表示"""
        return f"{self.__class__.__name__}(name='{self.name}', params={self.params})"


class IndicatorCombiner:
    """指标组合器，用于同时计算多个技术指标"""
    
    def __init__(self, indicators: List[BaseIndicator]):
        """
        初始化指标组合器
        
        :param indicators: 要组合的指标实例列表
        """
        self.indicators = indicators
        self._check_indicator_names()
    
    def _check_indicator_names(self) -> None:
        """检查指标名称是否存在冲突"""
        names = [indicator.name for indicator in self.indicators]
        if len(names) != len(set(names)):
            duplicates = [name for name in set(names) if names.count(name) > 1]
            logger.warning(f"发现重复的指标名称: {duplicates}，可能导致结果列覆盖")
    
    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有指标并合并结果
        
        :param data: 输入数据，包含基础价格和成交量数据
        :return: 包含所有指标计算结果的DataFrame
        """
        # 复制原始数据，避免修改输入
        result_df = data.copy()
        
        for indicator in self.indicators:
            try:
                # 检查数据是否满足指标计算要求
                if not indicator.check_required_data(data):
                    logger.warning(f"跳过指标 {indicator.name} 的计算")
                    continue
                
                # 计算指标
                indicator_results = indicator.calculate(data)
                
                # 合并结果，只添加新列
                new_columns = [col for col in indicator_results.columns if col not in result_df.columns]
                result_df = result_df.join(indicator_results[new_columns])
                
                logger.info(f"成功计算指标: {indicator}")
                
            except Exception as e:
                logger.error(f"计算指标 {indicator.name} 时发生错误: {str(e)}", exc_info=True)
        
        return result_df
    
    def get_indicators(self) -> List[BaseIndicator]:
        """
        获取所有指标实例
        
        :return: 指标实例列表
        """
        return self.indicators
    
    def explain_all(self) -> List[Dict[str, Any]]:
        """
        获取所有指标的解释信息
        
        :return: 包含所有指标解释信息的列表
        """
        return [indicator.explain() for indicator in self.indicators]
    
    def __len__(self) -> int:
        """返回组合中指标的数量"""
        return len(self.indicators)
