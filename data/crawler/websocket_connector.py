import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable

import websockets
from websockets import WebSocketClientProtocol

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockWebSocketConnector:
    """股票实时行情WebSocket连接器，用于获取高频实时数据"""
    
    def __init__(self, 
                 url: str, 
                 reconnect_interval: int = 5,
                 max_reconnect_attempts: int = 10):
        """
        初始化WebSocket连接器
        
        :param url: WebSocket服务器URL
        :param reconnect_interval: 重连间隔时间(秒)
        :param max_reconnect_attempts: 最大重连尝试次数，0表示无限重试
        """
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self.running = False
        self.subscribed_symbols = set()
        
        # 回调函数
        self.on_message_callback: Optional[Callable[[Dict], None]] = None
        self.on_connect_callback: Optional[Callable[[], None]] = None
        self.on_disconnect_callback: Optional[Callable[[], None]] = None
        self.on_error_callback: Optional[Callable[[Exception], None]] = None
    
    def set_callback(self, 
                    on_message: Optional[Callable[[Dict], None]] = None,
                    on_connect: Optional[Callable[[], None]] = None,
                    on_disconnect: Optional[Callable[[], None]] = None,
                    on_error: Optional[Callable[[Exception], None]] = None):
        """
        设置回调函数
        
        :param on_message: 收到消息时的回调
        :param on_connect: 连接成功时的回调
        :param on_disconnect: 断开连接时的回调
        :param on_error: 发生错误时的回调
        """
        if on_message:
            self.on_message_callback = on_message
        if on_connect:
            self.on_connect_callback = on_connect
        if on_disconnect:
            self.on_disconnect_callback = on_disconnect
        if on_error:
            self.on_error_callback = on_error
    
    async def connect(self) -> bool:
        """
        连接到WebSocket服务器
        
        :return: 连接成功返回True，否则返回False
        """
        try:
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            logger.info(f"成功连接到WebSocket服务器: {self.url}")
            
            # 触发连接成功回调
            if self.on_connect_callback:
                self.on_connect_callback()
            
            # 如果之前有订阅的股票，重新订阅
            if self.subscribed_symbols:
                await self.subscribe(list(self.subscribed_symbols))
                
            return True
            
        except Exception as e:
            logger.error(f"连接WebSocket服务器失败: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(e)
            return False
    
    async def disconnect(self):
        """断开与WebSocket服务器的连接"""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"关闭WebSocket连接时发生错误: {str(e)}")
            
        self.connected = False
        logger.info(f"已断开与WebSocket服务器的连接: {self.url}")
        
        # 触发断开连接回调
        if self.on_disconnect_callback:
            self.on_disconnect_callback()
    
    async def subscribe(self, symbols: List[str]):
        """
        订阅股票实时行情
        
        :param symbols: 股票代码列表
        """
        if not self.connected or not self.websocket:
            logger.warning("未连接到WebSocket服务器，无法订阅行情")
            return
        
        if not symbols:
            return
        
        try:
            # 构建订阅消息，这里假设服务器接受特定格式的订阅消息
            # 实际格式需要根据WebSocket服务器的要求进行调整
            subscribe_msg = {
                "action": "subscribe",
                "symbols": symbols,
                "timestamp": int(time.time() * 1000)
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            self.subscribed_symbols.update(symbols)
            logger.info(f"已订阅股票: {', '.join(symbols)}")
            
        except Exception as e:
            logger.error(f"订阅股票行情失败: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    async def unsubscribe(self, symbols: List[str]):
        """
        取消订阅股票实时行情
        
        :param symbols: 股票代码列表
        """
        if not self.connected or not self.websocket:
            logger.warning("未连接到WebSocket服务器，无法取消订阅")
            return
        
        if not symbols:
            return
        
        try:
            # 构建取消订阅消息
            unsubscribe_msg = {
                "action": "unsubscribe",
                "symbols": symbols,
                "timestamp": int(time.time() * 1000)
            }
            
            await self.websocket.send(json.dumps(unsubscribe_msg))
            
            # 更新已订阅股票集合
            for symbol in symbols:
                if symbol in self.subscribed_symbols:
                    self.subscribed_symbols.remove(symbol)
            
            logger.info(f"已取消订阅股票: {', '.join(symbols)}")
            
        except Exception as e:
            logger.error(f"取消订阅股票行情失败: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    async def _receive_loop(self):
        """接收消息的循环"""
        assert self.websocket is not None, "WebSocket连接未初始化"
        
        try:
            async for message in self.websocket:
                try:
                    # 解析JSON消息
                    data = json.loads(message)
                    
                    # 触发消息回调
                    if self.on_message_callback:
                        self.on_message_callback(data)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"解析WebSocket消息失败: {str(e)}, 消息: {message}")
                    if self.on_error_callback:
                        self.on_error_callback(e)
                        
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket连接已关闭: {str(e)}")
            self.connected = False
            if self.on_disconnect_callback:
                self.on_disconnect_callback()
                
        except Exception as e:
            logger.error(f"接收WebSocket消息时发生错误: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(e)
            self.connected = False
            if self.on_disconnect_callback:
                self.on_disconnect_callback()
    
    async def run(self):
        """运行WebSocket客户端，包括自动重连逻辑"""
        self.running = True
        reconnect_attempts = 0
        
        while self.running:
            # 尝试连接
            if not self.connected:
                if self.max_reconnect_attempts > 0 and reconnect_attempts >= self.max_reconnect_attempts:
                    logger.error(f"达到最大重连次数 ({self.max_reconnect_attempts})，停止尝试")
                    break
                
                if reconnect_attempts > 0:
                    logger.info(f"尝试重连 ({reconnect_attempts}/{self.max_reconnect_attempts if self.max_reconnect_attempts > 0 else '无限'})...")
                    await asyncio.sleep(self.reconnect_interval)
                
                # 连接服务器
                if await self.connect():
                    reconnect_attempts = 0  # 重置重连计数器
                else:
                    reconnect_attempts += 1
                    continue
            
            # 接收消息
            await self._receive_loop()
            
            # 如果退出接收循环且仍在运行，则表示连接断开，需要重连
            if self.running:
                reconnect_attempts += 1
        
        logger.info("WebSocket客户端已停止")
    
    async def stop(self):
        """停止WebSocket客户端"""
        self.running = False
        if self.connected:
            await self.disconnect()


# 示例实现：新浪财经WebSocket连接器
class SinaWebSocketConnector(StockWebSocketConnector):
    """新浪财经WebSocket连接器，获取A股实时行情"""
    
    def __init__(self, reconnect_interval: int = 5, max_reconnect_attempts: int = 10):
        """初始化新浪财经WebSocket连接器"""
        # 新浪财经WebSocket服务器地址
        url = "wss://hq.sinajs.cn/wskt?list="
        super().__init__(url, reconnect_interval, max_reconnect_attempts)
    
    async def subscribe(self, symbols: List[str]):
        """
        订阅股票实时行情，适配新浪财经WebSocket格式
        
        :param symbols: 股票代码列表，如['sh600000', 'sz000001']
        """
        if not self.connected or not self.websocket:
            logger.warning("未连接到WebSocket服务器，无法订阅行情")
            return
        
        if not symbols:
            return
        
        try:
            # 新浪财经WebSocket使用简单的订阅格式：每个股票代码用逗号分隔
            subscribe_str = ",".join(symbols)
            await self.websocket.send(subscribe_str)
            
            self.subscribed_symbols.update(symbols)
            logger.info(f"已订阅新浪财经股票: {', '.join(symbols)}")
            
        except Exception as e:
            logger.error(f"订阅新浪财经股票行情失败: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(e)
    
    async def unsubscribe(self, symbols: List[str]):
        """
        取消订阅股票实时行情，新浪财经WebSocket不直接支持取消订阅，
        这里通过重新订阅剩余股票的方式实现
        
        :param symbols: 股票代码列表
        """
        if not self.connected or not self.websocket:
            logger.warning("未连接到WebSocket服务器，无法取消订阅")
            return
        
        if not symbols:
            return
        
        # 从已订阅集合中移除
        remaining_symbols = []
        for symbol in self.subscribed_symbols:
            if symbol not in symbols:
                remaining_symbols.append(symbol)
        
        # 更新已订阅集合
        self.subscribed_symbols = set(remaining_symbols)
        
        if remaining_symbols:
            # 重新订阅剩余股票
            try:
                subscribe_str = ",".join(remaining_symbols)
                await self.websocket.send(subscribe_str)
                logger.info(f"已取消订阅股票: {', '.join(symbols)}，剩余订阅: {', '.join(remaining_symbols)}")
            except Exception as e:
                logger.error(f"重新订阅剩余股票失败: {str(e)}")
                if self.on_error_callback:
                    self.on_error_callback(e)
        else:
            # 如果没有剩余股票，发送空消息（实际上不会取消所有订阅）
            # 新浪财经WebSocket不支持完全取消订阅，需要断开连接
            logger.info(f"已取消所有订阅，将断开连接")
            await self.disconnect()


# 测试WebSocket连接器
async def test_websocket_connector():
    """测试股票WebSocket连接器"""
    def on_message(data):
        """消息回调函数"""
        print(f"收到消息: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    def on_connect():
        """连接成功回调函数"""
        print("WebSocket连接成功")
    
    def on_disconnect():
        """断开连接回调函数"""
        print("WebSocket连接断开")
    
    def on_error(e):
        """错误回调函数"""
        print(f"发生错误: {str(e)}")
    
    # 创建并配置连接器
    connector = SinaWebSocketConnector()
    connector.set_callback(
        on_message=on_message,
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        on_error=on_error
    )
    
    # 启动连接器
    connector_task = asyncio.create_task(connector.run())
    
    # 等待连接成功
    while not connector.connected:
        await asyncio.sleep(1)
    
    # 订阅股票
    await connector.subscribe(['sh600000', 'sz000001', 'sz300059'])
    
    # 运行10秒
    await asyncio.sleep(10)
    
    # 取消订阅部分股票
    await connector.unsubscribe(['sz300059'])
    
    # 再运行10秒
    await asyncio.sleep(10)
    
    # 停止连接器
    await connector.stop()
    await connector_task

if __name__ == "__main__":
    asyncio.run(test_websocket_connector())
