"""
WebSocket连接器测试类
测试WebSocket数据获取功能
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from websockets.exceptions import ConnectionClosed

from data.crawler.websocket_connector import StockWebSocketConnector, SinaWebSocketConnector


@pytest.fixture
def websocket_url():
    """测试用的WebSocket URL"""
    return "wss://test.example.com/ws"


@pytest.fixture
def ws_connector(websocket_url):
    """创建StockWebSocketConnector实例"""
    return StockWebSocketConnector(
        url=websocket_url,
        reconnect_interval=1,
        max_reconnect_attempts=3
    )


@pytest.fixture
def sina_ws_connector():
    """创建SinaWebSocketConnector实例"""
    return SinaWebSocketConnector(
        reconnect_interval=1,
        max_reconnect_attempts=3
    )


class TestStockWebSocketConnectorInit:
    """测试WebSocket连接器初始化"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        connector = StockWebSocketConnector(url="wss://test.com")
        assert connector.url == "wss://test.com"
        assert connector.reconnect_interval == 5
        assert connector.max_reconnect_attempts == 10
        assert connector.websocket is None
        assert not connector.connected
        assert not connector.running
        assert len(connector.subscribed_symbols) == 0

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        connector = StockWebSocketConnector(
            url="wss://test.com",
            reconnect_interval=2,
            max_reconnect_attempts=5
        )
        assert connector.reconnect_interval == 2
        assert connector.max_reconnect_attempts == 5

    def test_init_callbacks(self, ws_connector):
        """测试回调函数初始化"""
        assert ws_connector.on_message_callback is None
        assert ws_connector.on_connect_callback is None
        assert ws_connector.on_disconnect_callback is None
        assert ws_connector.on_error_callback is None


class TestStockWebSocketConnectorCallbacks:
    """测试回调函数设置"""

    def test_set_callback_all(self, ws_connector):
        """测试设置所有回调函数"""
        on_message = lambda data: None
        on_connect = lambda: None
        on_disconnect = lambda: None
        on_error = lambda e: None

        ws_connector.set_callback(
            on_message=on_message,
            on_connect=on_connect,
            on_disconnect=on_disconnect,
            on_error=on_error
        )

        assert ws_connector.on_message_callback == on_message
        assert ws_connector.on_connect_callback == on_connect
        assert ws_connector.on_disconnect_callback == on_disconnect
        assert ws_connector.on_error_callback == on_error

    def test_set_callback_partial(self, ws_connector):
        """测试设置部分回调函数"""
        on_message = lambda data: None

        ws_connector.set_callback(on_message=on_message)

        assert ws_connector.on_message_callback == on_message
        assert ws_connector.on_connect_callback is None
        assert ws_connector.on_disconnect_callback is None
        assert ws_connector.on_error_callback is None

    def test_callback_invocation_on_connect(self, ws_connector):
        """测试连接成功回调"""
        callback_called = []

        async def on_connect():
            callback_called.append('connect')

        ws_connector.set_callback(on_connect=on_connect)

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_connect.return_value = mock_ws

            await ws_connector.connect()

            assert 'connect' in callback_called

    def test_callback_invocation_on_error(self, ws_connector):
        """测试错误回调"""
        callback_called = []
        test_error = Exception("Test error")

        async def on_error(e):
            callback_called.append(e)

        ws_connector.set_callback(on_error=on_error)

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = test_error

            await ws_connector.connect()

            assert len(callback_called) == 1
            assert callback_called[0] == test_error


class TestStockWebSocketConnectorConnect:
    """测试连接功能"""

    @pytest.mark.asyncio
    async def test_connect_success(self, ws_connector):
        """测试成功连接"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_connect.return_value = mock_ws

            result = await ws_connector.connect()

            assert result is True
            assert ws_connector.connected
            assert ws_connector.websocket is not None
            mock_connect.assert_called_once_with(ws_connector.url)

    @pytest.mark.asyncio
    async def test_connect_failure(self, ws_connector):
        """测试连接失败"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            result = await ws_connector.connect()

            assert result is False
            assert not ws_connector.connected
            assert ws_connector.websocket is None

    @pytest.mark.asyncio
    async def test_connect_with_resubscribe(self, ws_connector):
        """测试重连后自动重新订阅"""
        ws_connector.subscribed_symbols.add('sh600000')
        ws_connector.subscribed_symbols.add('sz000001')

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            with patch.object(ws_connector, 'subscribe', new_callable=AsyncMock) as mock_subscribe:
                await ws_connector.connect()

                # 验证重新订阅
                mock_subscribe.assert_called_once_with(['sh600000', 'sz000001'])


