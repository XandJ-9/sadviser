# API 接口文档

## 文档信息

- **版本**: v1.0
- **更新日期**: 2026-01-21
- **Base URL**: `http://localhost:8000`
- **API 版本**: v1

## 目录

1. [概述](#概述)
2. [通用规范](#通用规范)
3. [股票数据 API](#股票数据-api)
4. [策略推荐 API](#策略推荐-api)
5. [回测 API](#回测-api)
6. [任务管理 API](#任务管理-api)
7. [数据管理 API](#数据管理-api)

---

## 概述

sadviser 提供 RESTful API 接口，用于获取股票数据、策略推荐、回测分析等功能。所有 API 返回 JSON 格式数据。

### API 版本说明

**重要**: API 路径不包含版本号，版本管理在后端内部处理
- **前端调用**: `/api/stocks`, `/api/tasks` 等（无版本号）
- **后端实现**: `service/api/v1/` 目录（当前版本 v1）
- **未来升级**: v1 → v2 时，后端内部实现切换，前端调用路径不变

---

## 通用规范

### 请求格式

```http
GET /api/stocks?limit=10&offset=0 HTTP/1.1
Host: localhost:8000
Content-Type: application/json
```

### 响应格式

#### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

#### 错误响应

```json
{
  "detail": "错误信息描述"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

---

## 股票数据 API

### 1. 获取股票列表

```http
GET /api/stocks
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| limit | integer | 否 | 返回数量 | 50 |
| offset | integer | 否 | 偏移量 | 0 |

**响应示例**:

```json
{
  "stocks": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "price": 12.50,
      "change": 0.25,
      "change_percent": 2.04
    }
  ],
  "total": 5000,
  "limit": 50,
  "offset": 0
}
```

### 2. 获取股票详情

```http
GET /api/stocks/{symbol}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 股票代码 |

**响应示例**:

```json
{
  "symbol": "000001",
  "name": "平安银行",
  "industry": "银行",
  "market": "深圳主板",
  "list_date": "1991-04-03",
  "price": 12.50,
  "change": 0.25,
  "change_percent": 2.04,
  "volume": 12345678,
  "amount": 156789012.35,
  "high": 12.65,
  "low": 12.30,
  "open": 12.35,
  "close": 12.50
}
```

### 3. 获取历史数据

```http
GET /api/stocks/{symbol}/history
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) | 30天前 |
| end_date | string | 否 | 结束日期 (YYYY-MM-DD) | 今天 |
| period | string | 否 | 周期 (daily/weekly/monthly) | daily |

**响应示例**:

```json
{
  "symbol": "000001",
  "data": [
    {
      "date": "2026-01-20",
      "open": 12.35,
      "high": 12.65,
      "low": 12.30,
      "close": 12.50,
      "volume": 12345678,
      "amount": 156789012.35
    }
  ]
}
```

### 4. 获取实时行情

```http
GET /api/stocks/quote?symbols=000001,000002
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbols | string | 是 | 股票代码，逗号分隔 |

**响应示例**:

```json
{
  "quotes": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "price": 12.50,
      "change": 0.25,
      "change_percent": 2.04,
      "volume": 12345678,
      "timestamp": "2026-01-21 09:30:00"
    }
  ],
  "count": 1
}
```

### 5. 获取热门股票

```http
GET /api/stocks/hot?limit=10
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| limit | integer | 否 | 返回数量 | 10 |

**响应示例**:

```json
{
  "stocks": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "rank": 1,
      "score": 95.5,
      "reason": "多指标共振买入信号"
    }
  ]
}
```

### 6. 搜索股票

```http
GET /api/stocks/search/{keyword}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（代码或名称） |

**响应示例**:

```json
{
  "results": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "market": "深圳主板"
    }
  ]
}
```

### 7. 获取市场概览

```http
GET /api/stocks/market/overview
```

**响应示例**:

```json
{
  "market_status": "交易中",
  "index": {
    "sh000001": {
      "name": "上证指数",
      "price": 3200.50,
      "change": 15.30,
      "change_percent": 0.48
    }
  },
  "market_stats": {
    "up_count": 2345,
    "down_count": 1234,
    "flat_count": 456,
    "limit_up_count": 50,
    "limit_down_count": 10
  }
}
```

---

## 策略推荐 API

### 1. 获取策略推荐

```http
GET /api/strategy/recommendations
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| date | string | 否 | 推荐日期 (YYYY-MM-DD) | 今天 |
| limit | integer | 否 | 返回数量 | 50 |

**响应示例**:

```json
{
  "date": "2026-01-21",
  "recommendations": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "strategy": "趋势突破策略",
      "signal": "buy",
      "confidence": 0.85,
      "reason": "均线多头排列，MACD金叉，成交量放大",
      "indicators": {
        "ma5": 12.45,
        "ma20": 12.30,
        "macd": 0.15,
        "rsi": 58.5
      }
    }
  ]
}
```

### 2. 股票筛选

```http
POST /api/strategy/screen
```

**请求体**:

```json
{
  "indicators": [
    {
      "name": "ma_cross",
      "params": { "short": 5, "long": 20 }
    },
    {
      "name": "rsi",
      "params": { "period": 14, "min": 30, "max": 70 }
    }
  ],
  "market": "全部",
  "industry": ["银行", "科技"],
  "limit": 50
}
```

**响应示例**:

```json
{
  "total": 123,
  "stocks": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "score": 85.5,
      "signals": {
        "ma_cross": "golden_cross",
        "rsi": 58.5
      }
    }
  ]
}
```

### 3. 获取交易信号

```http
GET /api/strategy/signals/{symbol}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 股票代码 |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| days | integer | 否 | 信号天数 | 30 |

**响应示例**:

```json
{
  "symbol": "000001",
  "signals": [
    {
      "date": "2026-01-21",
      "signal": "buy",
      "strategy": "趋势突破",
      "price": 12.50,
      "confidence": 0.85
    }
  ]
}
```

### 4. 获取策略列表

```http
GET /api/strategy/list
```

**响应示例**:

```json
{
  "strategies": [
    {
      "id": "trend_following",
      "name": "趋势跟踪策略",
      "description": "基于均线和MACD的趋势跟踪",
      "indicators": ["MA", "MACD", "BOLL"],
      "risk_level": "中"
    }
  ]
}
```

---

## 回测 API

### 1. 创建回测任务

```http
POST /api/backtest/create
```

**请求体**:

```json
{
  "strategy": {
    "name": "ma_cross",
    "params": {
      "short_period": 5,
      "long_period": 20
    }
  },
  "symbols": ["000001", "000002"],
  "start_date": "2025-01-01",
  "end_date": "2026-01-01",
  "initial_capital": 100000,
  "transaction_cost": 0.001,
  "slippage": 0.001
}
```

**响应示例**:

```json
{
  "task_id": "bt_20260121_001",
  "status": "running",
  "message": "回测任务已创建"
}
```

### 2. 获取回测结果

```http
GET /api/backtest/{task_id}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 回测任务 ID |

**响应示例**:

```json
{
  "task_id": "bt_20260121_001",
  "status": "completed",
  "result": {
    "total_return": 0.256,
    "annual_return": 0.25,
    "sharpe_ratio": 1.85,
    "max_drawdown": -0.123,
    "win_rate": 0.65,
    "profit_factor": 2.15
  }
}
```

### 3. 获取交易记录

```http
GET /api/backtest/{task_id}/trades
```

**响应示例**:

```json
{
  "trades": [
    {
      "symbol": "000001",
      "date": "2025-03-15",
      "action": "buy",
      "price": 11.50,
      "quantity": 1000,
      "amount": 11500,
      "cost": 11.50,
      "pnl": 1000
    }
  ]
}
```

### 4. 获取绩效指标

```http
GET /api/backtest/{task_id}/metrics
```

**响应示例**:

```json
{
  "returns": {
    "total": 0.256,
    "annual": 0.25,
    "monthly": 0.02
  },
  "risk": {
    "sharpe_ratio": 1.85,
    "max_drawdown": -0.123,
    "volatility": 0.15
  },
  "trades": {
    "total_count": 45,
    "win_count": 29,
    "loss_count": 16,
    "win_rate": 0.644
  }
}
```

---

## 任务管理 API

### 1. 获取任务列表

```http
GET /api/tasks
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| status | string | 否 | 任务状态 (pending/running/completed/failed) | - |
| limit | integer | 否 | 返回数量 | 20 |
| offset | integer | 否 | 偏移量 | 0 |

**响应示例**:

```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "type": "data_fetch",
      "status": "completed",
      "created_at": "2026-01-21 09:00:00",
      "updated_at": "2026-01-21 09:05:00",
      "message": "数据获取完成"
    }
  ],
  "count": 1
}
```

### 2. 获取任务详情

```http
GET /api/tasks/{task_id}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID |

