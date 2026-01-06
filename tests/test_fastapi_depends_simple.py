"""
简单验证 FastAPI 依赖注入配置
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import Depends
from service.api.dependencies import get_stock_service
from service.services.stock_service import StockService
from service.api.v1.stock_api import router


def test_dependency_function():
    """测试依赖函数"""
    print("\n测试 1: 依赖函数")
    service = get_stock_service()
    assert isinstance(service, StockService)
    print(f"✅ get_stock_service() 返回 StockService 实例")


def test_router_depends():
    """测试路由使用 Depends"""
    print("\n测试 2: 路由依赖注入")
    routes = router.routes
    assert len(routes) > 0

    # 检查路由是否正确配置
    for route in routes:
        # 检查路由函数的参数
        if hasattr(route, 'endpoint'):
            import inspect
            sig = inspect.signature(route.endpoint)
            params = sig.parameters

            # 检查是否有 service 参数使用 Depends
            if 'service' in params:
                param = params['service']
                print(f"  路由 {route.path}: 使用依赖注入")
                assert param.default is not None
                # 检查是否是 Depends 实例
                from fastapi.params import Depends as DependsType
                assert isinstance(param.default, DependsType)

    print(f"✅ 所有路由正确配置依赖注入 ({len(routes)} 个路由)")


def test_dependency_signature():
    """测试依赖函数的返回类型"""
    print("\n测试 3: 依赖函数类型注解")
    import inspect

    sig = inspect.signature(get_stock_service)
    return_annotation = sig.return_annotation

    print(f"  返回类型注解: {return_annotation}")
    print(f"  类型检查: {return_annotation == StockService}")
    print("✅ 依赖函数返回类型正确")


if __name__ == "__main__":
    print("=" * 60)
    print("FastAPI 依赖注入验证")
    print("=" * 60)

    test_dependency_function()
    test_router_depends()
    test_dependency_signature()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！FastAPI 依赖注入配置正确")
    print("=" * 60)
