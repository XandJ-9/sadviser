import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import aiohttp
import pandas as pd
from utils.custom_logger import CustomLogger

# 配置日志
logger = CustomLogger(
    name="base_crawler",
    log_level=logging.INFO,
    )

class BaseCrawler(ABC):
    """爬虫基类，定义数据爬取的通用接口和基础功能"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 10, delay: float = 1.0):
        """
        初始化爬虫基类
        
        :param max_retries: 最大重试次数
        :param timeout: 请求超时时间(秒)
        :param delay: 请求间隔时间(秒)，避免过于频繁的请求
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.delay = delay
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器进入方法，创建aiohttp会话"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """异步上下文管理器退出方法，关闭aiohttp会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @abstractmethod
    async def fetch_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        :param symbol: 股票代码
        :param start_date: 开始日期，格式'YYYY-MM-DD'
        :param end_date: 结束日期，格式'YYYY-MM-DD'
        :return: 包含日线数据的DataFrame
        """
        pass
    
    @abstractmethod
    async def fetch_realtime_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取股票实时行情
        
        :param symbols: 股票代码列表
        :return: 实时行情数据字典，key为股票代码，value为行情数据
        """
        pass
    
    async def _fetch_with_retry(self, url: str, **kwargs) -> Optional[str]:
        """
        带重试机制的HTTP GET请求
        
        :param url: 请求URL
        :param params: 请求参数
        :return: 响应文本，失败则返回None
        """
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url, **kwargs) as response:
                    response.raise_for_status()  # 抛出HTTP错误状态码
                    await asyncio.sleep(self.delay)  # 控制请求频率
                    return await response.text()
            except Exception as e:
                logger.warning(f"请求失败(尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 **attempt)  # 指数退避策略
                else:
                    logger.error(f"达到最大重试次数，请求失败: {url}")
                    return None
    
    @staticmethod
    def _validate_dates(start_date: str, end_date: str) -> bool:
        """
        验证日期格式和有效性
        
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 日期有效返回True，否则False
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            return start <= end and end <= datetime.now()
        except ValueError:
            logger.error(f"无效的日期格式: {start_date} 或 {end_date}，应为'YYYY-MM-DD'")
            return False
    
    @staticmethod
    def _convert_date_format(date_str: str, from_format: str, to_format: str) -> Optional[str]:
        """
        转换日期格式
        
        :param date_str: 原始日期字符串
        :param from_format: 原始格式
        :param to_format: 目标格式
        :return: 转换后的日期字符串，失败则返回None
        """
        try:
            date_obj = datetime.strptime(date_str, from_format)
            return date_obj.strftime(to_format)
        except ValueError:
            logger.error(f"日期格式转换失败: {date_str} 从 {from_format} 到 {to_format}")
            return None

    @staticmethod
    def _create_empty_dataframe() -> pd.DataFrame:
        """创建一个空的日线数据DataFrame，包含标准列"""
        return pd.DataFrame(columns=[
            'symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount'
        ])