**响应示例**:

```json
{
  "task_id": "task_001",
  "type": "data_fetch",
  "status": "completed",
  "progress": 100,
  "created_at": "2026-01-21 09:00:00",
  "updated_at": "2026-01-21 09:05:00",
  "result": { ... },
  "message": "数据获取完成"
}
```

### 3. 取消任务

```http
POST /api/tasks/{task_id}/cancel
```

**响应示例**:

```json
{
  "task_id": "task_001",
  "status": "cancelled",
  "message": "任务已取消"
}
```

### 4. 获取任务统计

```http
GET /api/tasks/stats
```

**响应示例**:

```json
{
  "total_tasks": 150,
  "status_counts": {
    "pending": 5,
    "running": 3,
    "completed": 140,
    "failed": 2
  },
  "type_counts": {
    "data_fetch": 80,
    "backtest": 50,
    "strategy_screen": 20
  }
}
```

### 5. 获取系统状态

```http
GET /api/tasks/status
```

**响应示例**:

```json
{
  "status": "healthy",
  "storage_connected": true,
  "active_tasks": 3,
  "queue_size": 5,
  "uptime": 86400,
  "last_update": "2026-01-21 10:00:00"
}
```

### 6. 获取最近任务

```http
GET /api/tasks/recent?limit=10
```

