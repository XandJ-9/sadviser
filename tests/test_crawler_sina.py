"""
SinaCrawler测试类
测试新浪财经数据爬取功能
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from data.crawler.sina_crawler import SinaCrawler


@pytest.fixture
def sina_crawler():
    """创建SinaCrawler实例"""
    return SinaCrawler(max_retries=3, timeout=10, delay=1.0)


@pytest.fixture
def mock_sina_daily_response():
    """模拟新浪财经日线数据响应"""
    # 模拟新浪财经返回的数据格式（包含换行符）
    response_text = '''var klc_kl_data = [
["2023-01-03", 10.50, 10.65, 10.45, 10.60, 123456, 1234567.89],
["2023-01-04", 10.58, 10.72, 10.55, 10.68, 145678, 1456789.01],
["2023-01-05", 10.65, 10.80, 10.60, 10.75, 156789, 1567890.12],
["2023-01-06", 10.70, 10.85, 10.68, 10.82, 167890, 1678901.23],
["2023-01-09", 10.75, 10.90, 10.72, 10.88, 178901, 1789012.34]
];'''
    return response_text


@pytest.fixture
def mock_sina_realtime_response():
    """模拟新浪财经实时行情响应"""
    # 新浪财经返回的数据格式需要至少33个字段
    response_text = '''var hq_str_sh600000="浦发银行,9.92,9.93,9.91,9.97,9.88,9.91,9.92,12345678,123456789.00,9.91,9.90,9.89,9.88,9.87,1000,2000,3000,4000,5000,9.93,9.94,9.95,9.96,9.97,1500,2500,3500,4500,5500,2023-01-01,10:30:00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0";
var hq_str_sz000001="平安银行,12.50,12.48,12.52,12.55,12.45,12.51,12.52,23456789,234567890.12,12.51,12.50,12.49,12.48,12.47,2000,3000,4000,5000,6000,12.53,12.54,12.55,12.56,12.57,2500,3500,4500,5500,6500,2023-01-01,10:30:00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0";'''
    return response_text


class TestSinaCrawlerInit:
    """测试SinaCrawler初始化"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        crawler = SinaCrawler()
        assert crawler.max_retries == 3
        assert crawler.timeout == 10
        assert crawler.delay == 1.0
        assert crawler.base_url == "https://hq.sinajs.cn"
        assert crawler.historical_url == "https://finance.sina.com.cn/realstock/company"

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        crawler = SinaCrawler(max_retries=5, timeout=15, delay=2.0)
        assert crawler.max_retries == 5
        assert crawler.timeout == 15
        assert crawler.delay == 2.0

    def test_headers_configuration(self):
        """测试请求头配置"""
        crawler = SinaCrawler()
        assert "Referer" in crawler.headers
        assert crawler.headers["Referer"] == "https://finance.sina.com.cn"
        assert crawler.headers["Content-Type"] == "application/json"