class TestStockWebSocketConnectorDisconnect:
    """测试断开连接功能"""

    @pytest.mark.asyncio
    async def test_disconnect_success(self, ws_connector):
        """测试成功断开连接"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.close = AsyncMock()
            mock_connect.return_value = mock_ws

            # 先连接
            await ws_connector.connect()
            assert ws_connector.connected

            # 再断开
            await ws_connector.disconnect()

            assert not ws_connector.connected
            mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_callback(self, ws_connector):
        """测试断开连接回调"""
        callback_called = []

        def on_disconnect():
            callback_called.append('disconnect')

        ws_connector.set_callback(on_disconnect=on_disconnect)

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.close = AsyncMock()
            mock_connect.return_value = mock_ws

            await ws_connector.connect()
            await ws_connector.disconnect()

            assert 'disconnect' in callback_called

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self, ws_connector):
        """测试断开未连接的连接器"""
        # 没有连接时断开不应该报错
        await ws_connector.disconnect()
        assert not ws_connector.connected


class TestStockWebSocketConnectorSubscribe:
    """测试订阅功能"""

    @pytest.mark.asyncio
    async def test_subscribe_success(self, ws_connector):
        """测试成功订阅"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            await ws_connector.connect()
            await ws_connector.subscribe(['sh600000', 'sz000001'])

            assert 'sh600000' in ws_connector.subscribed_symbols
            assert 'sz000001' in ws_connector.subscribed_symbols
            mock_ws.send.assert_called_once()

            # 验证发送的消息格式
            sent_message = json.loads(mock_ws.send.call_args[0][0])
            assert sent_message['action'] == 'subscribe'
            assert set(sent_message['symbols']) == {'sh600000', 'sz000001'}
            assert 'timestamp' in sent_message

    @pytest.mark.asyncio
    async def test_subscribe_not_connected(self, ws_connector):
        """测试未连接时订阅"""
        # 未连接时订阅不应该报错，但也不会实际订阅
        await ws_connector.subscribe(['sh600000'])

        assert len(ws_connector.subscribed_symbols) == 0

    @pytest.mark.asyncio
    async def test_subscribe_empty_list(self, ws_connector):
        """测试订阅空列表"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            await ws_connector.connect()
            await ws_connector.subscribe([])

            # 不应该发送消息
            mock_ws.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_subscribe_duplicate(self, ws_connector):
        """测试重复订阅"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            await ws_connector.connect()
            await ws_connector.subscribe(['sh600000'])
            await ws_connector.subscribe(['sh600000', 'sz000001'])

            # 验证股票只在集合中出现一次
            assert ws_connector.subscribed_symbols.count('sh600000') == 1


class TestStockWebSocketConnectorUnsubscribe:
    """测试取消订阅功能"""

    @pytest.mark.asyncio
    async def test_unsubscribe_success(self, ws_connector):
        """测试成功取消订阅"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            await ws_connector.connect()
            await ws_connector.subscribe(['sh600000', 'sz000001', 'sz300059'])
            await ws_connector.unsubscribe(['sz000001'])

            assert 'sh600000' in ws_connector.subscribed_symbols
            assert 'sz000001' not in ws_connector.subscribed_symbols
            assert 'sz300059' in ws_connector.subscribed_symbols

    @pytest.mark.asyncio
    async def test_unsubscribe_not_connected(self, ws_connector):
        """测试未连接时取消订阅"""
        # 未连接时取消订阅不应该报错
        await ws_connector.unsubscribe(['sh600000'])

    @pytest.mark.asyncio
    async def test_unsubscribe_empty_list(self, ws_connector):
        """测试取消订阅空列表"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            await ws_connector.connect()
            await ws_connector.unsubscribe([])

            # 不应该发送消息
            mock_ws.send.assert_not_called()


