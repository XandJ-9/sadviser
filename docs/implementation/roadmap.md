# sadviser 股票投资建议平台 - 开发计划与实施路线图

## 文档版本信息
- **创建日期**: 2026-01-02
- **版本**: v1.0
- **项目状态**: 核心框架已完成,待完善功能模块

---

## 目录
1. [项目概述](#1-项目概述)
2. [当前实现状态](#2-当前实现状态)
3. [功能缺失分析](#3-功能缺失分析)
4. [优先级划分](#4-优先级划分)
5. [实施路线图](#5-实施路线图)
6. [详细开发任务](#6-详细开发任务)

---

## 1. 项目概述

### 1.1 项目目标
构建一个基于技术指标的股票投资建议平台,提供:
- 多维度技术指标筛选
- 策略回测与优化
- 实时行情监控
- 智能投资建议
- 用户友好的交互界面

### 1.2 技术架构
```
前端层 (React 19)
    ↓
服务层 (FastAPI)
    ↓
计算层 (指标计算 + 策略引擎 + 回测系统)
    ↓
数据层 (爬虫 + 存储系统)
```

### 1.3 核心价值主张
- **准确性**: 基于历史数据验证的指标和策略
- **可扩展性**: 模块化设计,易于添加新功能
- **可解释性**: 所有推荐都有清晰的逻辑说明
- **高性能**: 支持全市场股票的实时筛选

---

## 2. 当前实现状态

### 2.1 已完成功能 ✅

#### 数据层
- ✅ **BaseCrawler基类** (data/crawler/base_crawler.py)
  - 异步HTTP请求框架
  - 自动重试机制
  - 日期验证逻辑

- ✅ **SinaCrawler爬虫** (data/crawler/sina_crawler.py)
  - 日线数据获取
  - 实时行情获取
  - 批量请求支持

- ✅ **BaseStorage基类** (data/storage/base_storage.py)
  - 统一CRUD接口
  - 异步操作支持
  - 时间戳管理

- ✅ **PostgreSQLStorage** (data/storage/postgres_storage.py)
  - 连接池管理
  - 批量操作支持
  - 表结构定义(stock_info, stock_daily, stock_minute)

#### 计算层
- ✅ **BaseIndicator基类** (calculation/indicators/base_indicator.py)
  - 参数验证机制
  - 数据检查功能
  - IndicatorCombiner组合器

- ✅ **趋势类指标** (calculation/indicators/trend_indicators.py)
  - MovingAverage (SMA, EMA, WMA, DEMA, TEMA)
  - MACD指标
  - BollingerBands指标

- ✅ **BaseStrategy基类** (calculation/strategies/base_strategy.py)
  - 策略生命周期管理
  - 绩效评估体系
  - StrategyCombiner组合器(majority_vote, weighted_average, consensus)

- ✅ **趋势策略** (calculation/strategies/trend_strategy.py)
  - MovingAverageCrossStrategy (均线交叉策略)
  - MACDStrategy (MACD策略)
  - BollingerBandStrategy (布林带策略)

- ✅ **BaseBacktest基类** (calculation/backtest/base_backtest.py)
  - 回测框架定义
  - 绩效指标计算(夏普比率、最大回撤、胜率等)
  - 交易成本模拟

#### 工具层
- ✅ **CustomLogger** (utils/custom_logger.py)
  - 彩色控制台输出
  - 文件日志支持
  - 多级别日志分离

- ✅ **AkShare API封装** (utils/akshare_api.py)
  - 基础API接口

#### 服务层
- ✅ **FastAPI主应用** (service/main.py)
- ✅ **API路由聚合** (service/api/api_router.py)
- ✅ **股票数据API基础** (service/api/v1/stock_api.py)

#### 前端
- ✅ **React 19框架** (frontend/)
- ✅ **Vite构建工具**
- ✅ **Tailwind CSS v4**
- ✅ **项目结构搭建**

#### 测试
- ✅ 日志功能测试 (tests/test_simple_logging.py)
- ✅ 新浪爬虫测试 (tests/test_sina_stock.py)

### 2.2 项目统计
- **总代码文件**: ~30个
- **已完成功能**: 核心框架 (~40%)
- **待实现功能**: 扩展模块和高级功能 (~60%)
- **测试覆盖率**: <10%

---

## 3. 功能缺失分析

### 3.1 数据层缺失功能

#### 3.1.1 爬虫模块
| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `tushare_crawler.py` | ❌ 空 | P1 | Tushare数据源爬取器 |
| `websocket_connector.py` | ❌ 空 | P2 | 实时行情WebSocket连接 |

**需要实现的功能**:
- TushareCrawler: 需要集成Tushare Pro API
  - 历史日线数据获取
  - 财务数据获取
  - 股票基本信息获取
- WebSocketConnector: 需要实现实时数据推送
  - WebSocket连接管理
  - 实时行情订阅
  - 断线重连机制

#### 3.1.2 存储模块
| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `mongodb_storage.py` | ❌ 空 | P1 | MongoDB存储实现 |
| `redis_cache.py` | ❌ 空 | P1 | Redis缓存实现 |
| `parquet_archive.py` | ❌ 空 | P2 | Parquet格式归档 |

**需要实现的功能**:
- MongoDBStorage:
  - 文档模型定义
  - CRUD操作实现
  - 索引优化
- RedisCache:
  - 缓存策略设计
  - TTL管理
  - 缓存预热机制
- ParquetArchive:
  - 数据分区策略
  - 压缩存储
  - 批量查询优化

#### 3.1.3 数据处理模块
| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `data/processor/` 目录 | ❌ 不存在 | P1 | 数据处理组件 |

**需要创建的文件**:
- `data_cleaner.py`: 数据清洗(去重、补全、格式转换)
- `feature_engineering.py`: 特征工程(衍生指标生成)
- `data_validator.py`: 数据校验(异常值检测、格式校验)

### 3.2 计算层缺失功能

#### 3.2.1 指标模块
| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `momentum_indicators.py` | ❌ 空 | P0 | 动量类指标(RSI, KDJ等) |
| `volume_indicators.py` | ❌ 不存在 | P1 | 量能类指标(OBV, VOL等) |
| `custom_indicators.py` | ❌ 不存在 | P2 | 自定义组合指标 |

**需要实现的指标**:
- **动量类指标**:
  - RSI (相对强弱指标)
  - KDJ (随机指标)
  - CCI (顺势指标)
  - WR (威廉指标)
  - MOM (动量指标)

- **量能类指标**:
  - OBV (能量潮)
  - VOL (成交量)
  - VR (成交量变异率)
  - EMV (简易波动指标)

- **自定义指标**:
  - 多指标组合评分
  - 市场情绪指标
  - 资金流向指标

#### 3.2.2 策略模块
| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `breakout_strategy.py` | ❌ 不存在 | P1 | 突破策略 |
| `rebound_strategy.py` | ❌ 不存在 | P1 | 反弹策略 |

**需要实现的策略**:
- **BreakoutStrategy**:
  - 价格突破策略
  - 成交量突破策略
  - 形态突破策略

- **ReboundStrategy**:
  - 超跌反弹策略
  - 支撑位反弹策略
  - 技术形态反弹策略

#### 3.2.3 回测模块
| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `normal_backtest.py` | ❌ 空 | P0 | 普通回测实现 |
| `backtest_engine.py` | ❌ 不存在 | P0 | 回测核心逻辑 |
| `result_analyzer.py` | ❌ 不存在 | P1 | 回测结果分析 |
| `visualization.py` | ❌ 不存在 | P1 | 回测结果可视化 |

**需要实现的功能**:
- **NormalBacktest**:
  - 完整的回测流程
  - 交易执行逻辑
  - 风险控制机制(止损、止盈)
  - 头寸管理

- **BacktestEngine**:
  - 多策略并行回测
  - 参数优化框架(网格搜索、遗传算法)
  - 样本内外测试

- **ResultAnalyzer**:
  - 交易记录分析
  - 收益归因分析
  - 风险评估

- **Visualization**:
  - 资产净值曲线
  - 回撤分析图
  - 交易信号标注
  - 绩效指标仪表盘

#### 3.2.4 AI模块 (高级功能)
| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `calculation/ai/` | ❌ 不存在 | P3 | AI增强模块 |

**需要创建的文件**:
- `ml_models/`: 机器学习模型(随机森林、LightGBM等)
- `dl_models/`: 深度学习模型(LSTM、Transformer等)
- `quantum_models/`: 量子计算模型(量子优化、量子机器学习)
- `feature_selector.py`: 特征重要性分析与筛选

### 3.3 服务层缺失功能

#### 3.3.1 API模块
| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `dependencies.py` | ❌ 空 | P1 | API依赖注入 |
| `strategy_api.py` | ❌ 不存在 | P0 | 策略推荐API |
| `backtest_api.py` | ❌ 不存在 | P0 | 回测结果API |
| `user_api.py` | ❌ 不存在 | P2 | 用户相关API |

**需要实现的API端点**:

**strategy_api.py**:
```python
GET  /api/v1/strategy/recommendations    # 获取策略推荐
POST /api/v1/strategy/screen             # 股票筛选
GET  /api/v1/strategy/signals/{symbol}   # 获取交易信号
POST /api/v1/strategy/backtest           # 执行策略回测
```

**backtest_api.py**:
```python
POST /api/v1/backtest/create             # 创建回测任务
GET  /api/v1/backtest/{task_id}          # 获取回测结果
GET  /api/v1/backtest/{task_id}/trades   # 获取交易记录
GET  /api/v1/backtest/{task_id}/metrics  # 获取绩效指标
```

**user_api.py**:
```python
POST /api/v1/user/register               # 用户注册
POST /api/v1/user/login                  # 用户登录
GET  /api/v1/user/profile                # 获取用户信息
PUT  /api/v1/user/profile                # 更新用户信息
GET  /api/v1/user/watchlist              # 获取自选股
POST /api/v1/user/watchlist              # 添加自选股
```

#### 3.3.2 任务调度模块
| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `service/tasks/` | ❌ 空 | P1 | 异步任务 |

**需要创建的文件**:
- `data_tasks.py`: 数据更新任务(每日行情、历史数据)
- `strategy_tasks.py`: 策略筛选任务(每日推荐、策略回测)
- `notification_tasks.py`: 通知任务(邮件、实时推送)
- `task_scheduler.py`: 任务调度配置(定时任务触发)

**需要实现的任务**:
- 每日收盘后数据更新(15:30-16:30)
- 每日股票筛选和推荐生成
- 策略回测任务
- 定时报告生成和推送

#### 3.3.3 通知模块
| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `service/notification/` | ❌ 不存在 | P2 | 消息通知 |

**需要创建的文件**:
- `email_service.py`: 邮件通知
- `websocket_service.py`: WebSocket实时推送
- `sms_service.py`: 短信通知
- `notification_center.py`: 通知渠道统一管理

### 3.4 配置模块缺失功能

| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `dev.py` | ❌ 不存在 | P0 | 开发环境配置 |
| `prod.py` | ❌ 不存在 | P0 | 生产环境配置 |
| `test.py` | ❌ 不存在 | P0 | 测试环境配置 |

**需要配置的内容**:
- 数据库连接信息
- API密钥和Token
- 日志级别和路径
- 任务调度配置
- 缓存配置
- CORS设置

### 3.5 前端缺失功能

#### 3.5.1 组件模块
| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `frontend/src/components/` | ❌ 空 | P0 | 通用组件 |
| `frontend/src/pages/` | ❌ 空 | P0 | 页面组件 |

**需要实现的组件**:

**通用组件** (components/):
- StockCard: 股票卡片
- KLineChart: K线图
- IndicatorChart: 技术指标图
- StockList: 股票列表
- FilterPanel: 筛选面板
- BacktestReport: 回测报告
- RecommendationCard: 推荐卡片

**页面组件** (pages/):
- HomePage: 首页
- DailyRecommendations: 每日推荐
- StockDetail: 股票详情
- BacktestPage: 回测页面
- StrategyPage: 策略页面
- AnalysisPage: 分析页面
- UserProfile: 用户中心

#### 3.5.2 其他模块
| 目录/文件 | 状态 | 优先级 | 说明 |
|----------|------|--------|------|
| `src/api/` | ❌ 不存在 | P0 | API请求封装 |
| `src/store/` | ❌ 不存在 | P1 | 状态管理 |
| `src/utils/` | ❌ 不存在 | P1 | 工具函数 |
| `tsconfig.json` | ❌ 不存在 | P0 | TypeScript配置 |

### 3.6 测试缺失功能

| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `tests/unit/` | ❌ 不存在 | P1 | 单元测试 |
| `tests/integration/` | ❌ 不存在 | P1 | 集成测试 |
| `tests/e2e/` | ❌ 不存在 | P2 | 端到端测试 |
| `tests/fixtures/` | ❌ 不存在 | P1 | 测试数据 |

**需要测试的内容**:
- 指标计算单元测试
- 策略逻辑单元测试
- 回测引擎单元测试
- API集成测试
- 数据流程端到端测试

### 3.7 基础设施缺失功能

#### 3.7.1 容器化部署
| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `infrastructure/docker/` | ❌ 不存在 | P1 | Docker配置 |

**需要创建的文件**:
- `Dockerfile.backend`: 后端服务镜像
- `Dockerfile.frontend`: 前端应用镜像
- `docker-compose.yml`: 本地开发环境编排

#### 3.7.2 Kubernetes部署
| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `infrastructure/k8s/` | ❌ 不存在 | P2 | Kubernetes配置 |

**需要创建的文件**:
- `deployment.yaml`: 部署配置
- `service.yaml`: 服务暴露配置
- `ingress.yaml`: 入口路由配置
- `configmap.yaml`: 配置映射

#### 3.7.3 监控配置
| 目录 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `infrastructure/monitoring/` | ❌ 不存在 | P2 | 监控配置 |

**需要创建的文件**:
- `prometheus.yml`: Prometheus监控配置
- `grafana_dashboards/`: Grafana仪表盘配置

### 3.8 辅助脚本缺失功能

| 文件 | 状态 | 优先级 | 说明 |
|------|------|--------|------|
| `scripts/init_db.py` | ❌ 不存在 | P1 | 数据库初始化 |
| `scripts/sync_historical_data.py` | ❌ 不存在 | P1 | 历史数据同步 |
| `scripts/validate_strategies.py` | ❌ 不存在 | P2 | 策略有效性验证 |
| `scripts/deploy.sh` | ❌ 不存在 | P2 | 部署脚本 |

---

## 4. 优先级划分

### 4.1 优先级定义
- **P0 (紧急)**: 核心功能,必须在第一阶段完成
- **P1 (高)**: 重要功能,在第二阶段完成
- **P2 (中)**: 增强功能,在第三阶段完成
- **P3 (低)**: 可选功能,后续迭代完成

### 4.2 功能优先级矩阵

#### 第一阶段 (MVP - 最小可行产品)
**目标**: 实现基础的数据获取、指标计算、策略筛选和回测功能

| 模块 | 功能 | 优先级 | 预计工作量 |
|------|------|--------|------------|
| 配置 | 环境配置文件 | P0 | 2天 |
| 指标 | 动量类指标 | P0 | 3天 |
| 指标 | 量能类指标 | P1 | 2天 |
| 策略 | 突破策略 | P1 | 2天 |
| 策略 | 反弹策略 | P1 | 2天 |
| 回测 | 普通回测实现 | P0 | 5天 |
| 回测 | 回测引擎 | P0 | 4天 |
| 回测 | 结果分析 | P1 | 3天 |
| 回测 | 可视化 | P1 | 3天 |
| API | 策略API | P0 | 3天 |
| API | 回测API | P0 | 3天 |
| API | 依赖注入 | P1 | 2天 |
| 数据处理 | 数据清洗 | P1 | 2天 |
| 数据处理 | 特征工程 | P1 | 2天 |
| 数据处理 | 数据校验 | P1 | 2天 |
| 存储 | MongoDB存储 | P1 | 3天 |
| 存储 | Redis缓存 | P1 | 3天 |
| 任务 | 数据任务 | P1 | 3天 |
| 任务 | 策略任务 | P1 | 3天 |
| 任务 | 任务调度 | P1 | 2天 |
| 前端 | API封装 | P0 | 2天 |
| 前端 | 通用组件 | P0 | 10天 |
| 前端 | 页面组件 | P0 | 15天 |
| 测试 | 单元测试 | P1 | 10天 |
| 测试 | 集成测试 | P1 | 5天 |

**第一阶段总计**: 约90-100天

#### 第二阶段 (功能完善)
**目标**: 完善高级功能,提升用户体验

| 模块 | 功能 | 优先级 | 预计工作量 |
|------|------|--------|------------|
| 爬虫 | Tushare爬虫 | P1 | 3天 |
| 爬虫 | WebSocket连接 | P2 | 5天 |
| 存储 | Parquet归档 | P2 | 3天 |
| 通知 | 邮件服务 | P2 | 3天 |
| 通知 | WebSocket服务 | P2 | 4天 |
| 通知 | 通知中心 | P2 | 3天 |
| API | 用户API | P2 | 5天 |
| 前端 | 状态管理 | P1 | 5天 |
| 前端 | 工具函数 | P1 | 3天 |
| 测试 | 端到端测试 | P2 | 8天 |
| 基础设施 | Docker配置 | P1 | 5天 |
| 基础设施 | 脚本工具 | P2 | 5天 |

**第二阶段总计**: 约60-70天

#### 第三阶段 (生产部署)
**目标**: 部署上线,性能优化

| 模块 | 功能 | 优先级 | 预计工作量 |
|------|------|--------|------------|
| AI | 机器学习模型 | P3 | 20天 |
| AI | 深度学习模型 | P3 | 20天 |
| AI | 量子模型 | P3 | 15天 |
| 基础设施 | K8s配置 | P2 | 10天 |
| 基础设施 | 监控配置 | P2 | 8天 |
| 通知 | 短信服务 | P2 | 3天 |

**第三阶段总计**: 约75天

---

## 5. 实施路线图

### 5.1 总体时间规划

```
┌─────────────────────────────────────────────────────────────────┐
│                    sadviser 开发时间线                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  第一阶段 (MVP)          第二阶段 (完善)       第三阶段 (高级)    │
│  ┌──────────────┐       ┌──────────────┐      ┌──────────────┐  │
│  │  0 - 100天   │       │  100-170天   │      │  170-245天   │  │
│  │  核心功能    │       │  功能完善    │      │  高级功能    │  │
│  └──────────────┘       └──────────────┘      └──────────────┘  │
│        │                       │                      │         │
│        ▼                       ▼                      ▼         │
│   ┌─────────┐           ┌─────────┐           ┌─────────┐      │
│   │ 基础功能 │           │ 增强功能 │           │ AI增强  │      │
│   │ 指标计算 │           │ 实时数据 │           │ 智能推荐 │      │
│   │ 策略筛选 │           │ 通知推送 │           │ 量子计算 │      │
│   │ 回测引擎 │           │ 用户管理 │           │ 监控运维 │      │
│   │ API服务  │           │ 性能优化 │           │          │      │
│   │ 前端界面 │           │          │           │          │      │
│   └─────────┘           └─────────┘           └─────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 第一阶段详细计划 (Week 1-14)

#### Week 1-2: 基础配置和指标完善
- [ ] 配置开发/测试/生产环境
- [ ] 实现动量类指标(RSI, KDJ, CCI, WR, MOM)
- [ ] 实现量能类指标(OBV, VOL, VR, EMV)
- [ ] 编写指标单元测试

#### Week 3-4: 策略扩展
- [ ] 实现突破策略
- [ ] 实现反弹策略
- [ ] 完善策略组合器
- [ ] 编写策略单元测试

#### Week 5-7: 回测系统
- [ ] 实现普通回测引擎
- [ ] 实现交易执行逻辑
- [ ] 实现绩效指标计算
- [ ] 实现回测结果分析
- [ ] 实现回测可视化
- [ ] 编写回测测试

#### Week 8-9: API服务
- [ ] 实现策略API
- [ ] 实现回测API
- [ ] 实现依赖注入
- [ ] API集成测试

#### Week 10-11: 数据处理和存储
- [ ] 实现数据清洗器
- [ ] 实现特征工程
- [ ] 实现数据校验器
- [ ] 实现MongoDB存储
- [ ] 实现Redis缓存

#### Week 12-13: 任务调度
- [ ] 实现数据更新任务
- [ ] 实现策略筛选任务
- [ ] 实现任务调度器
- [ ] 集成Celery

#### Week 14: 前端基础
- [ ] API请求封装
- [ ] 实现通用组件库
- [ ] 开始页面组件开发

### 5.3 第二阶段详细计划 (Week 15-24)

#### Week 15-17: 数据源扩展
- [ ] 实现Tushare爬虫
- [ ] 集成多个数据源
- [ ] 实现数据源切换机制
- [ ] WebSocket实时连接

#### Week 18-19: 通知系统
- [ ] 实现邮件通知服务
- [ ] 实现WebSocket推送
- [ ] 实现通知中心
- [ ] 集成通知任务

#### Week 20-21: 用户管理
- [ ] 实现用户API
- [ ] 实现用户认证
- [ ] 实现权限管理
- [ ] 实现自选股功能

#### Week 22-23: 前端完善
- [ ] 完成所有页面组件
- [ ] 实现状态管理
- [ ] 实现工具函数库
- [ ] 前端端到端测试

#### Week 24: 容器化部署
- [ ] 编写Dockerfile
- [ ] 配置docker-compose
- [ ] 本地容器化测试
- [ ] 编写部署脚本

### 5.4 第三阶段详细计划 (Week 25-35)

#### Week 25-29: AI增强(可选)
- [ ] 实现特征选择器
- [ ] 实现机器学习模型
- [ ] 实现深度学习模型
- [ ] 实现量子计算模型(可选)

#### Week 30-32: 生产部署
- [ ] Kubernetes配置
- [ ] 监控系统配置
- [ ] 日志聚合系统
- [ ] 性能优化

#### Week 33-35: 上线和维护
- [ ] 灰度发布
- [ ] 性能监控
- [ ] 用户反馈收集
- [ ] 迭代优化

---

## 6. 详细开发任务

### 6.1 立即开始的任务 (本周)

#### 任务1: 完善配置文件 ⏰ 2天

**文件**: `config/dev.py`, `config/prod.py`, `config/test.py`

**内容**:
```python
# config/dev.py
from .base import *

DEBUG = True
DATABASE_URL = "postgresql://user:pass@localhost:5432/sadviser_dev"
REDIS_URL = "redis://localhost:6379/0"
LOG_LEVEL = "DEBUG"
CORS_ORIGINS = ["http://localhost:5173"]

# config/prod.py
from .base import *

DEBUG = False
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
LOG_LEVEL = "INFO"
CORS_ORIGINS = ["https://your-domain.com"]

# config/test.py
from .base import *

DEBUG = True
DATABASE_URL = "postgresql://user:pass@localhost:5432/sadviser_test"
REDIS_URL = "redis://localhost:6379/1"
LOG_LEVEL = "DEBUG"
CORS_ORIGINS = ["*"]
```

#### 任务2: 实现动量类指标 ⏰ 3天

**文件**: `calculation/indicators/momentum_indicators.py`

**需要实现的指标**:
1. **RSI (相对强弱指标)**
   ```python
   class RSI(BaseIndicator):
       def __init__(self, period: int = 14):
           super().__init__(
               name="RSI",
               params={"period": period}
           )

       def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
           # RSI计算逻辑
           pass
   ```

2. **KDJ (随机指标)**
3. **CCI (顺势指标)**
4. **WR (威廉指标)**
5. **MOM (动量指标)**

**测试要求**:
- 单元测试覆盖所有指标
- 与TA-Lib结果对比验证精度
- 边界条件测试

#### 任务3: 实现普通回测 ⏰ 5天

**文件**: `calculation/backtest/normal_backtest.py`

**核心功能**:
```python
class NormalBacktest(BaseBacktest):
    def run(self):
        """执行回测"""
        # 1. 初始化
        # 2. 遍历历史数据
        # 3. 生成交易信号
        # 4. 执行交易
        # 5. 计算绩效
        pass

    def _execute_trade(self, signal, price, date):
        """执行交易"""
        # 计算交易成本和滑点
        # 更新持仓和资金
        pass

    def _check_risk_control(self):
        """检查风险控制"""
        # 止损检查
        # 止盈检查
        pass
```

#### 任务4: 实现策略API ⏰ 3天

**文件**: `service/api/v1/strategy_api.py`

**API端点**:
```python
@router.get("/recommendations")
async def get_recommendations(
    date: str = None,
    limit: int = 50
):
    """获取每日推荐股票"""
    pass

@router.post("/screen")
async def screen_stocks(request: ScreenRequest):
    """股票筛选"""
    pass

@router.get("/signals/{symbol}")
async def get_signals(symbol: str):
    """获取交易信号"""
    pass

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """执行策略回测"""
    pass
```

#### 任务5: 实现前端基础组件 ⏰ 5天

**文件**: `frontend/src/components/StockCard.jsx`

**组件结构**:
```jsx
function StockCard({ stock }) {
  return (
    <div className="stock-card">
      <h3>{stock.name}</h3>
      <p>代码: {stock.symbol}</p>
      <p>价格: {stock.price}</p>
      <p>涨跌幅: {stock.changePercent}%</p>
      {/* 技术指标展示 */}
      {/* 推荐理由 */}
    </div>
  );
}
```

**其他组件**:
- KLineChart.jsx (使用ECharts)
- StockList.jsx
- FilterPanel.jsx

### 6.2 技术难点和解决方案

#### 难点1: 大规模数据回测性能优化
**问题**: 对全市场5000只股票进行回测,计算量巨大

**解决方案**:
1. 使用并行计算 (multiprocessing/concurrent.futures)
2. 使用向量化计算 (NumPy/Pandas)
3. 使用增量计算,避免重复计算
4. 数据预处理和缓存

**示例代码**:
```python
from concurrent.futures import ProcessPoolExecutor

def parallel_backtest(symbols, strategy):
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_single_backtest, symbol, strategy)
                   for symbol in symbols]
        results = [f.result() for f in futures]
    return results
```

#### 难点2: 实时数据推送延迟
**问题**: WebSocket推送延迟影响用户体验

**解决方案**:
1. 使用Redis Pub/Sub消息队列
2. 数据预计算和缓存
3. 使用二进制协议减少传输量
4. 数据压缩

**架构设计**:
```
数据源 → WebSocket服务 → Redis Pub/Sub → API服务 → 前端
```

#### 难点3: 前端K线图性能优化
**问题**: 大量数据点导致K线图渲染缓慢

**解决方案**:
1. 使用数据抽样 (降采样)
2. 使用Canvas代替SVG
3. 虚拟滚动技术
4. 按需加载数据

**示例代码**:
```javascript
// 数据降采样
function downsampleData(data, threshold) {
  const result = [];
  const bucketSize = Math.floor(data.length / threshold);
  for (let i = 0; i < data.length; i += bucketSize) {
    const bucket = data.slice(i, i + bucketSize);
    const candle = {
      open: bucket[0].open,
      high: Math.max(...bucket.map(d => d.high)),
      low: Math.min(...bucket.map(d => d.low)),
      close: bucket[bucket.length - 1].close
    };
    result.push(candle);
  }
  return result;
}
```

### 6.3 质量保证

#### 代码规范
- 遵循PEP 8 (Python)
- 遵循ESLint + Prettier (JavaScript/React)
- 使用类型提示 (Python 3.10+)
- 编写文档字符串

#### 测试要求
- 单元测试覆盖率 > 80%
- 所有API端点集成测试
- 关键业务流程端到端测试
- 性能测试和压力测试

#### 安全要求
- 输入验证和参数校验
- SQL注入防护
- XSS防护
- CORS配置
- 敏感数据加密
- API速率限制

---

## 7. 里程碑和交付物

### 7.1 第一阶段里程碑 (Week 14)
**交付物**:
- ✅ 完整的技术指标库(趋势+动量+量能)
- ✅ 多种交易策略(趋势+突破+反弹)
- ✅ 完整的回测系统
- ✅ RESTful API服务
- ✅ 基础前端界面
- ✅ 单元测试和集成测试
- ✅ 技术文档

**验收标准**:
- 能够获取股票数据
- 能够计算技术指标
- 能够筛选股票并生成推荐
- 能够执行策略回测并查看结果
- API响应时间 < 500ms
- 前端页面加载时间 < 2s

### 7.2 第二阶段里程碑 (Week 24)
**交付物**:
- ✅ 完整的数据获取系统(多数据源)
- ✅ 实时数据推送
- ✅ 用户管理系统
- ✅ 通知系统
- ✅ 完善的前端应用
- ✅ Docker容器化部署

**验收标准**:
- 支持多个数据源
- 实时数据延迟 < 1s
- 用户注册登录功能正常
- 邮件和推送通知正常
- Docker一键部署

### 7.3 第三阶段里程碑 (Week 35)
**交付物**:
- ✅ AI增强功能(可选)
- ✅ Kubernetes部署配置
- ✅ 监控和日志系统
- ✅ 性能优化报告
- ✅ 用户手册和运维文档

**验收标准**:
- 系统稳定运行 > 99.9%
- API响应时间 < 200ms (P99)
- 支持1000+并发用户
- 完整的监控和告警

---

## 8. 风险评估与应对

### 8.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 数据源不稳定 | 高 | 高 | 多数据源备份,本地缓存 |
| 回测性能不足 | 中 | 中 | 并行计算,增量计算,算法优化 |
| 前端性能问题 | 中 | 中 | 虚拟滚动,数据抽样,懒加载 |
| 第三方API限制 | 中 | 中 | 请求限流,数据缓存,备用方案 |

### 8.2 业务风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 策略有效性不足 | 高 | 高 | 严格回测验证,持续优化 |
| 合规性问题 | 中 | 高 | 咨询法律顾问,明确免责声明 |
| 用户接受度低 | 中 | 中 | 用户调研,快速迭代 |

### 8.3 项目风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 开发进度延期 | 中 | 中 | 敏捷开发,定期评估,灵活调整 |
| 人员变动 | 低 | 高 | 知识文档化,代码规范,结对编程 |
| 需求变更 | 中 | 中 | 需求优先级管理,迭代开发 |

---

## 9. 资源需求

### 9.1 人力资源
- **后端开发**: 2人 (Python/FastAPI)
- **前端开发**: 1人 (React)
- **测试工程师**: 1人 (可兼职)
- **项目经理**: 1人 (可兼职)

### 9.2 技术资源
- **开发环境**:
  - Python 3.10+
  - Node.js 18+
  - PostgreSQL 14+
  - Redis 7+
  - MongoDB 6+

- **云服务** (生产环境):
  - 云服务器 (4核8G起步)
  - 云数据库
  - 对象存储
  - CDN加速

- **第三方服务**:
  - Tushare Pro API
  - 邮件服务 (SendGrid/阿里云)
  - 短信服务 (可选)
  - 监控服务 (可选)

### 9.3 预算估算
- **开发成本**: 约15-20万人民币 (3-4个月)
- **服务器成本**: 约2000-5000元/月
- **API成本**: 约5000-10000元/年
- **其他成本**: 约5000元 (域名、SSL证书等)

---

## 10. 下一步行动

### 立即执行 (本周)
1. **创建配置文件** (2天)
   - config/dev.py
   - config/prod.py
   - config/test.py

2. **实现RSI指标** (1天)
   - 完成RSI指标类
   - 编写单元测试
   - 验证计算精度

3. **搭建前端框架** (2天)
   - 配置TypeScript
   - 创建路由结构
   - 实现基础布局

### 短期目标 (本月)
1. 完成所有动量类指标实现
2. 完成普通回测引擎
3. 实现策略API核心端点
4. 完成前端基础组件库

### 中期目标 (3个月)
1. 完成第一阶段所有功能
2. 通过内测验收
3. 准备上线部署

---

## 附录

### A. 参考资料
- [TA-Lib官方文档](https://ta-lib.org/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [React官方文档](https://react.dev/)
- [ECharts文档](https://echarts.apache.org/)

### B. 术语表
- **技术指标**: 用于分析股票价格和成交量的数学计算
- **回测**: 使用历史数据验证交易策略的过程
- **夏普比率**: 衡量风险调整后收益的指标
- **最大回撤**: 投资组合从峰值到谷底的最大跌幅

### C. 联系方式
- 项目负责人: [姓名]
- 技术支持: [邮箱]
- 问题反馈: [GitHub Issues]

---

**文档结束**

*最后更新: 2026-01-02*
*下次审查: 每周一*
