# stock_api 路由配置验证报告

## 路由顺序

当前路由配置（正确的顺序）：

```
1. GET /stocks/                      → 获取股票列表
2. GET /stocks/quote                 → 获取实时行情
3. GET /stocks/hot                   → 获取热门股票
4. GET /stocks/search/{keyword}     → 搜索股票
5. GET /stocks/market/overview       → 获取市场概览
6. GET /stocks/{symbol}/history      → 获取股票历史数据
7. GET /stocks/{symbol}             → 获取股票详情
```

## 路由分类

### 固定路径（优先匹配）

这些路径没有任何参数，必须放在前面：

| 路由 | 端点函数 | 说明 |
|------|---------|------|
| `/stocks/` | `get_stocks` | 获取股票列表 |
| `/stocks/quote` | `get_stock_quote` | 获取实时行情 |
| `/stocks/hot` | `get_hot_stocks` | 获取热门股票 |
| `/stocks/search/{keyword}` | `search_stocks` | 搜索股票 |
| `/stocks/market/overview` | `get_market_overview` | 获取市场概览 |

### 参数路径（后匹配）

这些路径包含参数，必须放在后面：

| 路由 | 端点函数 | 说明 |
|------|---------|------|
| `/stocks/{symbol}/history` | `get_stock_history` | 获取股票历史数据 |
| `/stocks/{symbol}` | `get_stock_detail` | 获取股票详情 |

## 为什么这个顺序很重要？

FastAPI 按照路由定义的顺序进行匹配，一旦匹配成功就停止查找。

### 错误的顺序（会导致冲突）

```python
# ❌ 错误示例
@router.get("/{symbol}")           # 第 2 位
async def get_stock_detail(symbol: str):
    ...

@router.get("/quote")              # 第 4 位
async def get_stock_quote():
    ...
```

**问题**：
- 访问 `/quote` 会被 `/{symbol}` 匹配
- `quote` 被当作股票代码 `symbol`
- `/quote` 路由永远不会被匹配到

### 正确的顺序（当前配置）

```python
# ✅ 正确示例
@router.get("/quote")              # 第 2 位 - 先匹配固定路径
async def get_stock_quote():
    ...

@router.get("/{symbol}")           # 第 7 位 - 后匹配参数路径
async def get_stock_detail(symbol: str):
    ...
```

**效果**：
- 访问 `/quote` 正确匹配到 `/quote` 路由
- 访问 `/000001` 正确匹配到 `/{symbol}` 路由

## 路由匹配测试

### 测试用例

| 请求路径 | 匹配的路由 | 说明 |
|---------|-----------|------|
| `/stocks/` | `/stocks/` | 股票列表 |
| `/stocks/?limit=10` | `/stocks/` | 股票列表（带参数） |
| `/stocks/quote?symbols=000001` | `/stocks/quote` | 实时行情 |
| `/stocks/hot?limit=10` | `/stocks/hot` | 热门股票 |
| `/stocks/search/000` | `/stocks/search/{keyword}` | 搜索股票 |
| `/stocks/market/overview` | `/stocks/market/overview` | 市场概览 |
| `/stocks/000001` | `/stocks/{symbol}` | 股票详情 |
| `/stocks/000001/history` | `/stocks/{symbol}/history` | 股票历史 |

### 关键测试

1. **测试 `/quote` 不会被 `/{symbol}` 匹配**
   - ✅ 正确匹配到 `/quote` 路由
   - ✅ 不会把 "quote" 当作股票代码

2. **测试 `/hot` 不会被 `/{symbol}` 匹配**
   - ✅ 正确匹配到 `/hot` 路由
   - ✅ 不会把 "hot" 当作股票代码

3. **测试 `/search/xxx` 不会被 `/{symbol}` 匹配**
   - ✅ 正确匹配到 `/search/{keyword}` 路由
   - ✅ 不会把 "search" 当作股票代码

4. **测试 `/market/overview` 不会被 `/{symbol}` 匹配**
   - ✅ 正确匹配到 `/market/overview` 路由
   - ✅ 不会把 "market" 当作股票代码

5. **测试 `/{symbol}/history` 优先级高于 `/{symbol}`**
   - ✅ `/000001/history` 匹配到 `/{symbol}/history`
   - ✅ 不会匹配到 `/{symbol}` (把 "history" 当作股票代码)

## FastAPI 路由匹配规则

### 匹配优先级

1. **完全匹配优先**
   - `/stocks/quote` 完全匹配
   - `/stocks/hot` 完全匹配

2. **路径长度优先**
   - `/stocks/{symbol}/history` (3 段) 优先于
   - `/stocks/{symbol}` (2 段)

3. **定义顺序优先**
   - 如果两个路由都能匹配，先定义的优先

### 最佳实践

1. **固定路径在前，参数路径在后**
   ```python
   # ✅ 正确
   @router.get("/fixed")        # 固定路径
   @router.get("/{param}")       # 参数路径

   # ❌ 错误
   @router.get("/{param}")       # 参数路径
   @router.get("/fixed")        # 永远不会匹配
   ```

2. **更具体的路径在前**
   ```python
   # ✅ 正确
   @router.get("/users/{id}/posts")    # 更具体
   @router.get("/users/{id}")          # 更通用

   # ❌ 错误
   @router.get("/users/{id}")          # 会匹配所有请求
   @router.get("/users/{id}/posts")    # 永远不会匹配
   ```

3. **添加注释说明**
   ```python
   # ==================== 固定路径（优先匹配） ====================
   @router.get("/quote")
   async def get_stock_quote():
       ...

   # ==================== 参数路径（后匹配） ====================
   @router.get("/{symbol}")
   async def get_stock_detail(symbol: str):
       ...
   ```

## 验证脚本

运行验证脚本检查路由配置：

```bash
PYTHONPATH=/Users/xujia/MyCode/sadviser uv run python -c "
from service.api.v1.stock_api import router

for i, route in enumerate(router.routes, 1):
    if hasattr(route, 'path'):
        print(f'{i}. {route.path} -> {route.endpoint.__name__}')
"
```

## 总结

✅ **当前路由配置完全正确**

- 所有固定路径都在参数路径之前
- `/{symbol}/history` 在 `/{symbol}` 之前
- 路由冲突问题已解决
- 所有路由都能正确匹配

✅ **路由顺序验证通过**

1. `/stocks/` - 第 1 位 ✅
2. `/stocks/quote` - 第 2 位 ✅
3. `/stocks/hot` - 第 3 位 ✅
4. `/stocks/search/{keyword}` - 第 4 位 ✅
5. `/stocks/market/overview` - 第 5 位 ✅
6. `/stocks/{symbol}/history` - 第 6 位 ✅
7. `/stocks/{symbol}` - 第 7 位 ✅

所有路由都能正确匹配，没有冲突！