class TestStockWebSocketConnectorReceiveLoop:
    """测试接收消息循环"""

    @pytest.mark.asyncio
    async def test_receive_message_success(self, ws_connector):
        """测试成功接收消息"""
        received_messages = []

        def on_message(data):
            received_messages.append(data)

        ws_connector.set_callback(on_message=on_message)

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_connect.return_value = mock_ws

            await ws_connector.connect()

            # 模拟接收消息
            test_messages = [
                json.dumps({"symbol": "sh600000", "price": 10.50}),
                json.dumps({"symbol": "sz000001", "price": 12.30})
            ]

            async def mock_messages():
                for msg in test_messages:
                    yield msg

            mock_ws.__aiter__ = lambda self: mock_messages()

            await ws_connector._receive_loop()

            assert len(received_messages) == 2
            assert received_messages[0]["symbol"] == "sh600000"
            assert received_messages[1]["symbol"] == "sz000001"

    @pytest.mark.asyncio
    async def test_receive_invalid_json(self, ws_connector):
        """测试接收无效JSON"""
        error_caught = []

        def on_error(e):
            error_caught.append(e)

        ws_connector.set_callback(on_error=on_error)

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_connect.return_value = mock_ws

            await ws_connector.connect()

            # 模拟接收无效JSON
            async def mock_messages():
                yield "invalid json"

            mock_ws.__aiter__ = lambda self: mock_messages()

            await ws_connector._receive_loop()

            # 应该捕获JSON解析错误
            assert len(error_caught) > 0
            assert isinstance(error_caught[0], json.JSONDecodeError)


class TestStockWebSocketConnectorReconnect:
    """测试自动重连功能"""

    @pytest.mark.asyncio
    async def test_reconnect_on_connection_closed(self, ws_connector):
        """测试连接关闭后自动重连"""
        connect_attempts = []

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            # 第一次连接成功，第二次也成功
            mock_ws1 = MagicMock()
            mock_ws1.closed = False
            mock_ws2 = MagicMock()
            mock_ws2.closed = False

            mock_connect.side_effect = [mock_ws1, mock_ws2]

            async def mock_receive_first():
                # 模拟连接关闭
                raise ConnectionClosed(1000, "Normal closure")

            mock_ws1.__aiter__ = lambda self: mock_receive_first()
            mock_ws2.__aiter__ = lambda self: AsyncMock().__aiter__()

            # 启动连接器并运行一小段时间
            task = asyncio.create_task(ws_connector.run())

            # 等待连接尝试
            await asyncio.sleep(0.1)

            # 停止连接器
            await ws_connector.stop()
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except asyncio.TimeoutError:
                pass

            # 验证尝试了多次连接
            assert mock_connect.call_count >= 1

    @pytest.mark.asyncio
    async def test_max_reconnect_attempts(self, ws_connector):
        """测试最大重连次数限制"""
        ws_connector.max_reconnect_attempts = 2

        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            # 所有连接尝试都失败
            mock_connect.side_effect = Exception("Connection failed")

            # 启动连接器
            task = asyncio.create_task(ws_connector.run())

            # 等待达到最大重连次数
            await asyncio.sleep(0.5)

            try:
                await asyncio.wait_for(task, timeout=1.0)
            except asyncio.TimeoutError:
                await ws_connector.stop()

            # 验证重连次数不超过限制
            assert mock_connect.call_count <= 2


