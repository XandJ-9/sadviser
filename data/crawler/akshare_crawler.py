"""
Akshare数据爬取器
使用Akshare库获取东方财富网的股票数据
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None
    logging.warning("Akshare库未安装，请运行: pip install akshare")

from .base_crawler import BaseCrawler, logger


class AkshareCrawler(BaseCrawler):
    """Akshare数据爬取器，获取东方财富网的股票数据"""

    def __init__(self, max_retries: int = 3, timeout: int = 10, delay: float = 1.0):
        """
        初始化Akshare爬虫

        :param max_retries: 最大重试次数
        :param timeout: 请求超时时间(秒)
        :param delay: 请求间隔时间(秒)，避免过于频繁的请求
        """
        super().__init__(max_retries, timeout, delay)

        # 检查akshare是否安装
        if ak is None:
            raise ImportError("Akshare库未安装，请运行: pip install akshare")

        # Akshare使用同步API，不需要设置session
        logger.info("Akshare爬虫初始化成功")

    async def fetch_daily_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据

        :param symbol: 股票代码，如'000001'(平安银行)、'600000'(浦发银行)
        :param start_date: 开始日期，格式'YYYY-MM-DD'
        :param end_date: 结束日期，格式'YYYY-MM-DD'
        :return: 包含日线数据的DataFrame
        """
        # 验证日期
        if not self._validate_dates(start_date, end_date):
            return self._create_empty_dataframe()

        # 转换日期格式为YYYYMMDD
        start_str = self._convert_date_format(start_date, '%Y-%m-%d', '%Y%m%d')
        end_str = self._convert_date_format(end_date, '%Y-%m-%d', '%Y%m%d')

        if not start_str or not end_str:
            return self._create_empty_dataframe()

        # 移除股票代码前缀（sh/sz），Akshare使用纯数字
        clean_symbol = symbol.replace('sh', '').replace('sz', '')

        logger.info(f"获取Akshare日线数据: {clean_symbol}，从 {start_date} 到 {end_date}")

        try:
            # 在线程池中运行同步的akshare API
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zh_a_hist(
                    symbol=clean_symbol,
                    period="daily",
                    start_date=start_str,
                    end_date=end_str,
                    adjust=""  # 不复权
                )
            )

            if df is None or df.empty:
                logger.warning(f"Akshare未获取到 {clean_symbol} 的日线数据")
                return self._create_empty_dataframe()

            # 重命名列以匹配系统标准格式
            column_mapping = {
                '日期': 'date',
                '股票代码': 'symbol',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }

            # 只保留需要的列
            df = df[list(column_mapping.keys())].copy()
            df = df.rename(columns=column_mapping)

            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])

            # 添加完整的股票代码
            df['symbol'] = symbol

            # 按日期排序
            df = df.sort_values('date').reset_index(drop=True)

            logger.info(f"成功获取 {clean_symbol} 的日线数据，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取 {clean_symbol} 的日线数据失败: {str(e)}")
            return self._create_empty_dataframe()

    async def fetch_realtime_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        获取股票实时行情

        :param symbols: 股票代码列表，如['sh600000', 'sz000001']或['600000', '000001']
        :return: 实时行情数据字典，key为股票代码，value为行情数据
        """
        if not symbols:
            return {}

        logger.info(f"获取Akshare实时行情，股票数量: {len(symbols)}")

        try:
            # 在线程池中运行同步的akshare API
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zh_a_spot_em()
            )

            if df is None or df.empty:
                logger.warning("Akshare未获取到实时行情数据")
                return {}

            # 创建代码到完整代码的映射
            symbol_map = {}
            for s in symbols:
                clean = s.replace('sh', '').replace('sz', '')
                # 重新添加前缀用于返回
                if clean.startswith('6'):
                    symbol_map[clean] = f'sh{clean}'
                elif clean.startswith('0') or clean.startswith('3'):
                    symbol_map[clean] = f'sz{clean}'
                else:
                    symbol_map[clean] = s

            quotes = {}
            update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 遍历请求的股票代码
            for symbol in symbols:
                clean_symbol = symbol.replace('sh', '').replace('sz', '')

                # 在返回的数据中查找匹配的股票
                matched_rows = df[df['代码'] == clean_symbol]

                if matched_rows.empty:
                    logger.warning(f"未找到股票 {symbol} 的实时行情")
                    continue

                row = matched_rows.iloc[0]

                # 解析行情数据
                quote = {
                    'name': row.get('名称', ''),
                    'open': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'prev_close': float(row.get('昨收', 0)) if pd.notna(row.get('昨收')) else None,
                    'price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'high': float(row.get('最高', 0)) if pd.notna(row.get('最高')) else None,
                    'low': float(row.get('最低', 0)) if pd.notna(row.get('最低')) else None,
                    'volume': float(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else None,
                    'amount': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'bid1': float(row.get('买一', 0)) if pd.notna(row.get('买一')) else None,
                    'ask1': float(row.get('卖一', 0)) if pd.notna(row.get('卖一')) else None,
                    'update_time': update_time
                }

                # 计算涨跌幅
                if quote['prev_close'] and quote['price'] and quote['prev_close'] > 0:
                    quote['change'] = quote['price'] - quote['prev_close']
                    quote['change_percent'] = (quote['change'] / quote['prev_close']) * 100
                else:
                    quote['change'] = None
                    quote['change_percent'] = None

                # Akshare的实时数据可能没有完整的五档行情，设置为空列表
                quote['bids'] = {
                    'price': [None] * 5,
                    'volume': [None] * 5
                }
                quote['asks'] = {
                    'price': [None] * 5,
                    'volume': [None] * 5
                }

                # 使用原始请求的symbol作为key
                quotes[symbol] = quote

            logger.info(f"成功获取 {len(quotes)} 条实时行情数据")
            return quotes

        except Exception as e:
            logger.error(f"获取Akshare实时行情失败: {str(e)}")
            return {}

    async def fetch_stock_list(self) -> pd.DataFrame:
        """
        获取A股股票列表

        :return: 包含股票列表的DataFrame
        """
        logger.info("获取Akshare A股股票列表")

        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_info_a_code_name()
            )

            if df is None or df.empty:
                logger.warning("未获取到股票列表")
                return pd.DataFrame()

            logger.info(f"成功获取 {len(df)} 只股票的列表")
            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            return pd.DataFrame()


# 测试代码
async def test_akshare_crawler():
    """测试Akshare爬虫"""
    try:
        crawler = AkshareCrawler()

        # 测试获取日线数据
        print("=" * 60)
        print("测试1: 获取日线数据")
        print("=" * 60)
        df = await crawler.fetch_daily_data('000001', '2024-01-01', '2024-01-10')
        print(f"获取到 {len(df)} 条日线数据")
        if not df.empty:
            print(df.head())
            print("\n列名:", df.columns.tolist())

        # 测试获取实时行情
        print("\n" + "=" * 60)
        print("测试2: 获取实时行情")
        print("=" * 60)
        symbols = ['000001', '600000']
        quotes = await crawler.fetch_realtime_quote(symbols)
        print(f"获取到 {len(quotes)} 条实时行情数据")
        for symbol, quote in quotes.items():
            print(f"\n{symbol}: {quote['name']}")
            print(f"  现价: {quote['price']}")
            print(f"  涨跌幅: {quote['change_percent']:.2f}%")

        # 测试获取股票列表
        print("\n" + "=" * 60)
        print("测试3: 获取股票列表")
        print("=" * 60)
        stock_list = await crawler.fetch_stock_list()
        print(f"获取到 {len(stock_list)} 只股票")
        if not stock_list.empty:
            print(stock_list.head(10))

    except ImportError as e:
        print(f"错误: {e}")
        print("请安装akshare: pip install akshare")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_akshare_crawler())