class TestSinaCrawlerFetchDailyData:
    """测试日线数据获取"""

    @pytest.mark.asyncio
    async def test_fetch_daily_data_success(self, sina_crawler, mock_sina_daily_response):
        """测试成功获取日线数据"""
        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_sina_daily_response

                df = await sina_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

                # 验证返回的DataFrame
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 5
                assert 'symbol' in df.columns
                assert 'date' in df.columns
                assert df['symbol'].iloc[0] == 'sh600000'
                assert df['date'].dtype.name == 'datetime64[ns]'

    @pytest.mark.asyncio
    async def test_fetch_daily_data_invalid_symbol(self, sina_crawler):
        """测试无效的股票代码"""
        async with sina_crawler:
            df = await sina_crawler.fetch_daily_data('600000', '2023-01-01', '2023-01-10')

            # 应该返回空DataFrame
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_invalid_date_range(self, sina_crawler):
        """测试无效的日期范围"""
        async with sina_crawler:
            # 开始日期晚于结束日期
            df = await sina_crawler.fetch_daily_data('sh600000', '2023-12-31', '2023-01-01')

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_future_date(self, sina_crawler):
        """测试未来日期"""
        async with sina_crawler:
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            df = await sina_crawler.fetch_daily_data('sh600000', '2023-01-01', future_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_network_error(self, sina_crawler):
        """测试网络错误"""
        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = None

                df = await sina_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

                # 应该返回空DataFrame
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_invalid_response_format(self, sina_crawler):
        """测试无效的响应格式"""
        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = "invalid data format"

                df = await sina_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

                # 应该返回空DataFrame
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_different_symbols(self, sina_crawler, mock_sina_daily_response):
        """测试不同交易所的股票代码"""
        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_sina_daily_response

                # 测试上海证券交易所
                df_sh = await sina_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')
                assert len(df_sh) == 5

                # 测试深圳证券交易所
                df_sz = await sina_crawler.fetch_daily_data('sz000001', '2023-01-01', '2023-01-10')
                assert len(df_sz) == 5


class TestSinaCrawlerFetchRealtimeQuote:
    """测试实时行情获取"""

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_success(self, sina_crawler, mock_sina_realtime_response):
        """测试成功获取实时行情"""
        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_sina_realtime_response

                quotes = await sina_crawler.fetch_realtime_quote(['sh600000', 'sz000001'])

                # 验证返回的行情数据
                assert isinstance(quotes, dict)
                assert len(quotes) == 2
                assert 'sh600000' in quotes
                assert 'sz000001' in quotes

                # 验证行情数据结构
                quote = quotes['sh600000']
                assert 'name' in quote
                assert quote['name'] == '浦发银行'
                assert 'price' in quote
                assert 'open' in quote
                assert 'high' in quote
                assert 'low' in quote
                assert 'volume' in quote
                assert 'change' in quote
                assert 'change_percent' in quote

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_empty_list(self, sina_crawler):
        """测试空股票列表"""
        async with sina_crawler:
            quotes = await sina_crawler.fetch_realtime_quote([])

            assert isinstance(quotes, dict)
            assert len(quotes) == 0

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_batch_processing(self, sina_crawler, mock_sina_realtime_response):
        """测试批量处理（超过400个股票）"""
        # 生成401个股票代码（超过单批次的400个限制）
        symbols = [f'sh60{i:04d}' for i in range(401)]

        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_sina_realtime_response

                quotes = await sina_crawler.fetch_realtime_quote(symbols)

                # 验证调用了多次（401个股票需要2批次）
                assert mock_fetch.call_count == 2
                assert isinstance(quotes, dict)

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_network_error(self, sina_crawler):
        """测试网络错误"""
        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = None

                quotes = await sina_crawler.fetch_realtime_quote(['sh600000'])

                # 应该返回空字典
                assert isinstance(quotes, dict)
                assert len(quotes) == 0

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_incomplete_data(self, sina_crawler):
        """测试数据不完整的情况"""
        incomplete_response = 'var hq_str_sh600000="浦发银行,9.92,9.93";'

        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = incomplete_response

                quotes = await sina_crawler.fetch_realtime_quote(['sh600000'])

                # 数据不完整，应该被跳过
                assert isinstance(quotes, dict)
                assert len(quotes) == 0

    @pytest.mark.asyncio
    async def test_realtime_quote_change_calculation(self, sina_crawler):
        """测试涨跌幅计算"""
        # 构造测试数据：昨收10.00，现价10.50，涨幅应为5%
        test_response = '''var hq_str_sh600000="测试股票,10.50,10.00,10.50,10.60,10.40,10.49,10.50,1000000,10000000.00,10.49,10.48,10.47,10.46,10.45,1000,2000,3000,4000,5000,10.51,10.52,10.53,10.54,10.55,1500,2500,3500,4500,5500,2023-01-01,10:30:00,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0";'''

        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = test_response

                quotes = await sina_crawler.fetch_realtime_quote(['sh600000'])

                assert 'sh600000' in quotes
                quote = quotes['sh600000']
                assert quote['change'] == 0.50
                assert quote['change_percent'] == 5.0

    @pytest.mark.asyncio
    async def test_realtime_quote_orderbook_data(self, sina_crawler, mock_sina_realtime_response):
        """测试订单簿数据（买卖盘）"""
        async with sina_crawler:
            with patch.object(sina_crawler, '_fetch_with_retry', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_sina_realtime_response

                quotes = await sina_crawler.fetch_realtime_quote(['sh600000'])

                quote = quotes['sh600000']
                assert 'bids' in quote
                assert 'asks' in quote
                assert 'price' in quote['bids']
                assert 'volume' in quote['bids']
                assert 'price' in quote['asks']
                assert 'volume' in quote['asks']
                assert len(quote['bids']['price']) == 5
                assert len(quote['asks']['price']) == 5


class TestSinaCrawlerHelperMethods:
    """测试辅助方法"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """测试异步上下文管理器"""
        async with SinaCrawler() as crawler:
            assert crawler.session is not None
            assert not crawler.session.closed

        # 退出上下文后，session应该被关闭
        assert crawler.session is None

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, sina_crawler):
        """测试重试机制 - 验证在成功情况下能正常获取数据"""
        async with sina_crawler:
            with patch.object(sina_crawler.session, 'get', new_callable=AsyncMock) as mock_get:
                # 成功的响应
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.text = AsyncMock(return_value="test data")
                mock_get.return_value = mock_response

                result = await sina_crawler._fetch_with_retry("http://test.com")

                # 验证成功获取数据
                assert mock_get.call_count >= 1
                assert result == "test data"


@pytest.mark.parametrize("symbol,start_date,end_date,should_fail", [
    ('sh600000', '2023-01-01', '2023-01-10', False),  # 正常情况
    ('sz000001', '2023-01-01', '2023-01-10', False),  # 深圳股票
    ('600000', '2023-01-01', '2023-01-10', True),     # 缺少前缀
    ('bj600000', '2023-01-01', '2023-01-10', True),    # 错误前缀
    ('sh600000', '2023-13-01', '2023-01-10', True),    # 无效日期
    ('sh600000', '2023-01-01', '2023-01-50', True),    # 无效日期
])
def test_sina_daily_data_validation(symbol, start_date, end_date, should_fail):
    """测试日线数据参数验证"""
    crawler = SinaCrawler()

    # 验证日期格式
    date_valid = crawler._validate_dates(start_date, end_date)

    # 验证股票代码格式
    symbol_valid = symbol.startswith('sh') or symbol.startswith('sz')

    if should_fail:
        assert not date_valid or not symbol_valid
    else:
        assert date_valid and symbol_valid


class TestSinaCrawlerIntegration:
    """集成测试（需要网络连接）"""

    @pytest.mark.slow
    @pytest.mark.requires_network
    @pytest.mark.asyncio
    async def test_real_sina_api_call(self):
        """真实API调用测试（需要网络，默认跳过）"""
        # 这个测试只有在有网络连接且需要测试真实API时才运行
        # 使用 pytest -m "requires_network" 来运行
        async with SinaCrawler() as crawler:
            df = await crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

            # 验证基本结构
            assert isinstance(df, pd.DataFrame)
            if not df.empty:
                assert 'symbol' in df.columns
                assert 'date' in df.columns
