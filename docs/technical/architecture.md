# sadviser 系统架构设计

## 文档信息

- **版本**: v1.0
- **更新日期**: 2026-01-21
- **维护者**: 开发团队

## 目录

1. [架构概述](#架构概述)
2. [技术架构](#技术架构)
3. [模块设计](#模块设计)
4. [数据流](#数据流)
5. [技术栈](#技术栈)
6. [部署架构](#部署架构)

---

## 架构概述

### 设计原则

sadviser 采用**分层架构设计**，遵循以下核心原则：

1. **模块化**: 高内聚、低耦合，各模块独立开发和部署
2. **可扩展性**: 支持水平扩展和功能扩展
3. **高性能**: 异步处理、缓存优化、并行计算
4. **可维护性**: 清晰的代码结构、统一的接口规范
5. **安全性**: 数据加密、权限控制、输入验证

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                     │
│                   React 19 + Vite + Tailwind                  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS/WebSocket
┌────────────────────────────┴────────────────────────────────┐
│                         服务层 (Service)                      │
│                      FastAPI + Pydantic                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Stock API │  │  Strategy   │  │      Task API       │  │
│  │             │  │     API     │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                        计算层 (Calculation)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Indicators  │  │  Strategies  │  │  Backtest    │      │
│  │              │  │              │  │              │      │
│  │  趋势指标     │  │  趋势策略     │  │  回测引擎     │      │
│  │  动量指标     │  │  突破策略     │  │  绩效分析     │      │
│  │  量能指标     │  │  反弹策略     │  │  可视化       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                         数据层 (Data)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Crawlers   │  │   Storage    │  │    Cache     │      │
│  │              │  │              │  │              │      │
│  │  Sina        │  │  PostgreSQL  │  │  Redis       │      │
│  │  Tushare     │  │  MongoDB     │  │              │      │
│  │  AKShare     │  │  Parquet     │  │              │      │
│  │  WebSocket   │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术架构

### 分层架构

#### 1. 前端层 (Frontend Layer)

**职责**: 用户界面、数据展示、用户交互

**技术栈**:
- **框架**: React 19
- **构建工具**: Vite
- **样式**: Tailwind CSS v4
- **路由**: Wouter
- **图表**: Recharts
- **状态管理**: React Hooks (Context API)

**核心模块**:
```
frontend/src/
├── pages/           # 页面组件
│   ├── HomePage.jsx
│   ├── StockListPage.jsx
│   ├── StockDetailPage.jsx
│   ├── BacktestPage.jsx
│   └── DataManagementPage.jsx
├── components/      # 通用组件
│   ├── StockCard.jsx
│   ├── StockTable.jsx
│   ├── KLineChart.jsx
│   ├── FilterPanel.jsx
│   └── TaskList.jsx
├── api/            # API 调用封装
│   ├── index.js
│   ├── stock.js
│   ├── strategy.js
│   └── data.js
└── styles/         # 样式文件
```

#### 2. 服务层 (Service Layer)

**职责**: API 服务、业务逻辑、任务调度

**技术栈**:
- **框架**: FastAPI
- **验证**: Pydantic
- **异步**: asyncio/aiohttp
- **任务调度**: BackgroundTasks

**核心模块**:
```
service/
├── api/
│   ├── api_router.py      # 路由聚合
│   ├── dependencies.py    # 依赖注入
│   └── v1/                # API v1 版本
│       ├── stock_api.py    # 股票数据 API
│       ├── strategy_api.py # 策略推荐 API
│       ├── backtest_api.py # 回测 API
│       └── task_api.py     # 任务管理 API
├── crud/                  # 数据库操作
│   ├── stock_crud.py
│   └── task_crud.py
├── schemas/               # 数据模型
│   ├── stock.py
│   ├── strategy.py
│   ├── backtest.py
│   └── task.py
├── tasks/                 # 异步任务
│   ├── data_tasks.py
│   └── strategy_tasks.py
└── main.py               # 应用入口
```

#### 3. 计算层 (Calculation Layer)

**职责**: 技术指标计算、策略信号生成、回测分析

**技术栈**:
- **数值计算**: NumPy, Pandas
- **技术分析**: TA-Lib
- **并行计算**: multiprocessing, concurrent.futures

**核心模块**:
```
calculation/
├── indicators/           # 技术指标
│   ├── base_indicator.py      # 指标基类
│   ├── trend_indicators.py    # 趋势类指标 (MA, MACD, BOLL)
│   ├── momentum_indicators.py # 动量类指标 (RSI, KDJ)
│   └── volume_indicators.py   # 量能类指标 (OBV, VOL)
├── strategies/           # 交易策略
│   ├── base_strategy.py       # 策略基类
│   ├── trend_strategy.py      # 趋势策略
│   ├── breakout_strategy.py   # 突破策略
│   └── rebound_strategy.py    # 反弹策略
└── backtest/             # 回测系统
    ├── base_backtest.py       # 回测基类
    ├── normal_backtest.py     # 普通回测
    ├── backtest_engine.py     # 回测引擎
    └── visualization.py       # 结果可视化
```

#### 4. 数据层 (Data Layer)

**职责**: 数据获取、数据存储、缓存管理

**技术栈**:
- **HTTP 客户端**: aiohttp, requests
- **数据库**: PostgreSQL (asyncpg)
- **缓存**: Redis (aioredis)
- **文档存储**: MongoDB (motor)
- **数据归档**: Parquet (pyarrow)

**核心模块**:
```
data/
├── crawler/              # 数据爬虫
│   ├── base_crawler.py        # 爬虫基类
│   ├── sina_crawler.py        # 新浪数据源
│   ├── tushare_crawler.py     # Tushare 数据源
│   └── websocket_connector.py # WebSocket 实时数据
├── storage/              # 存储后端
│   ├── base_storage.py        # 存储基类
│   ├── postgres_storage.py    # PostgreSQL 存储
│   ├── mongodb_storage.py     # MongoDB 存储
│   ├── redis_cache.py         # Redis 缓存
│   └── parquet_archive.py     # Parquet 归档
└── processor/            # 数据处理
    ├── data_cleaner.py        # 数据清洗
    ├── feature_engineering.py # 特征工程
    └── data_validator.py      # 数据验证
```

---

## 模块设计

### 1. 指标计算模块

**设计模式**: 策略模式 + 模板方法模式

```python
class BaseIndicator(ABC):
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算指标"""

    def validate_params(self) -> None:
        """验证参数"""

    def get_results(self) -> pd.DataFrame:
        """获取计算结果"""
```

**核心特性**:
- ✅ 统一的接口规范
- ✅ 参数验证机制
- ✅ 数据检查功能
- ✅ 支持批量计算 (IndicatorCombiner)

### 2. 策略框架模块

**设计模式**: 依赖注入 + 组合模式

```python
class BaseStrategy(ABC):
    def __init__(self, indicators: List[BaseIndicator]):
        self.indicators = indicators

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号 (1=买入, 0=持有, -1=卖出)"""

    def evaluate(self, data: pd.DataFrame) -> Dict:
        """评估策略绩效"""
```

**核心特性**:
- ✅ 指标依赖注入
- ✅ 信号生成机制
- ✅ 绩效评估体系
- ✅ 策略组合器 (majority_vote, weighted_average, consensus)

### 3. 回测系统模块

**设计模式**: 模板方法模式 + 策略模式

```python
class BaseBacktest(ABC):
    @abstractmethod
    def run(self) -> Dict:
        """执行回测"""

    def calculate_metrics(self, returns: pd.Series) -> Dict:
        """计算绩效指标"""
        # 夏普比率、最大回撤、胜率、盈亏比

    def _execute_trade(self, signal, price, date):
        """模拟交易执行（含成本和滑点）"""
```

**核心特性**:
- ✅ 交易成本模拟
- ✅ 滑点模拟
- ✅ 风险控制 (止损/止盈)
- ✅ 头寸管理
- ✅ 完整的绩效指标

### 4. 数据获取模块

**设计模式**: 工厂模式 + 适配器模式

```python
class BaseCrawler(ABC):
    @abstractmethod
    async def fetch_daily_data(self, symbol: str) -> pd.DataFrame:
        """获取历史日线数据"""

    @abstractmethod
    async def fetch_realtime_quote(self, symbols: List[str]) -> Dict:
        """获取实时行情"""
```

**核心特性**:
- ✅ 异步数据获取
- ✅ 自动重试机制
- ✅ 多数据源支持
- ✅ 数据格式统一

### 5. 存储模块

**设计模式**: 适配器模式

```python
class BaseStorage(ABC):
    @abstractmethod
    async def connect(self):
        """连接数据库"""

    @abstractmethod
    async def insert(self, data: pd.DataFrame):
        """插入数据"""

    @abstractmethod
    async def query(self, filters: Dict) -> pd.DataFrame:
        """查询数据"""
```

**核心特性**:
- ✅ 统一的存储接口
- ✅ 支持多种存储后端
- ✅ 异步操作
- ✅ 自动时间戳管理

---

## 数据流

### 数据获取流程

```
┌─────────────┐
│  Data Source │ (Sina/Tushare/AKShare)
└──────┬──────┘
       │ HTTP/WebSocket
┌──────▼──────────────────────────┐
│       Crawler (异步爬取)         │
│  - 自动重试                      │
│  - 速率限制                      │
│  - 错误处理                      │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│    Data Validator (数据验证)     │
│  - 格式检查                      │
│  - 异常值检测                    │
│  - 数据完整性                    │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│    Data Cleaner (数据清洗)       │
│  - 去重                          │
│  - 缺失值处理                    │
│  - 格式统一                      │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   Storage (持久化存储)           │
│  - PostgreSQL (关系数据)         │
│  - MongoDB (灵活文档)            │
│  - Redis (缓存层)                │
└──────────────────────────────────┘
```

### 指标计算流程

```
┌─────────────┐
│ Stock Data  │ (OHLCV)
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│  IndicatorCombiner (批量计算)    │
│  - 依赖排序                      │
│  - 并行计算                      │
│  - 结果合并                      │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   BaseIndicator (指标计算)        │
│  - 趋势指标 (MA, MACD, BOLL)     │
│  - 动量指标 (RSI, KDJ, CCI)      │
│  - 量能指标 (OBV, VOL, VR)       │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│  Strategy (策略信号生成)          │
│  - 趋势策略                      │
│  - 突破策略                      │
│  - 反弹策略                      │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│  Signal Output (信号输出)        │
│  - 1: 买入信号                   │
│  - 0: 持有信号                   │
│  - -1: 卖出信号                  │
└──────────────────────────────────┘
```

### API 请求流程

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │ HTTP Request
┌────▼─────────────────────────────┐
│      API Gateway (FastAPI)        │
│  - 请求验证                       │
│  - 参数解析                       │
│  - 权限检查                       │
└────┬─────────────────────────────┘
     │
┌────▼─────────────────────────────┐
│    Business Logic (Service)       │
│  - 业务逻辑处理                   │
│  - 数据组装                       │
└────┬─────────────────────────────┘
     │
┌────▼─────────────────────────────┐
│  Data Access (Repository/CRUD)    │
│  - 数据库查询                     │
│  - 缓存访问                       │
└────┬─────────────────────────────┘
     │
┌────▼─────────────────────────────┐
│   Calculation (计算引擎)           │
│  - 指标计算                       │
│  - 策略执行                       │
│  - 回测分析                       │
└────┬─────────────────────────────┘
     │
┌────▼─────────────────────────────┐
│  Response (JSON/WebSocket)        │
└───────────────────────────────────┘
```

---

## 技术栈

### 后端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **运行时** | Python | 3.10+ | 主要开发语言 |
| **Web 框架** | FastAPI | 0.104+ | API 服务 |
| **数据验证** | Pydantic | 2.0+ | 数据模型 |
| **HTTP 客户端** | aiohttp | 3.8+ | 异步请求 |
| **数据处理** | Pandas | 2.0+ | 数据分析 |
| | NumPy | 1.24+ | 数值计算 |
| **技术分析** | TA-Lib | 0.4+ | 指标计算 |
| **数据库** | PostgreSQL | 14+ | 主数据库 |
| | MongoDB | 6+ | 文档存储 |
| | Redis | 7+ | 缓存 |
| **异步驱动** | asyncpg | - | PostgreSQL 异步 |
| | motor | - | MongoDB 异步 |
| | aioredis | - | Redis 异步 |

### 前端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **框架** | React | 19.0+ | UI 框架 |
| **构建工具** | Vite | 5.0+ | 构建工具 |
| **包管理器** | pnpm | 8.0+ | 依赖管理 |
| **样式** | Tailwind CSS | 4.0+ | CSS 框架 |
| **路由** | Wouter | 3.0+ | 路由管理 |
| **图表** | Recharts | 2.10+ | 数据可视化 |

### 开发工具

| 类别 | 技术 | 用途 |
|------|------|------|
| **包管理** | uv | Python 依赖管理 |
| **代码格式化** | Black | Python 代码格式化 |
| **类型检查** | mypy | Python 类型检查 |
| **测试框架** | pytest | 单元测试 |
| **文档生成** | MkDocs | 文档站点 |

---

## 部署架构

### 开发环境

```
┌─────────────────────────────────────────┐
│           Developer Machine              │
│  ┌─────────────┐  ┌─────────────┐       │
│  │  Frontend   │  │   Backend   │       │
│  │  (Vite Dev) │  │  (uv run)   │       │
│  │  :5173      │  │  :8000      │       │
│  └──────┬──────┘  └──────┬──────┘       │
│         │                │              │
└─────────┼────────────────┼──────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────┐
│          Local Services                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  PostgreSQL │  │  Redis  │  │ MongoDB │ │
│  │  :5432   │  │  :6379  │  │  :27017 │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────┘
```

### 生产环境

```
                                    ┌─────────────┐
                                    │   Users     │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │    CDN      │
                                    │  (Static)   │
                                    └──────┬──────┘
                                           │
        ┌──────────────────────────────────┼────────────────┐
        │                                  │                │
┌───────▼────────┐              ┌──────────▼─────────┐
│  Frontend Pod  │              │   Backend Pod      │
│  (React Build) │              │   (FastAPI)        │
│  Port: 80      │              │   Port: 8000       │
└────────────────┘              └──────────┬─────────┘
                                          │
        ┌─────────────────────────────────┼────────────────┐
        │                                 │                │
┌───────▼────────┐      ┌─────────┐  ┌───▼────┐  ┌───────▼─────┐
│ PostgreSQL     │      │  Redis  │  │ MongoDB │  │  Task Queue │
│ (Primary)      │      │  Cache  │  │  Store  │  │  (Celery)   │
└───────┬────────┘      └─────────┘  └─────────┘  └─────────────┘
         │
┌────────▼────────┐
│  PostgreSQL     │
│  (Replica)      │
└─────────────────┘
```

---

## 扩展性设计

### 水平扩展

1. **无状态服务**: API 服务无状态，可随意增减实例
2. **负载均衡**: Nginx/Istio 实现负载均衡
3. **数据库读写分离**: 主从复制，读写分离
4. **缓存集群**: Redis Cluster 模式

### 功能扩展

1. **插件化指标**: 实现新的 BaseIndicator 子类
2. **策略插件**: 实现新的 BaseStrategy 子类
3. **数据源插件**: 实现新的 BaseCrawler 子类
4. **存储插件**: 实现新的 BaseStorage 子类

---

## 安全设计

1. **输入验证**: Pydantic 模型严格验证
2. **SQL 注入防护**: 参数化查询
3. **XSS 防护**: 前端数据转义
4. **CORS 配置**: 严格的跨域控制
5. **速率限制**: API 访问频率限制
6. **数据加密**: 敏感数据加密存储

---

## 监控与日志

### 监控指标

- **系统指标**: CPU、内存、磁盘、网络
- **应用指标**: QPS、响应时间、错误率
- **业务指标**: 任务数量、计算耗时、数据量

### 日志系统

- **统一格式**: CustomLogger 标准化输出
- **日志级别**: DEBUG、INFO、WARNING、ERROR、CRITICAL
- **日志聚合**: ELK Stack (Elasticsearch + Logstash + Kibana)

---

## 相关文档

- [API 接口文档](./api-reference.md)
- [数据库设计](./database-schema.md)
- [部署指南](./deployment.md)
- [开发指南](./development-guide.md)

---

*最后更新: 2026-01-21*
