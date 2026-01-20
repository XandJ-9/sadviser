# 开发指南

## 文档信息

- **版本**: v1.0
- **更新日期**: 2026-01-21
- **目标读者**: 开发人员

## 目录

1. [环境准备](#环境准备)
2. [项目结构](#项目结构)
3. [开发流程](#开发流程)
4. [代码规范](#代码规范)
5. [测试指南](#测试指南)
6. [常见问题](#常见问题)

---

## 环境准备

### 系统要求

- **操作系统**: Linux/macOS/Windows
- **Python**: 3.10+
- **Node.js**: 18+
- **PostgreSQL**: 14+
- **Redis**: 7+ (可选)

### 后端环境搭建

#### 1. 安装依赖

```bash
# 安装 uv (Python 包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

#### 2. 配置数据库

```bash
# 创建数据库
createdb sadviser_dev

# 执行初始化脚本
psql -d sadviser_dev -f sql/create_tables.sql
```

#### 3. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/sadviser_dev
REDIS_URL=redis://localhost:6379/0

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs
```

#### 4. 启动开发服务器

```bash
# 方式一：直接运行
uv run main.py

# 方式二：使用 uvicorn
uv run uvicorn service.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档: `http://localhost:8000/docs`

### 前端环境搭建

#### 1. 安装依赖

```bash
cd frontend

# 使用 pnpm 安装依赖
pnpm install
```

#### 2. 配置环境变量

创建 `frontend/.env` 文件：

```bash
# API 地址
VITE_API_BASE_URL=http://localhost:8000/api

# 其他配置
VITE_APP_TITLE=sadviser
```

#### 3. 启动开发服务器

```bash
pnpm dev
```

访问前端页面: `http://localhost:5173`

---

## 项目结构

### 后端目录结构

```
sadviser/
├── calculation/          # 计算层
│   ├── indicators/       # 技术指标
│   │   ├── base_indicator.py
│   │   ├── trend_indicators.py
│   │   ├── momentum_indicators.py
│   │   └── volume_indicators.py
│   ├── strategies/       # 交易策略
│   │   ├── base_strategy.py
│   │   ├── trend_strategy.py
│   │   ├── breakout_strategy.py
│   │   └── rebound_strategy.py
│   └── backtest/         # 回测系统
│       ├── base_backtest.py
│       ├── normal_backtest.py
│       └── visualization.py
├── data/                 # 数据层
│   ├── crawler/          # 数据爬虫
│   │   ├── base_crawler.py
│   │   ├── sina_crawler.py
│   │   └── tushare_crawler.py
│   ├── storage/          # 存储后端
│   │   ├── base_storage.py
│   │   ├── postgres_storage.py
│   │   └── redis_cache.py
│   └── processor/        # 数据处理
│       ├── data_cleaner.py
│       └── data_validator.py
├── service/              # 服务层
│   ├── api/              # API 路由
│   │   ├── v1/
│   │   │   ├── stock_api.py
│   │   │   ├── strategy_api.py
│   │   │   ├── backtest_api.py
│   │   │   └── task_api.py
│   │   ├── api_router.py
│   │   └── dependencies.py
│   ├── crud/             # 数据库操作
│   ├── schemas/          # 数据模型
│   ├── tasks/            # 异步任务
│   └── main.py           # 应用入口
├── utils/                # 工具函数
│   ├── custom_logger.py
│   └── akshare_api.py
├── config/               # 配置文件
├── tests/                # 测试文件
└── sql/                  # SQL 脚本
```

### 前端目录结构

```
frontend/
├── src/
│   ├── api/              # API 调用
│   │   ├── index.js      # API 客户端
│   │   ├── stock.js
│   │   ├── strategy.js
│   │   └── data.js
│   ├── components/       # 通用组件
│   │   ├── StockCard.jsx
│   │   ├── StockTable.jsx
│   │   ├── KLineChart.jsx
│   │   └── FilterPanel.jsx
│   ├── pages/            # 页面组件
│   │   ├── HomePage.jsx
│   │   ├── StockListPage.jsx
│   │   ├── StockDetailPage.jsx
│   │   └── BacktestPage.jsx
│   ├── styles/           # 样式文件
│   ├── App.jsx           # 根组件
│   └── main.jsx          # 入口文件
├── public/               # 静态资源
├── index.html
├── vite.config.js
└── tailwind.config.js
```

---

## 开发流程

### 添加新的技术指标

#### 1. 创建指标类

在 `calculation/indicators/` 下创建文件：

```python
# calculation/indicators/my_indicator.py
from .base_indicator import BaseIndicator
import pandas as pd

class MyIndicator(BaseIndicator):
    def __init__(self, period: int = 20):
        super().__init__(
            name="my_indicator",
            params={"period": period}
        )
        self.validate_params()

    def validate_params(self) -> None:
        """验证参数"""
        if not isinstance(self.params["period"], int) or self.params["period"] < 2:
            raise ValueError(f"周期必须是大于1的整数")

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算指标"""
        self.check_required_data(data, ["close", "volume"])

        # 实现计算逻辑
        result = data.copy()
        period = self.params["period"]

        # 计算指标
        result["my_indicator"] = data["close"].rolling(window=period).mean()

        self.results = result
        return result
```

#### 2. 编写测试

在 `tests/` 下创建测试文件：

```python
# tests/test_my_indicator.py
import pytest
import pandas as pd
from calculation.indicators.my_indicator import MyIndicator

def test_my_indicator_calculation():
    # 准备测试数据
    data = pd.DataFrame({
        "close": [10, 11, 12, 13, 14],
        "volume": [100, 110, 120, 130, 140]
    })

    # 创建指标并计算
    indicator = MyIndicator(period=3)
    result = indicator.calculate(data)

    # 验证结果
    assert "my_indicator" in result.columns
    assert result["my_indicator"].iloc[-1] == pytest.approx(13.0)

def test_invalid_params():
    with pytest.raises(ValueError):
        MyIndicator(period=0)
```

#### 3. 运行测试

```bash
uv run pytest tests/test_my_indicator.py
```

### 添加新的交易策略

#### 1. 创建策略类

在 `calculation/strategies/` 下创建文件：

```python
# calculation/strategies/my_strategy.py
from .base_strategy import BaseStrategy
from calculation.indicators.trend_indicators import MovingAverage
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, short_period: int = 5, long_period: int = 20):
        # 创建所需指标
        ma_short = MovingAverage(period=short_period, ma_type="sma")
        ma_long = MovingAverage(period=long_period, ma_type="sma")

        super().__init__(
            name="my_strategy",
            params={
                "short_period": short_period,
                "long_period": long_period
            },
            indicators=[ma_short, ma_long]
        )

    def validate_params(self) -> None:
        """验证参数"""
        if self.params["short_period"] >= self.params["long_period"]:
            raise ValueError("短期周期必须小于长期周期")

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        # 计算指标
        data = self.calculate_indicators(data)

        # 生成信号
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0  # 默认持有

        short_ma = f"MA_{self.params['short_period']}"
        long_ma = f"MA_{self.params['long_period']}"

        # 金叉买入
        signals.loc[data[short_ma] > data[long_ma], "signal"] = 1

        # 死叉卖出
        signals.loc[data[short_ma] < data[long_ma], "signal"] = -1

        return signals
```

#### 2. 添加 API 端点

在 `service/api/v1/strategy_api.py` 添加：

```python
@router.post("/strategies/my-strategy/backtest")
async def run_my_strategy_backtest(
    request: BacktestRequest,
    service: StrategyService = Depends(get_strategy_service)
):
    """执行自定义策略回测"""
    from calculation.strategies.my_strategy import MyStrategy

    strategy = MyStrategy(
        short_period=request.params.get("short_period", 5),
        long_period=request.params.get("long_period", 20)
    )

    result = await service.run_backtest(
        strategy=strategy,
        symbols=request.symbols,
        start_date=request.start_date,
        end_date=request.end_date
    )

    return result
```

### 添加新的 API 端点

#### 1. 创建 Pydantic 模型

在 `service/schemas/` 下创建：

```python
# service/schemas/my_api.py
from pydantic import BaseModel
from typing import Optional

class MyRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class MyResponse(BaseModel):
    symbol: str
    result: dict
```

#### 2. 创建 CRUD 操作

在 `service/crud/` 下创建：

```python
# service/crud/my_crud.py
from database import get_db
from schemas.my_api import MyRequest

async def get_my_data(request: MyRequest):
    async with get_db() as conn:
        query = "SELECT * FROM my_table WHERE symbol = $1"
        return await conn.fetch(query, request.symbol)
```

#### 3. 创建 API 路由

在 `service/api/v1/` 下创建：

```python
# service/api/v1/my_api.py
from fastapi import APIRouter, Depends, HTTPException
from schemas.my_api import MyRequest, MyResponse
from crud.my_crud import get_my_data

router = APIRouter(prefix="/my-endpoint", tags=["My API"])

@router.post("/", response_model=MyResponse)
async def my_endpoint(request: MyRequest):
    """我的 API 端点"""
    try:
        data = await get_my_data(request)
        return MyResponse(symbol=request.symbol, result=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 4. 注册路由

在 `service/api/api_router.py` 中添加：

```python
from service.api.v1 import my_api

api_router.include_router(my_api.router, prefix="/my-api")
```

### 添加前端页面

#### 1. 创建页面组件

在 `frontend/src/pages/` 下创建：

```jsx
// frontend/src/pages/MyPage.jsx
import { useState, useEffect } from 'react';
import { getStockData } from '../api/stock';

export default function MyPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await getStockData();
      setData(result);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">我的页面</h1>
      {loading ? (
        <p>加载中...</p>
      ) : (
        <div>
          {/* 数据展示 */}
        </div>
      )}
    </div>
  );
}
```

#### 2. 添加路由

在 `frontend/src/App.jsx` 中添加：

```jsx
import MyPage from './pages/MyPage';

// 在路由配置中添加
<Route path="/my-page" element={<MyPage />} />
```

---

## 代码规范

### Python 代码规范

#### 1. 命名规范

```python
# 类名：大驼峰
class StockService:
    pass

# 函数名：小写 + 下划线
def get_stock_data():
    pass

# 变量名：小写 + 下划线
stock_list = []

# 常量：大写 + 下划线
MAX_LIMIT = 100

# 私有成员：前缀下划线
class MyClass:
    def __init__(self):
        self._private_var = 0
```

#### 2. 类型注解

```python
from typing import List, Dict, Optional

def get_stocks(
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, any]]:
    """获取股票列表"""
    pass

async def fetch_stock_data(
    symbol: str
) -> Optional[pd.DataFrame]:
    """获取股票数据"""
    pass
```

#### 3. 文档字符串

```python
def calculate_returns(prices: pd.Series) -> pd.Series:
    """
    计算收益率

    Args:
        prices: 价格序列

    Returns:
        收益率序列

    Example:
        >>> prices = pd.Series([100, 110, 120])
        >>> calculate_returns(prices)
        0    0.100000
        1    0.090909
    """
    return prices.pct_change()
```

#### 4. 导入顺序

```python
# 1. 标准库
import os
from typing import List

# 2. 第三方库
import pandas as pd
from fastapi import Depends

# 3. 本地模块
from calculation.indicators.base import BaseIndicator
from utils.custom_logger import CustomLogger
```

### JavaScript/React 代码规范

#### 1. 组件命名

```jsx
// 函数组件：大驼峰
export default function StockList() {
  return <div>...</div>;
}

// 文件名：大驼峰 .jsx
// StockList.jsx
```

#### 2. Hooks 使用规范

```jsx
// ✅ 正确
function MyComponent() {
  const [data, setData] = useState([]);
  useEffect(() => {
    // 副作用
  }, []);
  return <div>{data}</div>;
}

// ❌ 错误：在循环/条件中使用 Hooks
function MyComponent() {
  if (condition) {
    const [data, setData] = useState([]); // 错误
  }
}
```

#### 3. 组件结构

```jsx
function MyComponent({ prop1, prop2 }) {
  // 1. 状态定义
  const [state, setState] = useState(null);

  // 2. 副作用
  useEffect(() => {
    // ...
  }, []);

  // 3. 派生状态
  const derivedValue = useMemo(() => {
    return computeExpensiveValue(state);
  }, [state]);

  // 4. 事件处理
  const handleClick = () => {
    // ...
  };

  // 5. 渲染
  return <div>...</div>;
}
```

---

## 测试指南

### 后端测试

#### 1. 单元测试

```python
# tests/test_indicator.py
import pytest
import pandas as pd
from calculation.indicators.trend_indicators import MovingAverage

def test_sma_calculation():
    """测试 SMA 计算"""
    data = pd.DataFrame({
        "close": [10, 11, 12, 13, 14]
    })

    ma = MovingAverage(period=3, ma_type="sma")
    result = ma.calculate(data)

    assert result["MA_3"].iloc[-1] == 13.0

def test_invalid_period():
    """测试无效参数"""
    with pytest.raises(ValueError):
        MovingAverage(period=0)
```

#### 2. 集成测试

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from service.main import app

client = TestClient(app)

def test_get_stocks():
    """测试获取股票列表 API"""
    response = client.get("/api/stocks?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    assert len(data["stocks"]) <= 10
```

#### 3. 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定文件
uv run pytest tests/test_indicator.py

# 生成覆盖率报告
uv run pytest --cov=calculation --cov-report=html
```

### 前端测试

```bash
# 运行测试
pnpm test

# 运行测试并覆盖
pnpm test:coverage
```

---

## 常见问题

### Q1: 数据库连接失败

**问题**: `could not connect to server`

**解决**:
```bash
# 检查数据库是否运行
pg_isready

# 检查连接字符串
echo $DATABASE_URL

# 重启数据库
brew services restart postgresql
```

### Q2: 前端 API 调用失败

**问题**: `Network Error` 或 `CORS Error`

**解决**:
```javascript
// 检查 API 地址配置
console.log(import.meta.env.VITE_API_BASE_URL);

// 确保后端 CORS 配置正确
# service/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Q3: 依赖安装失败

**问题**: `uv sync` 失败

**解决**:
```bash
# 清理缓存
uv cache clean

# 重新同步
uv sync --reinstall
```

### Q4: 端口被占用

**问题**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用其他端口
uv run uvicorn service.main:app --port 8001
```

---

## 相关文档

- [系统架构](./architecture.md)
- [API 接口文档](./api-reference.md)
- [日志规范](../operational/logging.md)

---

*最后更新: 2026-01-21*
