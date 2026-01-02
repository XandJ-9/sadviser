"""
AkshareCrawler测试类
测试Akshare数据爬取功能
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from data.crawler.akshare_crawler import AkshareCrawler


@pytest.fixture
def akshare_crawler():
    """创建AkshareCrawler实例"""
    try:
        return AkshareCrawler(max_retries=3, timeout=10, delay=1.0)
    except ImportError:
        pytest.skip("Akshare库未安装，请运行: pip install akshare")


@pytest.fixture
def mock_akshare_daily_response():
    """模拟Akshare日线数据响应"""
    # Akshare返回的DataFrame格式
    data = {
        '日期': ['2024-01-02', '2024-01-03', '2024-01-04'],
        '股票代码': ['000001', '000001', '000001'],
        '开盘': [9.39, 9.19, 9.19],
        '收盘': [9.21, 9.20, 9.11],
        '最高': [9.42, 9.22, 9.19],
        '最低': [9.31, 9.15, 9.05],
        '成交量': [107574200, 67367300, 78747000],
        '成交额': [1075742000, 673673600, 787470100],
        '振幅': [2.24, 0.76, 1.20],
        '涨跌幅': [-1.92, -0.11, -0.98],
        '涨跌额': [-0.18, -0.01, -0.09],
        '换手率': [0.60, 0.38, 0.45]
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_akshare_realtime_response():
    """模拟Akshare实时行情响应"""
    # Akshare实时行情DataFrame格式
    data = {
        '代码': ['000001', '600000'],
        '名称': ['平安银行', '浦发银行'],
        '最新价': [11.41, 12.44],
        '昨收': [11.48, 12.39],
        '最高': [11.45, 12.50],
        '最低': [11.35, 12.30],
        '成交量': [12345678, 23456789],
        '成交额': [1.234e9, 2.345e9],
        '买一': [11.40, 12.43],
        '卖一': [11.42, 12.45],
        '涨跌幅': [-0.61, 0.40]
    }
    return pd.DataFrame(data)


class TestAkshareCrawlerInit:
    """测试AkshareCrawler初始化"""

    def test_init_default_params(self, akshare_crawler):
        """测试默认参数初始化"""
        assert akshare_crawler.max_retries == 3
        assert akshare_crawler.timeout == 10
        assert akshare_crawler.delay == 1.0

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        crawler = AkshareCrawler(max_retries=5, timeout=15, delay=2.0)
        assert crawler.max_retries == 5
        assert crawler.timeout == 15
        assert crawler.delay == 2.0

    def test_requires_akshare(self):
        """测试Akshare库依赖"""
        # 如果akshare未安装，应该抛出ImportError
        try:
            import akshare
            assert True
        except ImportError:
            with pytest.raises(ImportError):
                # 模拟akshare未安装的情况
                import data.crawler.akshare_crawler as ak_module
                original_ak = ak_module.ak
                ak_module.ak = None
                try:
                    AkshareCrawler()
                finally:
                    ak_module.ak = original_ak


class TestAkshareCrawlerFetchDailyData:
    """测试日线数据获取"""

    @pytest.mark.asyncio
    async def test_fetch_daily_data_success(self, akshare_crawler, mock_akshare_daily_response):
        """测试成功获取日线数据"""
        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_hist') as mock_hist:
            mock_hist.return_value = mock_akshare_daily_response

            df = await akshare_crawler.fetch_daily_data('000001', '2024-01-01', '2024-01-10')

            # 验证返回的DataFrame
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            assert 'symbol' in df.columns
            assert 'date' in df.columns
            assert df['symbol'].iloc[0] == '000001'
            assert df['date'].dtype.name == 'datetime64[ns]'

    @pytest.mark.asyncio
    async def test_fetch_daily_data_with_prefix(self, akshare_crawler, mock_akshare_daily_response):
        """测试带前缀的股票代码"""
        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_hist') as mock_hist:
            mock_hist.return_value = mock_akshare_daily_response

            # 测试上海股票
            df_sh = await akshare_crawler.fetch_daily_data('sh600000', '2024-01-01', '2024-01-10')
            assert len(df_sh) == 3

            # 测试深圳股票
            df_sz = await akshare_crawler.fetch_daily_data('sz000001', '2024-01-01', '2024-01-10')
            assert len(df_sz) == 3

    @pytest.mark.asyncio
    async def test_fetch_daily_data_invalid_date_range(self, akshare_crawler):
        """测试无效的日期范围"""
        df = await akshare_crawler.fetch_daily_data('000001', '2024-12-31', '2024-01-01')

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_empty_response(self, akshare_crawler):
        """测试空响应"""
        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_hist') as mock_hist:
            mock_hist.return_value = pd.DataFrame()

            df = await akshare_crawler.fetch_daily_data('000001', '2024-01-01', '2024-01-10')

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_api_error(self, akshare_crawler):
        """测试API错误"""
        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_hist') as mock_hist:
            mock_hist.side_effect = Exception("API error")

            df = await akshare_crawler.fetch_daily_data('000001', '2024-01-01', '2024-01-10')

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0


class TestAkshareCrawlerFetchRealtimeQuote:
    """测试实时行情获取"""

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_success(self, akshare_crawler, mock_akshare_realtime_response):
        """测试成功获取实时行情"""
        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_spot_em') as mock_spot:
            mock_spot.return_value = mock_akshare_realtime_response

            quotes = await akshare_crawler.fetch_realtime_quote(['000001', '600000'])

            # 验证返回的行情数据
            assert isinstance(quotes, dict)
            assert len(quotes) == 2
            assert '000001' in quotes
            assert '600000' in quotes

            # 验证行情数据结构
            quote = quotes['000001']
            assert 'name' in quote
            assert quote['name'] == '平安银行'
            assert 'price' in quote
            assert 'open' in quote
            assert 'high' in quote
            assert 'low' in quote
            assert 'volume' in quote
            assert 'change' in quote
            assert 'change_percent' in quote

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_with_prefix(self, akshare_crawler, mock_akshare_realtime_response):
        """测试带前缀的股票代码"""
        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_spot_em') as mock_spot:
            mock_spot.return_value = mock_akshare_realtime_response

            quotes = await akshare_crawler.fetch_realtime_quote(['sh600000', 'sz000001'])

            assert isinstance(quotes, dict)
            assert len(quotes) == 2
            assert 'sh600000' in quotes
            assert 'sz000001' in quotes

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_empty_list(self, akshare_crawler):
        """测试空股票列表"""
        quotes = await akshare_crawler.fetch_realtime_quote([])

        assert isinstance(quotes, dict)
        assert len(quotes) == 0

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_change_calculation(self, akshare_crawler):
        """测试涨跌幅计算"""
        test_data = pd.DataFrame({
            '代码': ['000001'],
            '名称': ['测试股票'],
            '最新价': [10.50],
            '昨收': [10.00],
            '最高': [10.60],
            '最低': [10.40],
            '成交量': [1000000],
            '成交额': [10000000],
            '买一': [10.49],
            '卖一': [10.51]
        })

        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_spot_em') as mock_spot:
            mock_spot.return_value = test_data

            quotes = await akshare_crawler.fetch_realtime_quote(['000001'])

            assert '000001' in quotes
            quote = quotes['000001']
            assert quote['price'] == 10.50
            assert quote['change'] == 0.50
            assert quote['change_percent'] == 5.0

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_not_found(self, akshare_crawler):
        """测试股票代码未找到"""
        test_data = pd.DataFrame({
            '代码': ['000002'],
            '名称': ['万科A'],
            '最新价': [10.00],
            '昨收': [9.90],
            '最高': [10.10],
            '最低': [9.80],
            '成交量': [1000000],
            '成交额': [10000000],
            '买一': [9.99],
            '卖一': [10.01]
        })

        with patch('data.crawler.akshare_crawler.ak.stock_zh_a_spot_em') as mock_spot:
            mock_spot.return_value = test_data

            quotes = await akshare_crawler.fetch_realtime_quote(['000001'])

            # 未找到的股票不在结果中
            assert '000001' not in quotes
            assert len(quotes) == 0


class TestAkshareCrawlerFetchStockList:
    """测试股票列表获取"""

    @pytest.mark.asyncio
    async def test_fetch_stock_list_success(self, akshare_crawler):
        """测试成功获取股票列表"""
        mock_data = pd.DataFrame({
            'code': ['000001', '000002', '600000'],
            'name': ['平安银行', '万科A', '浦发银行']
        })

        with patch('data.crawler.akshare_crawler.ak.stock_info_a_code_name') as mock_list:
            mock_list.return_value = mock_data

            df = await akshare_crawler.fetch_stock_list()

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3

    @pytest.mark.asyncio
    async def test_fetch_stock_list_empty(self, akshare_crawler):
        """测试空响应"""
        with patch('data.crawler.akshare_crawler.ak.stock_info_a_code_name') as mock_list:
            mock_list.return_value = pd.DataFrame()

            df = await akshare_crawler.fetch_stock_list()

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_stock_list_error(self, akshare_crawler):
        """测试API错误"""
        with patch('data.crawler.akshare_crawler.ak.stock_info_a_code_name') as mock_list:
            mock_list.side_effect = Exception("API error")

            df = await akshare_crawler.fetch_stock_list()

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0


@pytest.mark.parametrize("symbol,expected_clean", [
    ('sh600000', '600000'),
    ('sz000001', '000001'),
    ('600000', '600000'),
    ('000001', '000001'),
])
def test_symbol_cleaning(symbol, expected_clean):
    """测试股票代码清理"""
    clean = symbol.replace('sh', '').replace('sz', '')
    assert clean == expected_clean


@pytest.mark.parametrize("date_str,expected_format", [
    ('2024-01-01', '20240101'),
    ('2024-12-31', '20241231'),
    ('2023-06-15', '20230615'),
])
def test_date_format_conversion(date_str, expected_format):
    """测试日期格式转换（Akshare需要YYYYMMDD格式）"""
    converted = date_str.replace('-', '')
    assert converted == expected_format


class TestAkshareCrawlerIntegration:
    """集成测试（需要实际Akshare API）"""

    @pytest.mark.slow
    @pytest.mark.requires_network
    @pytest.mark.asyncio
    async def test_real_akshare_api_call(self, akshare_crawler):
        """真实API调用测试（需要网络，默认跳过）"""
        # 这个测试只有在需要测试真实API时才运行
        # 使用 pytest -m "requires_network" 来运行

        # 测试获取日线数据
        df = await akshare_crawler.fetch_daily_data('000001', '2024-12-01', '2024-12-05')

        # 验证基本结构
        assert isinstance(df, pd.DataFrame)
        if not df.empty:
            assert 'symbol' in df.columns
            assert 'date' in df.columns
            print(f"\n获取到 {len(df)} 条真实数据")
            print(df.head())
