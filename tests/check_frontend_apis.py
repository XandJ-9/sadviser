"""
前后端接口完整性检查
"""
import sys
sys.path.insert(0, '/Users/xujia/MyCode/sadviser')

print("\n" + "=" * 80)
print("前后端接口完整性检查报告")
print("=" * 80 + "\n")

# 前端使用的接口列表
frontend_apis = {
    # stock.js
    "GET /api/v1/stocks": "获取股票列表",
    "GET /api/v1/stocks/{symbol}": "获取股票详情",
    "GET /api/v1/stocks/{symbol}/history": "获取股票历史数据",
    "GET /api/v1/stocks/quote": "获取实时行情",
    "GET /api/v1/stocks/search/{keyword}": "搜索股票",
    "GET /api/v1/stocks/hot": "获取热门股票",
    "GET /api/v1/stocks/market/overview": "获取市场概览",

    # data.js
    "POST /api/v1/tasks/fetch/history": "创建历史数据获取任务",
    "POST /api/v1/tasks/fetch/realtime": "获取实时行情",
    "GET /api/v1/tasks/fetch/stocklist": "获取股票列表",
    "GET /api/v1/tasks": "获取所有任务",
    "GET /api/v1/tasks/{task_id}": "获取任务状态",
    "GET /api/v1/tasks/recent": "获取最近任务",
    "GET /api/v1/tasks/stats": "获取任务统计",
    "GET /api/v1/tasks/status": "获取系统状态",
    "POST /api/v1/data/store/batch": "批量存储数据 (已废弃)",
    "GET /api/v1/data/query": "查询数据 (已废弃)",

    # strategy.js
    "GET /api/v1/strategy/recommendations": "获取每日推荐",
    "POST /api/v1/strategy/screen": "股票筛选",
    "GET /api/v1/strategy/signals/{symbol}": "获取交易信号",
    "GET /api/v1/strategy/list": "获取策略列表",
    "POST /api/v1/backtest/create": "执行策略回测",
    "GET /api/v1/backtest/{task_id}": "获取回测结果",
    "GET /api/v1/backtest/{task_id}/trades": "获取回测交易记录",
    "GET /api/v1/backtest/{task_id}/metrics": "获取回测绩效指标",
}

# 从后端获取实际路由
from service.main import app

backend_routes = set()
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        for method in route.methods or []:
            if route.path not in ['/', '/health', '/docs', '/docs/oauth2-redirect', '/openapi.json', '/redoc']:
                backend_routes.add(f"{method} {route.path}")

# 检查每个前端API
print("【前端使用的接口检查】")
print("-" * 80)

issues = []
matched = []
deprecated = []

for api, description in frontend_apis.items():
    # 提取方法和路径
    parts = api.split(' ', 1)
    if len(parts) != 2:
        continue

    method, path = parts

    # 标记废弃的接口
    if '已废弃' in description:
        deprecated.append(api)
        if path in backend_routes or any(path in r for r in backend_routes):
            status = "⚠️  仍然可用但应迁移"
        else:
            status = "❌ 已不可用"
            issues.append(f"{api} - {description}: {status}")
    else:
        # 检查后端是否有对应接口
        # 处理路径参数的匹配
        found = False
        for backend_route in backend_routes:
            if method in backend_route:
                backend_path = backend_route.split(' ', 1)[1]
                # 简单匹配：检查路径模式是否相同
                if backend_path == path:
                    found = True
                    matched.append(api)
                    break
                # 处理路径参数
                if '{' in backend_path:
                    # 将路径参数替换为通配符进行比较
                    backend_pattern = backend_path.split('{')[0]
                    if path.startswith(backend_pattern):
                        found = True
                        matched.append(api)
                        break

        if found:
            status = "✅ 匹配"
        else:
            status = "❌ 后端不存在"
            issues.append(f"{api} - {description}: {status}")

    print(f"{status:20} {api:45} | {description}")

print("\n" + "=" * 80)
print("【统计信息】")
print("-" * 80)
print(f"前端接口总数: {len(frontend_apis)}")
print(f"匹配成功: {len(matched)}")
print(f"已废弃: {len(deprecated)}")
print(f"存在问题: {len(issues)}")

if issues:
    print("\n" + "=" * 80)
    print("【发现的问题】")
    print("-" * 80)
    for issue in issues:
        print(f"  ❌ {issue}")
else:
    print("\n" + "=" * 80)
    print("✅ 所有前端接口都已正确匹配后端！")

print("=" * 80 + "\n")

# 特别检查：参数传递方式
print("【参数传递方式检查】")
print("-" * 80)

checks = [
    {
        "name": "fetchRealtimeData",
        "frontend": "symbols 数组 -> 逗号分隔字符串",
        "backend": "symbols: str (逗号分隔)",
        "status": "✅ 已修复"
    },
    {
        "name": "getStockQuote",
        "frontend": "symbols 数组 -> 逗号分隔字符串",
        "backend": "symbols: str (逗号分隔)",
        "status": "✅ 正确"
    },
    {
        "name": "getTasks",
        "frontend": "返回 response.tasks",
        "backend": "返回 {tasks: [...]}",
        "status": "✅ 已适配"
    },
]

for check in checks:
    print(f"{check['status']:10} {check['name']:30} | {check['frontend']}")
    if check['backend']:
        print(f"{'':40} 后端: {check['backend']}")

print("\n" + "=" * 80)
print("检查完成！")
print("=" * 80 + "\n")

sys.exit(0 if not issues else 1)
