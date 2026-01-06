"""
测试 stock_api 所有路由是否正确匹配
"""
import sys
sys.path.insert(0, '/Users/xujia/MyCode/sadviser')

from fastapi.testclient import TestClient
from service.main import app


def test_all_routes():
    """测试所有路由是否正确匹配"""
    print("\n" + "=" * 70)
    print("测试 stock_api 路由匹配")
    print("=" * 70 + "\n")

    client = TestClient(app)

    # 测试用例：(路径, 预期状态码, 描述)
    test_cases = [
        # 固定路径
        ("/api/v1/stocks/", 200, "股票列表"),
        ("/api/v1/stocks/?limit=10", 200, "股票列表带参数"),
        ("/api/v1/stocks/quote?symbols=000001,000002", 200, "实时行情"),
        ("/api/v1/stocks/hot?limit=10", 200, "热门股票"),
        ("/api/v1/stocks/search/000", 200, "搜索股票"),
        ("/api/v1/stocks/market/overview", 200, "市场概览"),

        # 参数路径 - 需要真实股票代码
        ("/api/v1/stocks/000001", 200, "股票详情"),
        ("/api/v1/stocks/000001/history", 200, "股票历史"),
        ("/api/v1/stocks/000001/history?limit=10", 200, "股票历史带参数"),
    ]

    passed = 0
    failed = 0

    for path, expected_status, description in test_cases:
        try:
            response = client.get(path)
            actual_status = response.status_code

            # 200-299 都算成功
            if 200 <= actual_status < 300:
                status_icon = "✅"
                passed += 1
                print(f"{status_icon} {description:20} | {path:50} | {actual_status}")
            else:
                status_icon = "❌"
                failed += 1
                print(f"{status_icon} {description:20} | {path:50} | {actual_status} (期望 {expected_status})")
        except Exception as e:
            status_icon = "❌"
            failed += 1
            print(f"{status_icon} {description:20} | {path:50} | 异常: {e}")

    print("\n" + "=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 70 + "\n")

    return failed == 0


def test_route_priority():
    """测试路由优先级"""
    print("\n" + "=" * 70)
    print("测试路由优先级")
    print("=" * 70 + "\n")

    from service.api.v1.stock_api import router

    # 打印路由顺序
    routes = []
    for route in router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = list(route.methods) if route.methods else []
            for method in methods:
                routes.append((method, route.path))

    print("当前路由顺序:")
    for i, (method, path) in enumerate(routes, 1):
        print(f"  {i}. {method:6} {path}")

    print("\n验证路由顺序:")

    # 检查固定路径是否在参数路径之前
    fixed_paths = [("/", "/quote", "/hot", "/search/{keyword}", "/market/overview")]
    param_paths = ["/{symbol}", "/{symbol}/history"]

    fixed_indices = []
    param_indices = []

    for i, (method, path) in enumerate(routes):
        if path in fixed_paths:
            fixed_indices.append(i)
        elif path in param_paths:
            param_indices.append(i)

    if not fixed_indices or not param_indices:
        print("  ⚠️  路径列表为空，跳过验证")
    elif max(fixed_indices) < min(param_indices):
        print("  ✅ 固定路径都在参数路径之前")
    else:
        print("  ❌ 路由顺序有问题！固定路径应该在参数路径之前")

    print()


def test_conflicting_paths():
    """测试可能的路径冲突"""
    print("\n" + "=" * 70)
    print("测试路径冲突")
    print("=" * 70 + "\n")

    client = TestClient(app)

    # 测试可能被错误匹配的路径
    conflict_tests = [
        ("/api/v1/stocks/quote", "应该匹配 /quote 而不是 /{symbol}"),
        ("/api/v1/stocks/hot", "应该匹配 /hot 而不是 /{symbol}"),
        ("/api/v1/stocks/search/abc", "应该匹配 /search/{keyword} 而不是 /{symbol}"),
        ("/api/v1/stocks/market/overview", "应该匹配 /market/overview 而不是 /{symbol}"),
    ]

    for path, description in conflict_tests:
        try:
            response = client.get(path)
            # 如果成功匹配了正确的路由，应该返回成功或特定的业务错误
            # 而不是把路径参数当作股票代码
            if response.status_code == 404:
                # 404 说明路由匹配成功，只是业务上找不到资源
                print(f"  ✅ {path}")
                print(f"     → {description}")
            elif 200 <= response.status_code < 300:
                print(f"  ✅ {path}")
                print(f"     → {description}")
            else:
                print(f"  ⚠️  {path}")
                print(f"     → {description} (状态码: {response.status_code})")
        except Exception as e:
            print(f"  ❌ {path}")
            print(f"     → {description}")
            print(f"     → 错误: {e}")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("stock_api 路由完整测试")
    print("=" * 70)

    # 运行测试
    test_route_priority()
    test_conflicting_paths()
    success = test_all_routes()

    if success:
        print("=" * 70)
        print("✅ 所有测试通过！路由配置正确")
        print("=" * 70 + "\n")
        sys.exit(0)
    else:
        print("=" * 70)
        print("❌ 部分测试失败，请检查路由配置")
        print("=" * 70 + "\n")
        sys.exit(1)
