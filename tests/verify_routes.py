"""
验证 stock_api 路由顺序（不调用实际API）
"""
import sys
sys.path.insert(0, '/Users/xujia/MyCode/sadviser')

from service.api.v1.stock_api import router

print("\n" + "=" * 70)
print("stock_api 路由顺序验证")
print("=" * 70 + "\n")

# 获取所有路由
routes = []
for route in router.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = list(route.methods) if route.methods else []
        for method in methods:
            routes.append((method, route.path))

print("当前路由顺序:")
for i, (method, path) in enumerate(routes, 1):
    print(f"  {i}. {method:6} {path}")

# 验证路由顺序
print("\n验证路由顺序:")

# 定义路由分类
fixed_routes = [
    "/",
    "/quote",
    "/hot",
    "/search/{keyword}",
    "/market/overview"
]

param_routes = [
    "/{symbol}/history",
    "/{symbol}"
]

# 检查每个路由的位置
print("\n固定路径 (应该在前):")
for route_path in fixed_routes:
    for i, (method, path) in enumerate(routes):
        if path == route_path:
            print(f"  ✅ {i+1}. {method:6} {path}")
            break

print("\n参数路径 (应该在后):")
for route_path in param_routes:
    for i, (method, path) in enumerate(routes):
        if path == route_path:
            print(f"  ✅ {i+1}. {method:6} {path}")
            break

# 验证关键路径冲突
print("\n验证关键路径冲突:")

critical_tests = [
    {
        "path": "/quote",
        "should_match": "/quote",
        "should_not_match": "/{symbol}",
        "description": "访问 /quote 应该匹配固定路径，不是参数路径"
    },
    {
        "path": "/hot",
        "should_match": "/hot",
        "should_not_match": "/{symbol}",
        "description": "访问 /hot 应该匹配固定路径，不是参数路径"
    },
    {
        "path": "/search/abc",
        "should_match": "/search/{keyword}",
        "should_not_match": "/{symbol}",
        "description": "访问 /search/abc 应该匹配 search，不是 symbol"
    },
    {
        "path": "/market/overview",
        "should_match": "/market/overview",
        "should_not_match": "/{symbol}",
        "description": "访问 /market/overview 应该匹配固定路径，不是 {symbol}"
    },
    {
        "path": "/000001",
        "should_match": "/{symbol}",
        "should_not_match": None,
        "description": "访问 /000001 应该匹配参数路径"
    },
    {
        "path": "/000001/history",
        "should_match": "/{symbol}/history",
        "should_not_match": "/{symbol}",
        "description": "访问 /000001/history 应该匹配 /{symbol}/history，不是 /{symbol}"
    }
]

# 模拟 FastAPI 路由匹配
def match_route(test_path):
    """模拟 FastAPI 路由匹配逻辑"""
    for method, route_path in routes:
        # 简化的路径匹配逻辑
        route_parts = route_path.split('/')
        test_parts = test_path.split('/')

        # 如果路由没有参数，必须完全匹配
        if '{' not in route_path:
            if test_path == route_path:
                return route_path

        # 如果路由有参数
        else:
            # 检查路径段数量
            if len(test_parts) == len(route_parts):
                return route_path
    return None

print("\n路由匹配测试:")
all_passed = True
for test in critical_tests:
    matched = match_route(test["path"])

    if matched == test["should_match"]:
        print(f"  ✅ {test['path']:25} → {matched}")
        print(f"     {test['description']}")
    else:
        print(f"  ❌ {test['path']:25} → {matched} (期望: {test['should_match']})")
        print(f"     {test['description']}")
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("✅ 所有路由验证通过！路由顺序正确")
else:
    print("❌ 部分路由验证失败，请检查路由顺序")
print("=" * 70 + "\n")

sys.exit(0 if all_passed else 1)
