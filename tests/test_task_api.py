"""
测试 task_api 路由配置
"""
import sys
sys.path.insert(0, '/Users/xujia/MyCode/sadviser')

from service.api.v1.task_api import router

print("\n" + "=" * 70)
print("task_api 路由验证")
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

# 定义路由分类（注意：路径包含完整路径）
fixed_routes = [
    "/tasks/stats",
    "/tasks/status",
    "/tasks/recent",
    "/tasks/fetch/history",
    "/tasks/fetch/realtime",
    "/tasks/fetch/stocklist",
    "/tasks",
]

param_routes = [
    "/tasks/{task_id}"
]

# 检查固定路径
print("\n固定路径 (应该在前):")
for route_path in fixed_routes:
    for i, (method, path) in enumerate(routes):
        if path == route_path:
            icon = "✅" if i < len(routes) - 1 else "⚠️"
            print(f"  {icon} {i+1}. {method:6} {path}")
            break

# 检查参数路径
print("\n参数路径 (应该在后):")
for route_path in param_routes:
    for i, (method, path) in enumerate(routes):
        if path == route_path:
            icon = "✅" if i == len(routes) - 1 else "⚠️"
            print(f"  {icon} {i+1}. {method:6} {path} (最后)")
            break

# 验证关键路径位置
print("\n验证关键路径位置:")

all_passed = True

# 获取各路径的位置（注意：router路径包含完整路径）
stats_idx = None
status_idx = None
fetch_idx = None
param_idx = None

for i, (method, path) in enumerate(routes):
    if path == "/tasks/stats":
        stats_idx = i
    elif path == "/tasks/status":
        status_idx = i
    elif path == "/tasks/fetch/history":
        fetch_idx = i
    elif path == "/tasks/{task_id}":
        param_idx = i

# 验证固定路径在参数路径之前
if param_idx is not None:
    if stats_idx is not None and stats_idx < param_idx:
        print(f"  ✅ /stats 在 /{{task_id}} 之前 (位置 {stats_idx+1} < {param_idx+1})")
    else:
        print(f"  ❌ /stats 位置有问题")
        all_passed = False

    if status_idx is not None and status_idx < param_idx:
        print(f"  ✅ /status 在 /{{task_id}} 之前 (位置 {status_idx+1} < {param_idx+1})")
    else:
        print(f"  ❌ /status 位置有问题")
        all_passed = False

    if fetch_idx is not None and fetch_idx < param_idx:
        print(f"  ✅ /fetch/history 在 /{{task_id}} 之前 (位置 {fetch_idx+1} < {param_idx+1})")
    else:
        print(f"  ❌ /fetch/history 位置有问题")
        all_passed = False

    # 检查参数路径是否在最后
    if param_idx == len(routes) - 1:
        print(f"  ✅ /{{task_id}} 在最后位置 (位置 {param_idx+1})")
    else:
        print(f"  ⚠️  /{{task_id}} 不在最后位置 (位置 {param_idx+1})")
else:
    print(f"  ❌ 未找到参数路径 /tasks/{{task_id}}")
    all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("✅ 所有路由验证通过！路由顺序正确，没有冲突")
else:
    print("❌ 部分路由验证失败，请检查路由顺序")
print("=" * 70 + "\n")

sys.exit(0 if all_passed else 1)
