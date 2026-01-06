"""
测试 FastAPI 依赖注入
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from service.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_dependency_injection_stocks(client):
    """测试股票列表接口的依赖注入"""
    print("\n测试 1: 股票列表接口")
    response = client.get("/api/v1/stocks/?limit=5&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    assert "total" in data
    print(f"✅ 获取股票列表成功: {len(data['stocks'])} 只")


def test_dependency_injection_stock_detail(client):
    """测试股票详情接口的依赖注入"""
    print("\n测试 2: 股票详情接口")
    response = client.get("/api/v1/stocks/000001")

    assert response.status_code == 200
    data = response.json()
    assert "symbol" in data
    assert "name" in data
    print(f"✅ 获取股票详情成功: {data['name']}")


def test_dependency_injection_market_overview(client):
    """测试市场概览接口的依赖注入"""
    print("\n测试 3: 市场概览接口")
    response = client.get("/api/v1/stocks/market/overview")

    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "total_volume" in data
    print(f"✅ 获取市场概览成功: {data['date']}")


def test_dependency_injection_hot_stocks(client):
    """测试热门股票接口的依赖注入"""
    print("\n测试 4: 热门股票接口")
    response = client.get("/api/v1/stocks/hot?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    print(f"✅ 获取热门股票成功: {len(data['stocks'])} 只")


def test_dependency_injection_search(client):
    """测试搜索接口的依赖注入"""
    print("\n测试 5: 搜索接口")
    response = client.get("/api/v1/stocks/search/000?limit=3")

    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    print(f"✅ 搜索股票成功: 找到 {data['count']} 只")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
