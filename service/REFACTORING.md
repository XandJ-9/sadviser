# 后端接口重构总结

## 重构目标
1. 所有接口数据来源于数据库查询
2. 不在接口代码中调用数据获取接口（crawler）
3. 封装数据库查询逻辑
4. 减少重复代码

## 新架构设计

### 分层架构
```
API 层 (service/api/v1/)
    ↓
Service 层 (service/services/)
    ↓
Repository 层 (service/repositories/)
    ↓
Storage 层 (data/storage/)
```

### 各层职责

#### 1. API 层 (stock_api.py)
- **职责**: 处理 HTTP 请求/响应，参数验证
- **特点**:
  - 轻量级，只处理 HTTP 相关逻辑
  - 不直接访问数据库
  - 不调用数据爬虫
  - 通过依赖注入获取 Service 实例

**代码示例**:
```python
@router.get("/")
async def get_stocks(limit: int = 50, offset: int = 0):
    try:
        service = get_stock_service()
        return await service.get_stock_list(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2. Service 层 (services/stock_service.py)
- **职责**: 业务逻辑处理，数据转换
- **特点**:
  - 封装业务规则
  - 数据格式转换
  - 调用 Repository 获取数据
  - 不关心数据来源（数据库/缓存）

**代码示例**:
```python
class StockService:
    def __init__(self, stock_repository):
        self.repository = stock_repository

    async def get_stock_list(self, limit: int = 50, offset: int = 0):
        result = await self.repository.get_stocks_with_latest_prices(
            limit=limit, offset=offset
        )

        # 添加业务逻辑
        for stock in result.get("stocks", []):
            stock["indicators"] = {...}  # 添加技术指标

        return result
```

#### 3. Repository 层 (repositories/stock_repository.py)
- **职责**: 封装数据库查询逻辑
- **特点**:
  - 专门针对特定实体（Stock）的数据访问
  - 复杂查询封装
  - SQL 优化
  - 只返回原始数据，不包含业务逻辑

**代码示例**:
```python
class StockRepository(BaseRepository):
    async def get_stocks_with_latest_prices(self, limit: int, offset: int):
        total = await self.get_stock_list_count()
        stocks = await self.get_stock_list(limit=limit, offset=offset)

        result = []
        for stock in stocks:
            stock_with_price = await self.get_stock_with_latest_price(symbol)
            result.append(stock_with_price)

        return {"stocks": result, "total": total}
```

#### 4. Base Repository (repositories/base_repository.py)
- **职责**: 提供通用的数据库操作方法
- **特点**:
  - 可复用的基础查询方法
  - 统一的错误处理
  - 连接管理

**方法列表**:
- `find_one()`: 查询单条记录
- `find_many()`: 查询多条记录
- `count()`: 统计记录数
- `get_latest_date()`: 获取最新日期

#### 5. 依赖注入容器 (core/container.py)
- **职责**: 管理服务实例的生命周期
- **特点**:
  - 单例模式确保资源复用
  - 集中化配置管理
  - 便于测试和扩展

**使用示例**:
```python
from service.core.container import container

# 获取服务实例
stock_service = container.get_stock_service()

# 使用服务
result = await stock_service.get_stock_list(limit=10)
```

## 重构前后对比

### 重构前 (stock_api.py)
```python
# ❌ 问题：直接在 API 中操作数据库和调用爬虫
@router.get("/")
async def get_stocks(limit: int = 50, offset: int = 0):
    storage = get_storage()

    # 直接查询数据库
    count_result = await conn.fetch("SELECT COUNT(*) as total FROM stock_list")
    stocks = await storage.query(...)

    # 为每只股票添加最新价格（循环查询）
    for stock in stocks:
        latest_data = await storage.query(...)  # N+1 查询问题

    # 调用爬虫获取实时数据
    quote = await crawler.fetch_realtime_quote(...)

    return {"stocks": result, "total": total}
