# API Refactoring Guide

## Overview

This document describes the refactoring of the API module to follow FastAPI best practices, replacing the existing services/repositories pattern with Pydantic schemas and CRUD modules.

## Architecture Changes

### Before (Old Pattern)
```
API Layer → Service Layer → Repository Layer → Storage Layer
```

### After (New Pattern)
```
API Layer (with Pydantic Schemas) → CRUD Layer → Storage Layer
```

## Key Improvements

### 1. **Pydantic Schemas**
- **Location**: `service/schemas/`
- **Purpose**: Request/response validation, automatic API documentation
- **Benefits**:
  - Type safety
  - Automatic validation
  - Better error messages
  - Self-documenting APIs

**Example**:
```python
from service.schemas.stock import StockInfo, StockListResponse

@router.get("/", response_model=StockListResponse)
async def get_stocks(
    limit: int = Query(50, ge=1, le=500),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    # Returns validated StockListResponse
    pass
```

### 2. **Database Dependencies**
- **Location**: `service/database.py`
- **Purpose**: FastAPI dependency injection for database connections
- **Benefits**:
  - Automatic connection management
  - Request-scoped connections
  - Clean shutdown handling

**Example**:
```python
from service.database import get_storage
from data.storage.postgres_storage import PostgreSQLStorage

@router.get("/stocks")
async def get_stocks(storage: PostgreSQLStorage = Depends(get_storage)):
    # storage is automatically injected and connected
    result = await storage.query("stock_list")
    return result
```

### 3. **CRUD Modules**
- **Location**: `service/crud/`
- **Purpose**: Direct database operations without complex abstraction
- **Benefits**:
  - Simpler code structure
  - Easier to maintain
  - Better performance
  - More testable

**Example**:
```python
from service.crud.stock_crud import StockCRUD

@router.get("/stocks/{symbol}")
async def get_stock(symbol: str, storage: PostgreSQLStorage = Depends(get_storage)):
    crud = StockCRUD(storage)
    stock = await crud.get_stock_by_symbol(symbol)
    return stock
```

## Directory Structure

```
service/
├── schemas/              # Pydantic schemas
│   ├── __init__.py
│   ├── stock.py         # Stock-related schemas
│   ├── strategy.py      # Strategy-related schemas
│   ├── backtest.py      # Backtest-related schemas
│   └── task.py          # Task-related schemas
├── crud/                # CRUD operations
│   ├── __init__.py
│   └── stock_crud.py    # Stock CRUD operations
├── database.py          # Database dependencies
├── api/
│   └── v1/
│       ├── stock_api.py     # Refactored ✅
│       ├── strategy_api.py  # To be refactored
│       ├── backtest_api.py  # To be refactored
│       └── task_api.py      # To be refactored
├── services/            # Legacy (to be removed)
└── repositories/        # Legacy (to be removed)
```

## Schema Design Patterns

### Request Schemas
Used for validating incoming requests:

```python
from pydantic import BaseModel, Field, field_validator

class FetchHistoryRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1)
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    source: Literal["akshare", "tushare"] = Field("akshare")

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
```

### Response Schemas
Used for serializing responses:

```python
class StockListResponse(BaseModel):
    stocks: List[StockInfo] = Field(..., description="List of stocks")
    total: int = Field(..., description="Total number of stocks", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "stocks": [...],
                "total": 5000
            }
        }
```

## CRUD Pattern

### Basic CRUD Class

```python
class StockCRUD:
    def __init__(self, storage: PostgreSQLStorage):
        self.storage = storage

    async def get_stock_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get single stock by symbol"""
        return await self.storage.find_one(
            table_name="stock_list",
            conditions={"symbol": symbol}
        )

    async def get_stock_list(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get paginated stock list"""
        # Custom SQL for better performance
        conn = await self.storage._get_connection()
        query = "SELECT * FROM stock_list ORDER BY symbol LIMIT $1 OFFSET $2"
        rows = await conn.fetch(query, limit, offset)
        await self.storage.pool.release(conn)
        return [dict(row) for row in rows]
```

## API Endpoint Patterns

### Pattern 1: Simple List Endpoint