**响应示例**:

```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "type": "data_fetch",
      "status": "completed",
      "created_at": "2026-01-21 09:00:00"
    }
  ]
}
```

---

## 数据管理 API

### 1. 获取历史数据

```http
POST /api/tasks/fetch/history
```

**请求体**:

```json
{
  "symbols": ["000001", "000002"],
  "start_date": "2025-01-01",
  "end_date": "2026-01-01",
  "source": "akshare",
  "store": true
}
```

**响应示例**:

```json
{
  "task_id": "task_002",
  "status": "pending",
  "message": "历史数据获取任务已创建"
}
```

### 2. 获取实时行情

```http
POST /api/tasks/fetch/realtime?symbols=000001,000002&source=akshare&store=true
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbols | string | 是 | 股票代码，逗号分隔 |
| source | string | 否 | 数据源 (akshare/sina) | akshare |
| store | boolean | 否 | 是否存储 | true |

**响应示例**:

```json
{
  "quotes": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "price": 12.50,
      "change": 0.25,
      "change_percent": 2.04
    }
  ],
  "count": 1,
  "stored": true
}
```

### 3. 获取股票列表

```http
GET /api/tasks/fetch/stocklist?source=akshare&store=true
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| source | string | 否 | 数据源 | akshare |
| store | boolean | 否 | 是否存储 | false |

**响应示例**:

```json
{
  "count": 5000,
  "stocks": [
    {
      "symbol": "000001",
      "name": "平安银行",
      "market": "深圳主板"
    }
  ],
  "stored": true
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误信息描述"
}
```

### 常见错误码

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|----------|------|
| 400 | BadRequest | 请求参数错误 |
| 404 | NotFound | 资源不存在 |
| 422 | ValidationError | 数据验证失败 |
| 500 | InternalError | 服务器内部错误 |

### 错误示例

```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

---

## 接口版本管理

### 当前版本: v1

- **Base Path**: `/api`
- **实现位置**: `service/api/v1/`

### 版本升级策略

1. **向后兼容**: 尽量保持向后兼容
2. **渐进式迁移**: 新版本并行运行
3. **弃用通知**: 提前通知接口变更
4. **版本切换**: 后端内部实现切换，前端路径不变

---

## API 文档访问

### Swagger UI

访问地址: `http://localhost:8000/docs`

### ReDoc

访问地址: `http://localhost:8000/redoc`

---

## 相关文档

- [系统架构](./architecture.md)
- [数据库设计](./database-schema.md)
- [开发指南](./development-guide.md)

---

*最后更新: 2026-01-21*
