import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .base_crawler import BaseCrawler

# 配置日志
logger = logging.getLogger(__name__)

class SinaCrawler(BaseCrawler):
    """新浪财经数据爬取器，获取A股市场数据"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 10, delay: float = 1.0):
        """初始化新浪财经爬虫"""
        super().__init__(max_retries, timeout, delay)
        # 新浪财经API基础URL
        self.base_url = "https://hq.sinajs.cn"
        self.historical_url = "https://finance.sina.com.cn/realstock/company"
        self.headers={
          "Referer":'https://finance.sina.com.cn',
          "Content-Type": 'application/json'
        }
    
    async def fetch_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取新浪财经的股票日线数据
        
        :param symbol: 股票代码，如'sh600000'表示上海证券交易所的浦发银行
        :param start_date: 开始日期，格式'YYYY-MM-DD'
        :param end_date: 结束日期，格式'YYYY-MM-DD'
        :return: 包含日线数据的DataFrame
        """
        # 验证日期
        if not self._validate_dates(start_date, end_date):
            return self._create_empty_dataframe()
        
        # 新浪财经的股票代码格式为sh600000或sz000001
        if not (symbol.startswith('sh') or symbol.startswith('sz')):
            logger.error(f"无效的股票代码格式: {symbol}，应为sh或sz开头")
            return self._create_empty_dataframe()
        
        # 转换日期格式为YYYYMMDD
        start_str = self._convert_date_format(start_date, '%Y-%m-%d', '%Y%m%d')
        end_str = self._convert_date_format(end_date, '%Y-%m-%d', '%Y%m%d')
        
        if not start_str or not end_str:
            return self._create_empty_dataframe()
        
        # 构建URL
        # 新浪财经历史数据API格式: https://finance.sina.com.cn/realstock/company/{symbol}/hisdata/klc_kl.js?from={start}&to={end}
        url = f"{self.historical_url}/{symbol}/hisdata/klc_kl.js"
        params = {
            'from': start_str,
            'to': end_str
        }
        logger.info(f"获取股票日线数据: {symbol}，从 {start_date} 到 {end_date}")
        
        # 发送请求
        response_text = await self._fetch_with_retry(url,params=params, headers=self.headers)
        
        if not response_text:
            logger.error(f"无法获取 {symbol} 的日线数据")
            return self._create_empty_dataframe()
        
        # 解析响应数据
        try:
            # 新浪财经返回的数据格式是var klc_kl_data = [[...], [...]...];
            # 提取数据部分
            start_idx = response_text.find('[[')
            end_idx = response_text.rfind(']]') + 2
            data_str = response_text[start_idx:end_idx]
            
            # 转换为列表
            import ast
            data_list = ast.literal_eval(data_str)
            
            # 转换为DataFrame
            df = pd.DataFrame(data_list, columns=[
                'date', 'open', 'high', 'low', 'close', 'volume', 'amount'
            ])
            
            # 数据类型转换
            df['date'] = pd.to_datetime(df['date'])
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
            
            # 添加股票代码
            df['symbol'] = symbol
            
            # 按日期排序
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"成功获取 {symbol} 的日线数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"解析 {symbol} 的日线数据失败: {str(e)}")
            return self._create_empty_dataframe()
    
    async def fetch_realtime_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取新浪财经的股票实时行情
        
        :param symbols: 股票代码列表，如['sh600000', 'sz000001']
        :return: 实时行情数据字典，key为股票代码，value为行情数据
        """
        if not symbols:
            return {}
        
        # 新浪财经实时行情API一次最多请求400个股票代码
        batch_size = 400
        results = {}
        
        # 分批处理
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            logger.info(f"获取实时行情，批次 {i//batch_size + 1}，股票数量: {len(batch)}")
            
            # 构建请求URL
            symbols_str = ",".join(batch)
            url = f"{self.base_url}?list={symbols_str}"
            
            # 发送请求
            response_text = await self._fetch_with_retry(url, headers=self.headers)
            
            if not response_text:
                logger.error(f"无法获取实时行情，批次 {i//batch_size + 1}")
                continue
            
            # 解析响应
            quotes = self._parse_realtime_quote(response_text, batch)
            results.update(quotes)
        
        return results
    
    def _parse_realtime_quote(self, response_text: str, symbols: List[str]) -> Dict[str, Dict]:
        """
        解析新浪财经的实时行情响应
        
        新浪财经实时行情返回格式:
        var hq_str_sh600000="浦发银行,9.92,9.93,9.91,9.97,9.88,9.91,9.92,12345678,123456789.00,...";
        """
        quotes = {}
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('var hq_str_') or '="' not in line:
                continue
            
            try:
                # 提取股票代码
                code_start = len('var hq_str_')
                code_end = line.find('="')
                symbol = line[code_start:code_end]
                
                if symbol not in symbols:
                    continue
                
                # 提取行情数据
                data_str = line[code_end+2:line.rfind('"')]
                data = data_str.split(',')
                
                if len(data) < 33:  # 确保数据完整性
                    logger.warning(f"实时行情数据不完整: {symbol}")
                    continue
                
                # 解析行情数据
                # 新浪财经行情数据字段说明：
                # 0: 股票名称, 1: 今开, 2: 昨收, 3: 现价, 4: 最高, 5: 最低, 
                # 6: 买一, 7: 卖一, 8: 成交量, 9: 成交额, 
                # 10-14: 买一到买五价格, 15-19: 买一到买五数量,
                # 20-24: 卖一到卖五价格, 25-29: 卖一到卖五数量,
                # 30: 日期, 31: 时间
                quote = {
                    'name': data[0],
                    'open': float(data[1]) if data[1] else None,
                    'prev_close': float(data[2]) if data[2] else None,
                    'price': float(data[3]) if data[3] else None,
                    'high': float(data[4]) if data[4] else None,
                    'low': float(data[5]) if data[5] else None,
                    'bid1': float(data[6]) if data[6] else None,
                    'ask1': float(data[7]) if data[7] else None,
                    'volume': float(data[8]) if data[8] else None,
                    'amount': float(data[9]) if data[9] else None,
                    'bids': {
                        'price': [float(data[i]) if data[i] else None for i in range(10, 15)],
                        'volume': [float(data[i]) if data[i] else None for i in range(15, 20)]
                    },
                    'asks': {
                        'price': [float(data[i]) if data[i] else None for i in range(20, 25)],
                        'volume': [float(data[i]) if data[i] else None for i in range(25, 30)]
                    },
                    'date': data[30],
                    'time': data[31],
                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 计算涨跌幅
                if quote['prev_close'] and quote['price'] and quote['prev_close'] > 0:
                    quote['change'] = quote['price'] - quote['prev_close']
                    quote['change_percent'] = (quote['change'] / quote['prev_close']) * 100
                else:
                    quote['change'] = None
                    quote['change_percent'] = None
                
                quotes[symbol] = quote
                
            except Exception as e:
                logger.error(f"解析实时行情失败，行: {line}, 错误: {str(e)}")
        
        return quotes

# 测试代码
async def test_sina_crawler():
    """测试新浪财经爬虫"""
    async with SinaCrawler() as crawler:
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

if __name__ == "__main__":
    asyncio.run(test_sina_crawler())