```python
@router.get("/", response_model=StockListResponse)
async def get_stocks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    crud = StockCRUD(storage)
    stocks = await crud.get_stock_list(limit=limit, offset=offset)
    total = await crud.get_stock_list_count()

    return StockListResponse(stocks=stocks, total=total)
```

### Pattern 2: Detail Endpoint

```python
@router.get("/{symbol}", response_model=StockDetailResponse)
async def get_stock_detail(
    symbol: str,
    storage: PostgreSQLStorage = Depends(get_storage)
):
    crud = StockCRUD(storage)
    stock = await crud.get_stock_by_symbol(symbol)

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    return StockDetailResponse(**stock)
```

### Pattern 3: Search Endpoint

```python
@router.get("/search/{keyword}", response_model=StockSearchResponse)
async def search_stocks(
    keyword: str,
    limit: int = Query(20, ge=1, le=100),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    crud = StockCRUD(storage)
    stocks = await crud.search_stocks(keyword=keyword, limit=limit)

    return StockSearchResponse(stocks=stocks, total=len(stocks))
```

## Migration Checklist

For each API file to be refactored:

### ✅ stock_api.py - COMPLETED
- [x] Import Pydantic schemas
- [x] Replace service dependency with storage dependency
- [x] Create StockCRUD class
- [x] Update all endpoints to use schemas
- [x] Add response_model to all endpoints
- [x] Add Query validators
- [x] Update error handling

### ⏳ strategy_api.py - PENDING
- [ ] Import strategy schemas
- [ ] Replace mock data with CRUD operations
- [ ] Create StrategyCRUD class
- [ ] Update all endpoints
- [ ] Add request/response models

### ⏳ backtest_api.py - PENDING
- [ ] Import backtest schemas
- [ ] Create BacktestCRUD class
- [ ] Update all endpoints
- [ ] Add complex validation
- [ ] Handle long-running tasks

### ⏳ task_api.py - PENDING
- [ ] Import task schemas (partially done)
- [ ] Update to use new schema structure
- [ ] Create TaskCRUD class
- [ ] Update background task handling

## Best Practices

### 1. Always Use Response Models
```python
# ❌ Bad
@router.get("/stocks")
async def get_stocks():
    return {"stocks": [...], "total": 100}

# ✅ Good
@router.get("/stocks", response_model=StockListResponse)
async def get_stocks():
    return StockListResponse(stocks=[...], total=100)
```

### 2. Validate Input Parameters
```python
# ❌ Bad
@router.get("/stocks")
async def get_stocks(limit: int, offset: int):
    pass

# ✅ Good
@router.get("/stocks")
async def get_stocks(
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    pass
```

### 3. Use Field Descriptions
```python
class StockInfo(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., sh600000)")
    name: str = Field(..., description="Stock name")
    price: float = Field(..., description="Current price", ge=0)
```

### 4. Custom Validators
```python
@field_validator('date')
@classmethod
def validate_date_format(cls, v: str) -> str:
    try:
        datetime.strptime(v, '%Y-%m-%d')
        return v
    except ValueError:
        raise ValueError('Date must be in YYYY-MM-DD format')
```

### 5. Error Handling
```python
try:
    result = await crud.get_stock(symbol)
    if not result:
        raise HTTPException(status_code=404, detail="Stock not found")
    return result
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## Benefits

1. **Type Safety**: Pydantic provides automatic type checking
2. **Documentation**: Auto-generated OpenAPI docs at `/docs`
3. **Validation**: Input/output validation built-in
4. **Maintainability**: Clearer code structure
5. **Performance**: Fewer abstraction layers
6. **Testing**: Easier to test with clear interfaces

## Testing

### Example Test with New Pattern

```python
import pytest
from httpx import AsyncClient
from service.main import app

@pytest.mark.asyncio
async def test_get_stocks():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/stocks?limit=10")

    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    assert "total" in data
    assert len(data["stocks"]) <= 10
```

## Rollback Plan

If needed, the old code can be restored from git history:

```bash
# View changes
git diff HEAD -- service/api/v1/stock_api.py

# Revert specific file
git checkout HEAD -- service/api/v1/stock_api.py

# Revert all changes
git reset --hard HEAD
```

## Next Steps

1. Complete remaining API refactoring (strategy, backtest, task)
2. Remove legacy service and repository files
3. Update integration tests
4. Update API documentation
5. Performance testing

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
