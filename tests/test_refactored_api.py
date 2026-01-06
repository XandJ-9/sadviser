"""
测试重构后的 API 架构
"""
import asyncio
import sys
import os
import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
async def container():
    """创建独立的容器实例用于测试"""
    from service.core.container import Container
    from service.repositories.stock_repository import StockRepository
    from service.services.stock_service import StockService

    class TestContainer:
        def __init__(self):
            from config.base import DATA_STORAGE
            from data.storage.postgres_storage import PostgreSQLStorage

            self._storage = PostgreSQLStorage(DATA_STORAGE["postgresql"])
            self._stock_repository = StockRepository(self._storage)
            self._stock_service = StockService(self._stock_repository)

        def get_stock_repository(self):
            return self._stock_repository

        def get_stock_service(self):
            return self._stock_service

        async def close(self):
            if self._storage and self._storage.connected:
                await self._storage.pool.close()

    test_container = TestContainer()
    yield test_container
    await test_container.close()


@pytest.mark.asyncio
async def test_container(container):
    """测试依赖注入容器"""
    print("=" * 60)
    print("测试 1: 依赖注入容器")
    print("=" * 60)

    # 测试单例模式
    repo1 = container.get_stock_repository()
    repo2 = container.get_stock_repository()
    assert repo1 is repo2, "Repository 应该是单例"
    print("✅ Repository 单例模式正常")

    service1 = container.get_stock_service()
    service2 = container.get_stock_service()
    assert service1 is service2, "Service 应该是单例"
    print("✅ Service 单例模式正常")

    print()


@pytest.mark.asyncio
async def test_repository(container):
    """测试 Repository 层"""
    print("=" * 60)
    print("测试 2: Repository 层")
    print("=" * 60)

    repo = container.get_stock_repository()

    # 测试连接
    await repo._ensure_connection()
    print("✅ 数据库连接成功")

    # 测试查询
    stocks = await repo.get_stock_list(limit=5)
    print(f"✅ 查询到 {len(stocks)} 只股票")
    if stocks:
        print(f"   示例: {stocks[0].get('symbol')} - {stocks[0].get('name')}")

    # 测试总数统计
    total = await repo.get_stock_list_count()
    print(f"✅ 股票总数: {total}")

    print()


@pytest.mark.asyncio
async def test_service(container):
    """测试 Service 层"""
    print("=" * 60)
    print("测试 3: Service 层")
    print("=" * 60)

    service = container.get_stock_service()

    # 测试获取股票列表
    result = await service.get_stock_list(limit=5)
    print(f"✅ 获取股票列表: {len(result.get('stocks', []))} 只")
    print(f"   总数: {result.get('total', 0)}")

    # 测试市场概览
    overview = await service.get_market_overview()
    print(f"✅ 市场概览日期: {overview.get('date')}")
    print(f"   总成交量: {overview.get('total_volume')}")
    print(f"   涨停数: {overview.get('limit_up')}")
    print(f"   跌停数: {overview.get('limit_down')}")

    # 测试搜索
    search_result = await service.search_stocks("000", limit=3)
    print(f"✅ 搜索 '000': 找到 {search_result.get('count', 0)} 只股票")

    # 测试热门股票
    hot_result = await service.get_hot_stocks(limit=5)
    print(f"✅ 热门股票: {hot_result.get('count', 0)} 只")

    print()


@pytest.mark.asyncio
async def test_api_endpoints():
    """测试 API 端点"""
    print("=" * 60)
    print("测试 4: API 端点")
    print("=" * 60)

    from service.api.v1.stock_api import router

    print(f"✅ 路由前缀: {router.prefix}")
    print(f"✅ 路由数量: {len(router.routes)}")

    print("\n所有路由:")
    for i, route in enumerate(router.routes, 1):
        methods = list(route.methods) if hasattr(route, 'methods') else []
        print(f"  {i}. {methods} {route.path}")

    print()
