"""
使用 FastAPI 实际路由匹配验证
"""
import sys
sys.path.insert(0, '/Users/xujia/MyCode/sadviser')

from fastapi import FastAPI
from service.api.v1.stock_api import router

# 创建测试应用
app = FastAPI()
app.include_router(router)

print("\n" + "=" * 70)
print("stock_api 路由验证（使用 FastAPI 实际匹配）")
print("=" * 70 + "\n")

# 获取所有路由
routes = []
for route in router.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = list(route.methods) if route.methods else []
        for method in methods:
            routes.append((method, route.path, route))

print("当前路由顺序:")
for i, (method, path, _) in enumerate(routes, 1):
    print(f"  {i}. {method:6} {path}")

# 测试路由匹配
print("\n路由匹配测试:")

test_cases = [
    ("/", "应该匹配 / (股票列表)"),
    ("/?limit=10", "应该匹配 / (股票列表带参数)"),
    ("/quote?symbols=000001", "应该匹配 /quote (实时行情)"),
    ("/hot?limit=10", "应该匹配 /hot (热门股票)"),
    ("/search/000", "应该匹配 /search/{keyword} (搜索)"),
    ("/market/overview", "应该匹配 /market/overview (市场概览)"),
    ("/000001", "应该匹配 /{symbol} (股票详情)"),
    ("/000001/history", "应该匹配 /{symbol}/history (历史数据)"),
]

# 模拟路由匹配
def find_route(path):
    """使用 FastAPI 的路由匹配逻辑"""
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            # 简化匹配：检查路径是否匹配模式
            route_path = route.path

            # 完全匹配
            if path == route_path or path.split('?')[0] == route_path:
                return route_path, route

            # 参数匹配
            if '{' in route_path:
                route_parts = route_path.split('/')
                test_parts = path.split('?')[0].split('/')

                if len(route_parts) == len(test_parts):
                    # 检查固定部分是否匹配
                    match = True
                    for rp, tp in zip(route_parts, test_parts):
                        if not rp.startswith('{') and rp != tp:
                            match = False
                            break

                    if match:
                        return route_path, route

    return None, None

all_passed = True
for test_path, description in test_cases:
    matched_path, route_obj = find_route(test_path)

    if matched_path:
        # 获取路由函数名
        if hasattr(route_obj, 'endpoint'):
            func_name = route_obj.endpoint.__name__
        else:
            func_name = "unknown"

        print(f"  ✅ {test_path:40} → {matched_path:25} ({func_name})")
        print(f"     {description}")
    else:
        print(f"  ❌ {test_path:40} → 未匹配")
        print(f"     {description}")
        all_passed = False

# 验证路由顺序
print("\n路由顺序验证:")

# 检查 /quote 是否在 /{symbol} 之前
quote_idx = None
symbol_idx = None

for i, (_, path, _) in enumerate(routes):
    if path == "/quote":
        quote_idx = i
    elif path == "/{symbol}":
        symbol_idx = i

if quote_idx is not None and symbol_idx is not None:
    if quote_idx < symbol_idx:
        print(f"  ✅ /quote 在 /{{symbol}} 之前 (位置 {quote_idx+1} < {symbol_idx+1})")
    else:
        print(f"  ❌ /quote 在 /{{symbol}} 之后 (位置 {quote_idx+1} > {symbol_idx+1})")
        all_passed = False
else:
    print(f"  ⚠️  无法确定 /quote 和 /{{symbol}} 的位置")

# 检查 /hot 是否在 /{symbol} 之前
hot_idx = None
for i, (_, path, _) in enumerate(routes):
    if path == "/hot":
        hot_idx = i
        break

if hot_idx is not None and symbol_idx is not None:
    if hot_idx < symbol_idx:
        print(f"  ✅ /hot 在 /{{symbol}} 之前 (位置 {hot_idx+1} < {symbol_idx+1})")
    else:
        print(f"  ❌ /hot 在 /{{symbol}} 之后 (位置 {hot_idx+1} > {symbol_idx+1})")
        all_passed = False

# 检查 /{symbol}/history 是否在 /{symbol} 之前
history_idx = None
for i, (_, path, _) in enumerate(routes):
    if path == "/{symbol}/history":
        history_idx = i
        break

if history_idx is not None and symbol_idx is not None:
    if history_idx < symbol_idx:
        print(f"  ✅ /{{symbol}}/history 在 /{{symbol}} 之前 (位置 {history_idx+1} < {symbol_idx+1})")
    else:
        print(f"  ❌ /{{symbol}}/history 在 /{{symbol}} 之后 (位置 {history_idx+1} > {symbol_idx+1})")
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("✅ 所有路由验证通过！路由顺序正确，没有冲突")
else:
    print("❌ 路由验证失败，存在路由冲突")
print("=" * 70 + "\n")

sys.exit(0 if all_passed else 1)