```

**问题**:
1. API 层直接操作数据库
2. 代码重复（每个 API 都有类似的查询逻辑）
3. 业务逻辑与数据访问混合
4. 难以测试和维护
5. 调用爬虫导致响应慢

### 重构后 (stock_api.py)
```python
# ✅ 改进：只处理 HTTP 请求/响应
@router.get("/")
async def get_stocks(limit: int = 50, offset: int = 0):
    try:
        service = get_stock_service()
        return await service.get_stock_list(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**优势**:
1. API 层只有 10 行代码
2. 所有数据来自数据库
3. 业务逻辑在 Service 层
4. 数据访问在 Repository 层
5. 易于测试（可 mock Service）
6. 代码复用性高

## 代码统计

### 重构前
- **stock_api.py**: 594 行
- 包含数据库操作、爬虫调用、业务逻辑

### 重构后
- **stock_api.py**: 182 行（减少 69%）
- **services/stock_service.py**: 177 行（新增）
- **repositories/stock_repository.py**: 389 行（新增）
- **repositories/base_repository.py**: 160 行（新增）
- **core/container.py**: 64 行（新增）

### 总体变化
- API 层代码大幅简化
- 职责清晰分离
- 可测试性提升
- 可维护性提升

## 测试结果

所有测试通过：
```
tests/test_refactored_api.py::test_container PASSED       [ 25%]
tests/test_refactored_api.py::test_repository PASSED      [ 50%]
tests/test_refactored_api.py::test_service PASSED         [ 75%]
tests/test_refactored_api.py::test_api_endpoints PASSED    [100%]
============================== 4 passed in 0.43s ===============================
```

## 如何扩展

### 添加新的 API 端点
1. 在 Service 层添加业务逻辑方法
2. 在 API 层创建路由，调用 Service
3. 不需要修改 Repository 层（如果使用现有方法）

### 添加新的 Repository
1. 继承 `BaseRepository`
2. 实现特定的数据库查询方法
3. 在 Container 中注册

### 添加新的 Service
1. 创建 Service 类，接受 Repository 实例
2. 实现业务逻辑方法
3. 在 Container 中添加 getter 方法

## 最佳实践

1. **API 层**:
   - 只处理 HTTP 请求/响应
   - 参数验证
   - 异常处理和日志记录

2. **Service 层**:
   - 业务逻辑
   - 数据转换
   - 缓存管理（后续添加）
   - 不直接访问数据库

3. **Repository 层**:
   - 数据库查询
   - SQL 优化
   - 只返回原始数据

4. **依赖注入**:
   - 使用 Container 获取实例
   - 不要直接 new 实例
   - 便于单元测试

## 后续改进建议

1. **添加缓存层**:
   - 在 Service 层添加 Redis 缓存
   - 减少数据库查询

2. **添加 DTO 层**:
   - 使用 Pydantic 模型定义数据结构
   - 自动验证和序列化

3. **添加事务支持**:
   - 在 Service 层添加事务管理
   - 确保数据一致性

4. **优化查询性能**:
   - 使用批量查询代替循环查询
   - 添加数据库索引

5. **添加监控和日志**:
   - 记录 API 调用链路
   - 性能监控

## 文件结构

```
service/
├── api/
│   └── v1/
│       └── stock_api.py          # API 层（重构）
├── services/
│   ├── __init__.py
│   └── stock_service.py          # Service 层（新增）
├── repositories/
│   ├── __init__.py
│   ├── base_repository.py        # 基础 Repository（新增）
│   └── stock_repository.py       # Stock Repository（新增）
└── core/
    ├── __init__.py
    └── container.py              # 依赖注入容器（新增）
```

## 总结

本次重构成功实现了以下目标：
1. ✅ 所有接口数据来源于数据库查询
2. ✅ 不在接口代码中调用数据获取接口
3. ✅ 封装数据库查询逻辑到 Repository 层
4. ✅ 大幅减少重复代码

新架构具有以下优势：
- **可维护性**: 职责分离，代码清晰
- **可测试性**: 各层独立，易于 mock
- **可扩展性**: 添加新功能更容易
- **可复用性**: Repository 和 Service 可被多个 API 使用
