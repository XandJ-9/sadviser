# FastAPI 依赖注入使用指南

## 概述

本项目使用 FastAPI 的依赖注入系统来管理服务的注入，实现了更优雅、更符合 FastAPI 最佳实践的方式。

## 架构

```
API 端点 (stock_api.py)
    ↓ 使用 Depends
依赖函数 (dependencies.py)
    ↓ 获取实例
容器 (core/container.py)
    ↓ 管理单例
服务实例 (StockService)
```

## 文件结构

```
service/
├── api/
│   ├── dependencies.py         # 依赖函数定义
│   └── v1/
│       └── stock_api.py        # API 路由（使用 Depends）
├── services/
│   └── stock_service.py        # 业务逻辑服务
└── core/
    └── container.py            # 依赖注入容器
```

## 使用方法

### 1. 定义依赖函数

在 `service/api/dependencies.py` 中定义依赖函数：

```python
from fastapi import Depends
from service.core.container import container
from service.services.stock_service import StockService


def get_stock_service() -> StockService:
    """
    获取 StockService 实例的依赖函数

    FastAPI 会自动调用这个函数，并将返回值注入到路由函数中

    Returns:
        StockService 实例（单例）
    """
    return container.get_stock_service()
```

### 2. 在 API 路由中使用依赖注入

在路由函数中，使用 `Depends` 来声明依赖：

```python
from fastapi import APIRouter, Depends
from service.api.dependencies import get_stock_service
from service.services.stock_service import StockService

router = APIRouter(prefix='/stocks', tags=['stocks'])


@router.get("/")
async def get_stocks(
    limit: int = 50,
    offset: int = 0,
    service: StockService = Depends(get_stock_service)  # ← 依赖注入
):
    """
    获取股票列表

    Args:
        limit: 返回数量限制
        offset: 偏移量
        service: 注入的 StockService 实例（由 FastAPI 自动提供）
    """
    return await service.get_stock_list(limit=limit, offset=offset)
```

### 3. FastAPI 自动处理依赖

FastAPI 会自动：
1. 在请求到达时调用 `get_stock_service()`
2. 将返回的 `StockService` 实例注入到 `service` 参数
3. 在路由函数执行完毕后自动清理

## 优势

### 1. 更符合 FastAPI 最佳实践
- ✅ 使用官方推荐的依赖注入方式
- ✅ 自动处理依赖的生命周期
- ✅ 与 FastAPI 文档和 OpenAPI 集成

### 2. 代码更简洁
- ✅ 不需要在每个函数中手动调用 `get_stock_service()`
- ✅ 减少重复代码

### 3. 更容易测试
- ✅ 可以轻松覆盖依赖（Override Dependencies）
- ✅ 可以注入 Mock 实例进行单元测试

### 4. 类型提示和自动补全
- ✅ IDE 可以识别 `service` 参数的类型
- ✅ 提供更好的代码提示

## 对比：重构前 vs 重构后

### 重构前
```python
@router.get("/")
async def get_stocks(limit: int = 50, offset: int = 0):
    try:
        # ❌ 手动调用函数获取服务
        service = get_stock_service()
        return await service.get_stock_list(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 重构后
```python
@router.get("/")
async def get_stocks(
    limit: int = 50,
    offset: int = 0,
    service: StockService = Depends(get_stock_service)  # ✅ 依赖注入
):
    try:
        # ✅ 直接使用注入的 service
        return await service.get_stock_list(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## 测试

### 验证依赖注入配置

运行简单验证测试：
```bash
PYTHONPATH=/Users/xujia/MyCode/sadviser uv run python tests/test_fastapi_depends_simple.py
```

### 单元测试示例

使用 FastAPI 的 `DependencyOverride` 来覆盖依赖：

```python
from fastapi.testclient import TestClient
from service.main import app

# 创建 Mock 服务
class MockStockService:
    async def get_stock_list(self, limit, offset):
        return {"stocks": [], "total": 0}

# 覆盖依赖
app.dependency_overrides[get_stock_service] = lambda: MockStockService()

# 使用测试客户端
client = TestClient(app)
response = client.get("/api/v1/stocks/")
```

## 扩展：添加新的依赖

### 1. 创建新的 Service

```python
# service/services/strategy_service.py
class StrategyService:
    def __init__(self, strategy_repository):
        self.repository = strategy_repository

    async def get_strategies(self):
        return await self.repository.find_all()
```

### 2. 在 Container 中注册

```python
# service/core/container.py
class Container:
    def __init__(self):
        self._strategy_service: Optional[StrategyService] = None

    def get_strategy_service(self) -> StrategyService:
        if self._strategy_service is None:
            self._strategy_service = StrategyService(
                self.get_strategy_repository()
            )
        return self._strategy_service
```

### 3. 创建依赖函数

```python
# service/api/dependencies.py
def get_strategy_service() -> StrategyService:
    return container.get_strategy_service()
```

### 4. 在 API 中使用

```python
from service.api.dependencies import get_strategy_service
from service.services.strategy_service import StrategyService

@router.get("/strategies")
async def get_strategies(
    service: StrategyService = Depends(get_strategy_service)
):
    return await service.get_strategies()
```

## 常见问题

### Q1: 为什么要使用 FastAPI 的 Depends 而不是直接调用函数？

**A**: FastAPI 的 `Depends` 提供了以下优势：
- 自动依赖管理
- 支持依赖的嵌套和层级
- 更好的测试支持（可以轻松覆盖）
- 与 FastAPI 的文档系统自动集成
- 支持缓存和单例模式

### Q2: 依赖函数每次请求都会被调用吗？

**A**: 这取决于依赖函数的实现。在我们的实现中：
- `get_stock_service()` 返回的是 Container 中的单例
- 所有请求共享同一个 `StockService` 实例
- 如果需要每次请求创建新实例，可以在依赖函数中直接 `return StockService(...)`

### Q3: 如何在测试中覆盖依赖？

**A**: 使用 FastAPI 的 `dependency_overrides`：

```python
from service.api.dependencies import get_stock_service

# 在测试中覆盖
app.dependency_overrides[get_stock_service] = lambda: MockStockService()
```

### Q4: 一个路由可以有多个依赖吗？

**A**: 可以！每个需要注入的服务都使用 `Depends`：

```python
@router.get("/analysis/{symbol}")
async def get_analysis(
    symbol: str,
    stock_service: StockService = Depends(get_stock_service),
    strategy_service: StrategyService = Depends(get_strategy_service),
    backtest_service: BacktestService = Depends(get_backtest_service)
):
    # 可以同时使用多个服务
    stock = await stock_service.get_stock_detail(symbol)
    strategies = await strategy_service.get_strategies()
    ...
```

## 最佳实践

1. **依赖函数应该简单**
   - 只负责返回服务实例
   - 不要包含业务逻辑

2. **使用类型提示**
   - 明确指定依赖的返回类型
   - 帮助 IDE 提供更好的代码提示

3. **保持依赖的单例**
   - 通过 Container 管理服务实例
   - 避免重复创建昂贵的资源（如数据库连接）

4. **文档化依赖**
   - 为每个依赖函数添加文档字符串
   - 在路由文档中说明注入的参数

## 总结

使用 FastAPI 的依赖注入系统：

✅ **更标准**: 符合 FastAPI 最佳实践
✅ **更简洁**: 减少重复代码
✅ **更易测试**: 支持依赖覆盖
✅ **更易维护**: 集中管理依赖
✅ **类型安全**: 完整的类型提示

参考文档：
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI Dependency Override](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
