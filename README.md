# 背景介绍
<a href="./docs/introduction.md">背景介绍</a>


# 项目结构
```
/  # 项目根目录
├── docs/  # 项目文档
│   ├── api/  # API接口文档（自动生成+手动补充）
│   ├── architecture/  # 架构设计图、流程图
│   ├── requirements/  # 需求文档、用例说明
│   └── user_manual/  # 用户操作手册
│
├── config/  # 配置文件目录
│   ├── base.py  # 基础配置（环境变量、通用参数）
│   ├── dev.py  # 开发环境配置
│   ├── prod.py  # 生产环境配置
│   └── test.py  # 测试环境配置
│
├── data/  # 数据相关模块
│   ├── crawler/  # 数据爬取组件
│   │   ├── base_crawler.py  # 爬虫基类
│   │   ├── sina_crawler.py  # 新浪财经数据爬取
│   │   ├── tushare_crawler.py  # Tushare数据爬取
│   │   └── websocket_connector.py  # 实时行情WebSocket连接
│   │
│   ├── storage/  # 数据存储组件
│   │   ├── base_storage.py  # 存储基类
│   │   ├── postgres_storage.py  # PostgreSQL存储
│   │   ├── mongodb_storage.py  # MongoDB存储
│   │   ├── redis_cache.py  # Redis缓存
│   │   └── parquet_archive.py  # Parquet格式历史数据归档
│   │
│   └── processor/  # 数据处理组件
│       ├── data_cleaner.py  # 数据清洗（去重、补全、格式转换）
│       ├── feature_engineering.py  # 特征工程（衍生指标生成）
│       └── data_validator.py  # 数据校验（异常值检测、格式校验）
│
├── calculation/  # 计算核心模块
│   ├── indicators/  # 技术指标计算
│   │   ├── base_indicator.py  # 指标基类
│   │   ├── trend_indicators.py  # 趋势类指标（均线、MACD等）
│   │   ├── momentum_indicators.py  # 动量类指标（RSI、KDJ等）
│   │   ├── volume_indicators.py  # 量能类指标（成交量、OBV等）
│   │   └── custom_indicators.py  # 自定义组合指标
│   │
│   ├── strategies/  # 策略筛选逻辑
│   │   ├── base_strategy.py  # 策略基类
│   │   ├── trend_strategy.py  # 趋势跟踪策略
│   │   ├── breakout_strategy.py  # 突破策略
│   │   ├── rebound_strategy.py  # 反弹策略
│   │   └── strategy_combiner.py  # 多策略组合器
│   │
│   ├── backtest/  # 回测引擎
│   │   ├── backtest_engine.py  # 回测核心逻辑
│   │   ├── performance_metrics.py  # 绩效评估指标（胜率、夏普比率等）
│   │   ├── result_analyzer.py  # 回测结果分析
│   │   └── visualization.py  # 回测结果可视化
│   │
│   └── ai/  # AI增强模块
│       ├── ml_models/  # 机器学习模型（随机森林、LightGBM等）
│       ├── dl_models/  # 深度学习模型（LSTM、Transformer等）
│       ├── quantum_models/  # 量子计算模型（量子优化、量子机器学习）
│       └── feature_selector.py  # 特征重要性分析与筛选
│
├── service/  # 服务层（API与任务）
│   ├── api/  # API接口
│   │   ├── dependencies.py  # 接口依赖（权限、数据校验等）
│   │   ├── v1/  # v1版本接口
│   │   │   ├── stock_api.py  # 股票数据接口
│   │   │   ├── strategy_api.py  # 策略推荐接口
│   │   │   ├── backtest_api.py  # 回测结果接口
│   │   │   └── user_api.py  # 用户相关接口
│   │   └── api_router.py  # API路由汇总
│   │
│   ├── tasks/  # 异步任务
│   │   ├── data_tasks.py  # 数据更新任务（每日行情、历史数据）
│   │   ├── strategy_tasks.py  # 策略筛选任务（每日推荐、策略回测）
│   │   ├── notification_tasks.py  # 通知任务（邮件、实时推送）
│   │   └── task_scheduler.py  # 任务调度配置（定时任务触发）
│   │
│   └── notification/  # 消息通知
│       ├── email_service.py  # 邮件通知
│       ├── websocket_service.py  # WebSocket实时推送
│       ├── sms_service.py  # 短信通知
│       └── notification_center.py  # 通知渠道统一管理
│
├── frontend/  # 前端应用
│   ├── public/  # 静态资源（图片、图标等）
│   ├── src/
│   │   ├── api/  # API请求封装
│   │   ├── components/  # 通用组件（股票列表、K线图等）
│   │   ├── pages/  # 页面组件（首页、推荐列表、详情页等）
│   │   ├── store/  # 状态管理（Redux/Context）
│   │   ├── utils/  # 工具函数（格式化、验证等）
│   │   ├── App.tsx  # 根组件
│   │   └── index.tsx  # 入口文件
│   ├── package.json  # 依赖配置
│   └── tsconfig.json  # TypeScript配置
│
├── infrastructure/  # 基础设施（部署与运维）
│   ├── docker/  # Docker配置
│   │   ├── Dockerfile.backend  # 后端服务镜像
│   │   ├── Dockerfile.frontend  # 前端应用镜像
│   │   └── docker-compose.yml  # 本地开发环境编排
│   │
│   ├── k8s/  # Kubernetes配置
│   │   ├── deployment.yaml  # 部署配置
│   │   ├── service.yaml  # 服务暴露配置
│   │   ├── ingress.yaml  # 入口路由配置
│   │   └── configmap.yaml  # 配置映射
│   │
│   └── monitoring/  # 监控配置
│       ├── prometheus.yml  # Prometheus监控配置
│       └── grafana_dashboards/  # Grafana仪表盘配置
│
├── tests/  # 测试目录
│   ├── unit/  # 单元测试（指标计算、策略逻辑等）
│   ├── integration/  # 集成测试（API调用、数据流程等）
│   ├── e2e/  # 端到端测试（用户操作流程）
│   └── fixtures/  # 测试数据与环境
│
├── scripts/  # 辅助脚本
│   ├── init_db.py  # 数据库初始化
│   ├── sync_historical_data.py  # 历史数据同步
│   ├── validate_strategies.py  # 策略有效性验证
│   └── deploy.sh  # 部署脚本
│
├── .github/  # CI/CD配置（GitHub Actions）
│   └── workflows/
│       ├── test.yml  # 测试流程
│       └── deploy.yml  # 部署流程
│
├── requirements/  # 依赖管理
│   ├── base.txt  # 基础依赖
│   ├── dev.txt  # 开发环境依赖
│   └── prod.txt  # 生产环境依赖
│
├── .env.example  # 环境变量示例
├── .gitignore  # Git忽略文件配置
├── README.md  # 项目说明
└── main.py  # 后端服务入口
```