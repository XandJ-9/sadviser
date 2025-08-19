import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .base_crawler import BaseCrawler

# 配置日志
logger = logging.getLogger(__name__)

class TushareCrawler(BaseCrawler):
    """Tushare数据爬取器，获取专业股票数据"""
    
    def __init__(self, token: str, max_retries: int = 3, timeout: int = 15, delay: float = 2.0):
        """
        初始化Tushare爬虫
        
        :param token: Tushare API访问令牌，需在Tushare官网注册获取
        :param max_retries: 最大重试次数
        :param timeout: 请求超时时间(秒)
        :param delay: 请求间隔时间(秒)，Tushare有访问频率限制
        """
        super().__init__(max_retries, timeout, delay)
        self.token = token
        self.base_url = "http://api.tushare.pro"
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # 验证token是否有效
        if not self.token:
            logger.warning("Tushare token未设置，部分API可能无法访问")
    
    async def _post_with_retry(self, api_name: str, params: Dict) -> Optional[Dict]:
        """
        带重试机制的HTTP POST请求，适用于Tushare API
        
        :param api_name: Tushare API名称
        :param params: 请求参数
        :return: 响应JSON数据，失败则返回None
        """
        # 添加token到参数
        params_with_token = {** params, "token": self.token}
        
        # 构建请求体
        payload = {
            "api_name": api_name,
            "params": params_with_token,
            "fields": ""
        }
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    # 检查API返回状态
                    if result.get("code") != 0:
                        logger.warning(f"Tushare API错误: {result.get('msg')}, API: {api_name}, 尝试 {attempt + 1}/{self.max_retries}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 **attempt)
                            continue
                        else:
                            return None
                    
                    await asyncio.sleep(self.delay)
                    return result
                    
            except Exception as e:
                logger.warning(f"请求失败(尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2** attempt)
                else:
                    logger.error(f"达到最大重试次数，请求失败: {api_name}")
                    return None
    
    async def fetch_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        :param symbol: 股票代码，如'600000.SH'表示上海证券交易所的浦发银行
        :param start_date: 开始日期，格式'YYYY-MM-DD'
        :param end_date: 结束日期，格式'YYYY-MM-DD'
        :return: 包含日线数据的DataFrame
        """
        # 验证日期
        if not self._validate_dates(start_date, end_date):
            return self._create_empty_dataframe()
        
        # 处理股票代码格式，Tushare使用'600000.SH'格式
        if symbol.startswith('sh'):
            ts_code = f"{symbol[2:]}.SH"
        elif symbol.startswith('sz'):
            ts_code = f"{symbol[2:]}.SZ"
        else:
            ts_code = symbol  # 假设已经是Tushare格式
        
        logger.info(f"获取Tushare日线数据: {ts_code}，从 {start_date} 到 {end_date}")
        
        # 调用Tushare的daily接口
        result = await self._post_with_retry(
            api_name="daily",
            params={
                "ts_code": ts_code,
                "start_date": start_date.replace("-", ""),
                "end_date": end_date.replace("-", "")
            }
        )
        
        if not result or not result.get("data") or not result["data"].get("items"):
            logger.warning(f"未获取到 {ts_code} 的日线数据")
            return self._create_empty_dataframe()
        
        # 解析返回数据
        try:
            columns = result["data"]["fields"]
            items = result["data"]["items"]
            
            df = pd.DataFrame(items, columns=columns)
            
            # 数据处理
            if not df.empty:
                # 重命名列以保持与系统一致
                column_mapping = {
                    "ts_code": "symbol",
                    "trade_date": "date",
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "vol": "volume",
                    "amount": "amount"
                }
                df = df.rename(columns=column_mapping)
                
                # 转换日期格式
                df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
                
                # 确保只保留需要的列
                required_columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount']
                df = df.reindex(columns=required_columns)
                
                # 按日期排序
                df = df.sort_values("date").reset_index(drop=True)
            
            logger.info(f"成功获取 {ts_code} 的日线数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"解析 {ts_code} 的日线数据失败: {str(e)}")
            return self._create_empty_dataframe()
    
    async def fetch_realtime_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取股票实时行情
        
        :param symbols: 股票代码列表，如['sh600000', 'sz000001']
        :return: 实时行情数据字典，key为股票代码，value为行情数据
        """
        if not symbols:
            return {}
        
        # 转换股票代码为Tushare格式
        ts_codes = []
        code_mapping = {}  # 用于将Tushare格式映射回原始格式
        
        for symbol in symbols:
            if symbol.startswith('sh'):
                ts_code = f"{symbol[2:]}.SH"
            elif symbol.startswith('sz'):
                ts_code = f"{symbol[2:]}.SZ"
            else:
                ts_code = symbol
                code_mapping[ts_code] = symbol
            
            ts_codes.append(ts_code)
            code_mapping[ts_code] = symbol
        
        logger.info(f"获取Tushare实时行情，股票数量: {len(ts_codes)}")
        
        # 调用Tushare的stock_basic接口获取实时行情
        result = await self._post_with_retry(
            api_name="stock_basic",
            params={
                "ts_code": ",".join(ts_codes),
                "exchange": "",
                "list_status": "L",  # 上市
                "fields": "ts_code,name,open,high,low,last,pre_close,vol,amount,up_limit,down_limit"
            }
        )
        
        if not result or not result.get("data") or not result["data"].get("items"):
            logger.warning("未获取到实时行情数据")
            return {}
        
        # 解析返回数据
        try:
            columns = result["data"]["fields"]
            items = result["data"]["items"]
            
            quotes = {}
            update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for item in items:
                quote_dict = dict(zip(columns, item))
                ts_code = quote_dict["ts_code"]
                original_symbol = code_mapping.get(ts_code, ts_code)
                
                # 计算涨跌幅
                last_price = float(quote_dict.get("last", 0))
                pre_close = float(quote_dict.get("pre_close", 0))
                
                change = None
                change_percent = None
                if pre_close > 0:
                    change = last_price - pre_close
                    change_percent = (change / pre_close) * 100
                
                # 整理行情数据
                quotes[original_symbol] = {
                    "name": quote_dict.get("name", ""),
                    "open": float(quote_dict.get("open", 0)) if quote_dict.get("open") else None,
                    "prev_close": float(quote_dict.get("pre_close", 0)) if quote_dict.get("pre_close") else None,
                    "price": last_price if last_price > 0 else None,
                    "high": float(quote_dict.get("high", 0)) if quote_dict.get("high") else None,
                    "low": float(quote_dict.get("low", 0)) if quote_dict.get("low") else None,
                    "volume": float(quote_dict.get("vol", 0)) if quote_dict.get("vol") else None,
                    "amount": float(quote_dict.get("amount", 0)) if quote_dict.get("amount") else None,
                    "up_limit": float(quote_dict.get("up_limit", 0)) if quote_dict.get("up_limit") else None,
                    "down_limit": float(quote_dict.get("down_limit", 0)) if quote_dict.get("down_limit") else None,
                    "change": change,
                    "change_percent": change_percent,
                    "update_time": update_time
                }
            
            logger.info(f"成功获取 {len(quotes)} 条实时行情数据")
            return quotes
            
        except Exception as e:
            logger.error(f"解析实时行情数据失败: {str(e)}")
            return {}
    
    async def fetch_stock_basic(self, exchange: str = "", market: str = "") -> pd.DataFrame:
        """
        获取股票基本信息
        
        :param exchange: 交易所代码，SH-上交所，SZ-深交所
        :param market: 市场类型，主板、创业板、科创板等
        :return: 包含股票基本信息的DataFrame
        """
        params = {
            "exchange": exchange,
            "list_status": "L",  # 上市
            "market": market,
            "fields": "ts_code,symbol,name,area,industry,fullname,enname,market,exchange,curr_type,"
                      "list_status,list_date,delist_date,is_hs"
        }
        
        result = await self._post_with_retry(
            api_name="stock_basic",
            params=params
        )
        
        if not result or not result.get("data") or not result["data"].get("items"):
            logger.warning("未获取到股票基本信息")
            return pd.DataFrame()
        
        try:
            columns = result["data"]["fields"]
            items = result["data"]["items"]
            
            df = pd.DataFrame(items, columns=columns)
            logger.info(f"成功获取 {len(df)} 条股票基本信息")
            return df
            
        except Exception as e:
            logger.error(f"解析股票基本信息失败: {str(e)}")
            return pd.DataFrame()

# 测试代码
async def test_tushare_crawler():
    """测试Tushare爬虫"""
    # 请替换为您的Tushare token
    TUSHARE_TOKEN = "your_tushare_token_here"
    
    if TUSHARE_TOKEN == "your_tushare_token_here":
        print("请先设置您的Tushare token")
        return
    
    async with TushareCrawler(TUSHARE_TOKEN) as crawler:
        # 测试获取日线数据
        print("测试获取日线数据...")
        df = await crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-12-31')
        print(f"获取到 {len(df)} 条日线数据")
        if not df.empty:
            print(df.head())
        
        # 测试获取实时行情
        print("\n测试获取实时行情...")
        symbols = ['sh600000', 'sz000001', 'sz300059']
        quotes = await crawler.fetch_realtime_quote(symbols)
        print(f"获取到 {len(quotes)} 条实时行情数据")
        for symbol, quote in quotes.items():
            print(f"{symbol}: {quote['name']} {quote['price']} 元, 涨跌幅: {quote['change_percent']:.2f}%")
        
        # 测试获取股票基本信息
        print("\n测试获取股票基本信息...")
        basic_df = await crawler.fetch_stock_basic(exchange="SH")
        print(f"获取到 {len(basic_df)} 条股票基本信息")
        if not basic_df.empty:
            print(basic_df[['ts_code', 'name', 'industry', 'list_date']].head())

if __name__ == "__main__":
    asyncio.run(test_tushare_crawler())
