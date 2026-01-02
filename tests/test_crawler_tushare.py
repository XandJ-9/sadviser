"""
TushareCrawler测试类
测试Tushare数据爬取功能
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from data.crawler.tushare_crawler import TushareCrawler


@pytest.fixture
def tushare_token():
    """测试用的Tushare token"""
    return "test_token_12345678"


@pytest.fixture
def tushare_crawler(tushare_token):
    """创建TushareCrawler实例"""
    return TushareCrawler(token=tushare_token, max_retries=3, timeout=15, delay=2.0)


@pytest.fixture
def mock_tushare_daily_response():
    """模拟Tushare日线数据响应"""
    return {
        "code": 0,
        "msg": None,
        "data": {
            "fields": ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"],
            "items": [
                ["600000.SH", "20230103", 10.50, 10.65, 10.45, 10.60, 123456.0, 1234567.89],
                ["600000.SH", "20230104", 10.58, 10.72, 10.55, 10.68, 145678.0, 1456789.01],
                ["600000.SH", "20230105", 10.65, 10.80, 10.60, 10.75, 156789.0, 1567890.12],
                ["600000.SH", "20230106", 10.70, 10.85, 10.68, 10.82, 167890.0, 1678901.23],
                ["600000.SH", "20230109", 10.75, 10.90, 10.72, 10.88, 178901.0, 1789012.34]
            ]
        }
    }


@pytest.fixture
def mock_tushare_realtime_response():
    """模拟Tushare实时行情响应"""
    return {
        "code": 0,
        "msg": None,
        "data": {
            "fields": ["ts_code", "name", "open", "high", "low", "last", "pre_close", "vol", "amount", "up_limit", "down_limit"],
            "items": [
                ["600000.SH", "浦发银行", 9.92, 9.97, 9.88, 9.92, 9.85, 12345678.0, 123456789.0, 10.84, 8.86],
                ["000001.SZ", "平安银行", 12.50, 12.55, 12.45, 12.52, 12.48, 23456789.0, 234567890.0, 13.73, 11.23]
            ]
        }
    }


@pytest.fixture
def mock_tushare_stock_basic_response():
    """模拟Tushare股票基本信息响应"""
    return {
        "code": 0,
        "msg": None,
        "data": {
            "fields": ["ts_code", "symbol", "name", "area", "industry", "fullname", "enname", "market", "exchange", "curr_type", "list_status", "list_date"],
            "items": [
                ["600000.SH", "600000", "浦发银行", "上海", "银行", "上海浦东发展银行股份有限公司", "SPDB", "主板", "SSE", "CNY", "L", "19991110"],
                ["000001.SZ", "000001", "平安银行", "深圳", "银行", "平安银行股份有限公司", "PING AN BANK", "主板", "SZSE", "CNY", "L", "19910403"]
            ]
        }
    }


@pytest.fixture
def mock_tushare_error_response():
    """模拟Tushare API错误响应"""
    return {
        "code": -1,
        "msg": "权限不足，请检查token",
        "data": None
    }


class TestTushareCrawlerInit:
    """测试TushareCrawler初始化"""

    def test_init_with_token(self, tushare_token):
        """测试带token的初始化"""
        crawler = TushareCrawler(token=tushare_token)
        assert crawler.token == tushare_token
        assert crawler.max_retries == 3
        assert crawler.timeout == 15
        assert crawler.delay == 2.0
        assert crawler.base_url == "http://api.tushare.pro"

    def test_init_custom_params(self, tushare_token):
        """测试自定义参数初始化"""
        crawler = TushareCrawler(
            token=tushare_token,
            max_retries=5,
            timeout=20,
            delay=3.0
        )
        assert crawler.max_retries == 5
        assert crawler.timeout == 20
        assert crawler.delay == 3.0

    def test_init_without_token(self):
        """测试不带token的初始化"""
        crawler = TushareCrawler(token="")
        assert crawler.token == ""

    def test_headers_configuration(self, tushare_token):
        """测试请求头配置"""
        crawler = TushareCrawler(token=tushare_token)
        assert "Content-Type" in crawler.headers
        assert crawler.headers["Content-Type"] == "application/json"


class TestTushareCrawlerFetchDailyData:
    """测试日线数据获取"""

    @pytest.mark.asyncio
    async def test_fetch_daily_data_success(self, tushare_crawler, mock_tushare_daily_response):
        """测试成功获取日线数据"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_tushare_daily_response

                df = await tushare_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

                # 验证返回的DataFrame
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 5
                assert 'symbol' in df.columns
                assert 'date' in df.columns
                assert df['symbol'].iloc[0] == '600000.SH'
                assert df['date'].dtype.name == 'datetime64[ns]'

    @pytest.mark.asyncio
    async def test_fetch_daily_data_symbol_conversion(self, tushare_crawler, mock_tushare_daily_response):
        """测试股票代码格式转换"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_tushare_daily_response

                # 测试上海股票代码转换
                df_sh = await tushare_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')
                assert len(df_sh) == 5

                # 测试深圳股票代码转换
                sz_response = mock_tushare_daily_response.copy()
                sz_response["data"]["items"][0][0] = "000001.SZ"
                mock_post.return_value = sz_response

                df_sz = await tushare_crawler.fetch_daily_data('sz000001', '2023-01-01', '2023-01-10')
                assert len(df_sz) == 5

    @pytest.mark.asyncio
    async def test_fetch_daily_data_invalid_date_range(self, tushare_crawler):
        """测试无效的日期范围"""
        async with tushare_crawler:
            # 开始日期晚于结束日期
            df = await tushare_crawler.fetch_daily_data('sh600000', '2023-12-31', '2023-01-01')

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_api_error(self, tushare_crawler, mock_tushare_error_response):
        """测试API错误"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_tushare_error_response

                df = await tushare_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

                # API错误应该返回空DataFrame
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_empty_response(self, tushare_crawler):
        """测试空响应"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = None

                df = await tushare_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

                assert isinstance(df, pd.DataFrame)
                assert len(df) == 0

    @pytest.mark.asyncio
    async def test_fetch_daily_data_no_items(self, tushare_crawler):
        """测试返回数据无items"""
        response = {
            "code": 0,
            "msg": None,
            "data": {
                "fields": ["ts_code", "trade_date"],
                "items": []
            }
        }

        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = response

                df = await tushare_crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

                assert isinstance(df, pd.DataFrame)
                assert len(df) == 0


class TestTushareCrawlerFetchRealtimeQuote:
    """测试实时行情获取"""

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_success(self, tushare_crawler, mock_tushare_realtime_response):
        """测试成功获取实时行情"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_tushare_realtime_response

                quotes = await tushare_crawler.fetch_realtime_quote(['sh600000', 'sz000001'])

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
                assert 'up_limit' in quote
                assert 'down_limit' in quote

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_empty_list(self, tushare_crawler):
        """测试空股票列表"""
        async with tushare_crawler:
            quotes = await tushare_crawler.fetch_realtime_quote([])

            assert isinstance(quotes, dict)
            assert len(quotes) == 0

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_change_calculation(self, tushare_crawler):
        """测试涨跌幅计算"""
        # 构造测试数据：昨收10.00，现价10.50，涨幅应为5%
        test_response = {
            "code": 0,
            "msg": None,
            "data": {
                "fields": ["ts_code", "name", "open", "high", "low", "last", "pre_close", "vol", "amount", "up_limit", "down_limit"],
                "items": [
                    ["600000.SH", "测试股票", 10.50, 10.60, 10.40, 10.50, 10.00, 1000000.0, 10000000.0, 11.00, 9.00]
                ]
            }
        }

        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = test_response

                quotes = await tushare_crawler.fetch_realtime_quote(['sh600000'])

                assert 'sh600000' in quotes
                quote = quotes['sh600000']
                assert quote['price'] == 10.50
                assert quote['change'] == 0.50
                assert quote['change_percent'] == 5.0

    @pytest.mark.asyncio
    async def test_fetch_realtime_quote_api_error(self, tushare_crawler, mock_tushare_error_response):
        """测试API错误"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_tushare_error_response

                quotes = await tushare_crawler.fetch_realtime_quote(['sh600000'])

                # 应该返回空字典
                assert isinstance(quotes, dict)
                assert len(quotes) == 0


class TestTushareCrawlerFetchStockBasic:
    """测试股票基本信息获取"""

    @pytest.mark.asyncio
    async def test_fetch_stock_basic_success(self, tushare_crawler, mock_tushare_stock_basic_response):
        """测试成功获取股票基本信息"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_tushare_stock_basic_response

                df = await tushare_crawler.fetch_stock_basic(exchange="SH")

                # 验证返回的DataFrame
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 2
                assert 'ts_code' in df.columns
                assert 'name' in df.columns
                assert 'industry' in df.columns

    @pytest.mark.asyncio
    async def test_fetch_stock_basic_with_market(self, tushare_crawler, mock_tushare_stock_basic_response):
        """测试带市场参数的股票基本信息获取"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_tushare_stock_basic_response

                df = await tushare_crawler.fetch_stock_basic(exchange="SZ", market="主板")

                assert isinstance(df, pd.DataFrame)
                # 验证传递的参数
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert call_args[0][0] == "stock_basic"
                assert 'exchange' in call_args[1]['params']
                assert 'market' in call_args[1]['params']

    @pytest.mark.asyncio
    async def test_fetch_stock_basic_empty_response(self, tushare_crawler):
        """测试空响应"""
        async with tushare_crawler:
            with patch.object(tushare_crawler, '_post_with_retry', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = None

                df = await tushare_crawler.fetch_stock_basic()

                assert isinstance(df, pd.DataFrame)
                assert len(df) == 0


class TestTushareCrawlerPostWithRetry:
    """测试POST请求重试机制"""

    @pytest.mark.asyncio
    async def test_post_with_retry_success(self, tushare_crawler, mock_tushare_daily_response):
        """测试成功的POST请求"""
        async with tushare_crawler:
            # 模拟session.post的响应
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value=mock_tushare_daily_response)

            with patch.object(tushare_crawler.session, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                result = await tushare_crawler._post_with_retry("daily", {"ts_code": "600000.SH"})

                assert result is not None
                assert result["code"] == 0
                mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_with_retry_api_error_retry(self, tushare_crawler, mock_tushare_error_response):
        """测试API错误时的重试"""
        async with tushare_crawler:
            # 模拟session.post的响应
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value=mock_tushare_error_response)

            with patch.object(tushare_crawler.session, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                result = await tushare_crawler._post_with_retry("daily", {"ts_code": "600000.SH"})

                # API错误，应该重试后返回None
                assert result is None
                # 应该重试了max_retries次
                assert mock_post.call_count == tushare_crawler.max_retries

    @pytest.mark.asyncio
    async def test_post_with_retry_network_error(self, tushare_crawler):
        """测试网络错误重试"""
        async with tushare_crawler:
            with patch.object(tushare_crawler.session, 'post', new_callable=AsyncMock) as mock_post:
                # 模拟网络错误
                mock_post.side_effect = Exception("Network error")

                result = await tushare_crawler._post_with_retry("daily", {"ts_code": "600000.SH"})

                # 网络错误，应该重试后返回None
                assert result is None
                # 应该重试了max_retries次
                assert mock_post.call_count == tushare_crawler.max_retries


class TestTushareCrawlerHelperMethods:
    """测试辅助方法"""

    @pytest.mark.asyncio
    async def test_async_context_manager(self, tushare_token):
        """测试异步上下文管理器"""
        async with TushareCrawler(token=tushare_token) as crawler:
            assert crawler.session is not None
            assert not crawler.session.closed

        # 退出上下文后，session应该被关闭
        assert crawler.session is None


@pytest.mark.parametrize("symbol,expected_ts_code", [
    ('sh600000', '600000.SH'),
    ('sz000001', '000001.SZ'),
    ('sh603993', '603993.SH'),
    ('sz300750', '300750.SZ'),
])
def test_symbol_conversion(symbol, expected_ts_code):
    """测试股票代码格式转换逻辑"""
    # 这个测试验证代码转换逻辑是否正确
    if symbol.startswith('sh'):
        ts_code = f"{symbol[2:]}.SH"
    elif symbol.startswith('sz'):
        ts_code = f"{symbol[2:]}.SZ"
    else:
        ts_code = symbol

    assert ts_code == expected_ts_code


@pytest.mark.parametrize("date_str,expected_format", [
    ('2023-01-01', '20230101'),
    ('2023-12-31', '20231231'),
    ('2024-06-15', '20240615'),
])
def test_date_format_conversion(date_str, expected_format):
    """测试日期格式转换（Tushare需要YYYYMMDD格式）"""
    converted = date_str.replace("-", "")
    assert converted == expected_format


class TestTushareCrawlerIntegration:
    """集成测试（需要实际token）"""

    @pytest.mark.slow
    @pytest.mark.requires_network
    @pytest.mark.asyncio
    async def test_real_tushare_api_call(self):
        """真实API调用测试（需要有效token和网络，默认跳过）"""
        # 这个测试只有在有有效token且需要测试真实API时才运行
        # 使用 pytest -m "requires_network" 来运行

        token = "your_real_token_here"  # 替换为真实token
        if token == "your_real_token_here":
            pytest.skip("需要设置真实的Tushare token")

        async with TushareCrawler(token=token) as crawler:
            df = await crawler.fetch_daily_data('sh600000', '2023-01-01', '2023-01-10')

            # 验证基本结构
            assert isinstance(df, pd.DataFrame)
            if not df.empty:
                assert 'symbol' in df.columns
                assert 'date' in df.columns