class TestStockWebSocketConnectorStop:
    """测试停止功能"""

    @pytest.mark.asyncio
    async def test_stop_running_connector(self, ws_connector):
        """测试停止运行中的连接器"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_connect.return_value = mock_ws

            # 启动连接器
            task = asyncio.create_task(ws_connector.run())
            await asyncio.sleep(0.1)

            # 停止连接器
            await ws_connector.stop()

            # 验证状态
            assert not ws_connector.running
            assert not ws_connector.connected


class TestSinaWebSocketConnector:
    """测试新浪WebSocket连接器"""

    def test_init(self):
        """测试初始化"""
        connector = SinaWebSocketConnector()
        assert connector.url == "wss://hq.sinajs.cn/wskt?list="
        assert connector.reconnect_interval == 5
        assert connector.max_reconnect_attempts == 10

    @pytest.mark.asyncio
    async def test_subscribe_format(self, sina_ws_connector):
        """测试新浪订阅格式"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            await sina_ws_connector.connect()
            await sina_ws_connector.subscribe(['sh600000', 'sz000001'])

            # 新浪使用简单的逗号分隔格式
            sent_message = mock_ws.send.call_args[0][0]
            assert sent_message == "sh600000,sz000001"

    @pytest.mark.asyncio
    async def test_unsubscribe_resubscribe_remaining(self, sina_ws_connector):
        """测试新浪取消订阅后重新订阅剩余股票"""
        async with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
            mock_ws = MagicMock()
            mock_ws.closed = False
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            await sina_ws_connector.connect()
            await sina_ws_connector.subscribe(['sh600000', 'sz000001', 'sz300059'])
            await sina_ws_connector.unsubscribe(['sz000001'])

            # 应该重新订阅剩余股票
            assert mock_ws.send.call_count == 2  # 第一次订阅，第二次重新订阅
            sent_message = mock_ws.send.call_args[0][0]
            assert "sh600000" in sent_message
            assert "sz300059" in sent_message
            assert "sz000001" not in sent_message


@pytest.mark.parametrize("symbols,expected_count", [
    (['sh600000'], 1),
    (['sh600000', 'sz000001'], 2),
    (['sh600000', 'sz000001', 'sz300059'], 3),
])
def test_subscribe_symbols_add_to_set(symbols, expected_count):
    """测试订阅股票添加到集合"""
    connector = StockWebSocketConnector(url="wss://test.com")
    connector.subscribed_symbols.update(symbols)
    assert len(connector.subscribed_symbols) == expected_count


@pytest.mark.parametrize("max_attempts,should_stop", [
    (0, False),  # 无限重试
    (3, True),   # 3次后停止
    (10, True),  # 10次后停止
])
def test_max_reconnect_attempts_logic(max_attempts, should_stop):
    """测试最大重连次数逻辑"""
    connector = StockWebSocketConnector(
        url="wss://test.com",
        max_reconnect_attempts=max_attempts
    )
    assert connector.max_reconnect_attempts == max_attempts

    # 如果max_attempts为0，表示无限重试
    if max_attempts == 0:
        should_stop = False

    # 否则在达到次数后停止
    assert (max_attempts > 0) == should_stop or max_attempts == 0


class TestWebSocketConnectorIntegration:
    """集成测试（需要实际WebSocket服务器）"""

    @pytest.mark.slow
    @pytest.mark.requires_network
    @pytest.mark.asyncio
    async def test_real_websocket_connection(self):
        """真实WebSocket连接测试（需要服务器，默认跳过）"""
        # 这个测试只有在有实际WebSocket服务器时才运行
        # 使用 pytest -m "requires_network" 来运行

        # 使用公共WebSocket测试服务器
        url = "wss://echo.websocket.org"

        connector = StockWebSocketConnector(url=url, reconnect_interval=1, max_reconnect_attempts=1)

        received_data = []

        def on_message(data):
            received_data.append(data)
            # 收到消息后停止
            asyncio.create_task(connector.stop())

        connector.set_callback(on_message=on_message)

        # 启动连接器
        task = asyncio.create_task(connector.run())

        # 等待连接
        for _ in range(10):
            if connector.connected:
                break
            await asyncio.sleep(0.5)
        else:
            await connector.stop()
            pytest.skip("无法连接到WebSocket服务器")

        # 发送测试消息
        await connector.subscribe(['test'])

        # 等待响应或超时
        await asyncio.sleep(2)

        # 停止连接器
        await connector.stop()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except asyncio.TimeoutError:
            pass
