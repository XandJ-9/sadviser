# sadviser 测试文档

## 概述

本目录包含sadviser股票投资建议平台的所有测试代码。测试覆盖了已完成实现的核心功能模块。

## 测试结构

```
tests/
├── conftest.py                  # pytest配置和共享fixtures
├── test_simple_logging.py       # 日志系统测试
├── test_sina_stock.py          # 新浪爬虫测试
├── test_postgres_storage.py    # PostgreSQL存储测试
├── test_trend_indicators.py    # 技术指标测试
├── test_strategies.py          # 交易策略测试
├── test_backtest.py            # 回测功能测试
└── fixtures/                   # 测试数据目录(待创建)
```

## 测试覆盖的模块

### 1. 数据层测试

#### test_postgres_storage.py
- ✅ 连接管理
- ✅ CRUD操作(插入、查询、更新、删除)
- ✅ 批量操作
- ✅ DataFrame查询
- ✅ 错误处理
- ✅ 性能测试

**测试类**:
- `TestPostgreSQLStorage` - 基本功能测试
- `TestPostgreSQLStorageErrorHandling` - 错误处理测试
- `TestPostgreSQLStoragePerformance` - 性能测试

### 2. 计算层测试

#### test_trend_indicators.py
- ✅ 移动平均线(SMA, EMA, WMA, DEMA, TEMA)
- ✅ MACD指标
- ✅ 布林带指标
- ✅ 指标组合器
- ✅ 参数验证
- ✅ 计算准确性验证

**测试类**:
- `TestMovingAverage` - 移动平均线测试
- `TestMACD` - MACD指标测试
- `TestBollingerBands` - 布林带测试
- `TestIndicatorCombiner` - 指标组合器测试

#### test_strategies.py
- ✅ 均线交叉策略
- ✅ MACD策略
- ✅ 布林带策略
- ✅ 策略组合器(多数投票、加权平均、共识法)
- ✅ 绩效评估
- ✅ 策略集成测试

**测试类**:
- `TestMovingAverageCrossStrategy` - 均线交叉策略测试
- `TestMACDStrategy` - MACD策略测试
- `TestBollingerBandStrategy` - 布林带策略测试
- `TestStrategyEvaluation` - 绩效评估测试
- `TestStrategyCombiner` - 策略组合器测试
- `TestStrategyIntegration` - 集成测试
- `TestStrategyErrorHandling` - 错误处理测试

#### test_backtest.py
- ✅ 数据验证
- ✅ 交易成本计算
- ✅ 绩效指标计算(夏普比率、最大回撤、胜率等)
- ✅ 风险控制(止损、止盈、头寸管理)
- ✅ 边缘情况处理
- ✅ 性能测试

**测试类**:
- `TestBaseBacktest` - 回测基类测试
- `TestBacktestIntegration` - 集成测试
- `TestBacktestRiskControls` - 风险控制测试
- `TestBacktestEdgeCases` - 边缘情况测试
- `TestBacktestPerformance` - 性能测试
- `TestBacktestOutput` - 输出测试

### 3. 工具层测试

#### test_simple_logging.py
- ✅ 日志配置
- ✅ 彩色输出
- ✅ 文件日志
- ✅ 多级别日志

### 4. 数据爬虫测试

#### test_sina_stock.py
- ✅ 数据获取
- ✅ 数据解析
- ✅ 批量请求

#### test_crawler_sina.py - **新增**
- ✅ 初始化参数测试 (3个测试)
- ✅ 日线数据获取测试 (7个测试)
- ✅ 实时行情获取测试 (7个测试)
- ✅ 批量处理测试 (>400股票)
- ✅ 订单簿数据测试 (买卖盘)
- ✅ 涨跌幅计算测试
- ✅ 辅助方法测试 (2个测试)
- ✅ 参数验证测试 (6个参数化测试)

**总计**: 26个测试, 通过率 ~88%

#### test_crawler_tushare.py - **新增**
- ✅ 初始化和Token认证测试 (4个测试)
- ✅ 日线数据获取测试 (6个测试)
- ✅ 实时行情获取测试 (4个测试)
- ✅ 股票基本信息测试 (3个测试)
- ✅ POST请求重试测试 (3个测试)
- ✅ 辅助方法测试 (2个测试)
- ✅ 参数化测试 (7个测试)

**总计**: 29个测试, 通过率 ~93%

#### test_crawler_websocket.py - **新增**
- ✅ 连接管理测试
- ✅ 订阅/取消订阅测试
- ✅ 自动重连机制测试
- ✅ 回调函数系统测试
- ✅ 消息接收和解析测试
- ⚠️ 状态: 存在语法错误需要修复

**总计**: ~30个测试

## 环境配置

### 依赖安装

```bash
# 安装测试依赖
uv sync --extra test

# 或使用pip
pip install pytest pytest-asyncio pytest-cov
```

### 配置测试数据库

测试使用PostgreSQL数据库,需要先创建测试数据库:

```bash
# 创建测试数据库
createdb sadviser_test

# 或使用psql
psql -U postgres -c "CREATE DATABASE sadviser_test;"
```

### 环境变量

创建 `.env.test` 文件:

```bash
TEST_DATABASE_HOST=localhost
TEST_DATABASE_PORT=5432
TEST_DATABASE_NAME=sadviser_test
TEST_DATABASE_USER=your_user
TEST_DATABASE_PASSWORD=your_password
```

## 运行测试

### 运行所有测试

```bash
# 使用uv
uv run pytest

# 或直接使用pytest
pytest
```

### 运行特定测试文件

```bash
# 测试PostgreSQL存储
pytest tests/test_postgres_storage.py -v

# 测试技术指标
pytest tests/test_trend_indicators.py -v

# 测试交易策略
pytest tests/test_strategies.py -v

# 测试回测功能
pytest tests/test_backtest.py -v
```

### 运行特定测试类或方法

```bash
# 运行特定测试类
pytest tests/test_trend_indicators.py::TestMovingAverage -v

# 运行特定测试方法
pytest tests/test_trend_indicators.py::TestMovingAverage::test_ma_init -v
```

### 生成测试覆盖率报告

```bash
# 生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term

# 查看HTML报告
open htmlcov/index.html
```

### 并行运行测试(加速)

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 使用多进程运行
pytest -n auto
```

## 测试Fixtures

### conftest.py中提供的共享fixtures

#### 数据Fixtures
- `sample_ohlcv_data` - 生成示例OHLCV数据(100天)
- `sample_stock_list` - 示例股票列表
- `valid_ohlcv_data` - 有效的OHLCV数据
- `invalid_ohlcv_data_missing_columns` - 缺失列的数据
- `invalid_ohlcv_data_nan` - 包含NaN的数据
- `insufficient_data` - 数据量不足的数据

#### 配置Fixtures
- `mock_storage_config` - 模拟存储配置
- `sample_indicators_params` - 示例指标参数
- `sample_strategy_params` - 示例策略参数
- `backtest_config` - 回测配置

#### 工具Fixtures
- `temp_dir` - 临时目录(自动清理)

### 使用Fixtures示例

```python
def test_indicator_calculation(sample_ohlcv_data):
    """使用sample_ohlcv_data fixture"""
    ma = MovingAverage(period=20)
    result = ma.calculate(sample_ohlcv_data)
    assert 'sma_20' in result.columns
```

## 测试最佳实践

### 1. 编写测试的原则

- **独立性**: 每个测试应该独立运行,不依赖其他测试
- **可重复性**: 测试结果应该可重复,不受环境影响
- **快速性**: 单元测试应该快速执行
- **清晰性**: 测试名称和断言应该清晰易懂

### 2. 测试命名规范

```python
# 测试类名: Test + 模块名
class TestMovingAverage:
    pass

# 测试方法名: test + 被测功能 + 场景
def test_ma_calculate_with_valid_data():
    pass

def test_ma_calculate_with_insufficient_data():
    pass

def test_ma_init_with_invalid_period():
    pass
```

### 3. 使用参数化测试

```python
@pytest.mark.parametrize("ma_type", ['sma', 'ema', 'wma'])
def test_ma_with_different_types(ma_type):
    ma = MovingAverage(period=20, ma_type=ma_type)
    # 测试逻辑
```

### 4. 异步测试

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 5. Mock外部依赖

```python
from unittest.mock import patch, AsyncMock

@patch('asyncpg.create_pool', new_callable=AsyncMock)
async def test_with_mock(mock_pool):
    # 使用mock对象
    pass
```

## 测试覆盖率目标

| 模块 | 测试数量 | 当前覆盖率 | 目标覆盖率 | 状态 |
|------|---------|------------|------------|------|
| 数据层-Crawler | 85+ | 70% | 85% | ✅ 良好 |
| 数据层-Storage | 30+ | 75% | 85% | ✅ 良好 |
| 计算层-指标 | 40+ | 70% | 90% | ✅ 良好 |
| 计算层-策略 | 50+ | 65% | 85% | ✅ 良好 |
| 计算层-回测 | 40+ | 50% | 80% | ⚠️ 待提升 |
| 工具层 | 5+ | 80% | 90% | ✅ 优秀 |
| **总计** | **250+** | **约65%** | **85%** | **持续改进** |

### Crawler测试详情

| Crawler类型 | 测试文件 | 测试数 | 通过率 | 状态 |
|------------|---------|--------|--------|------|
| SinaCrawler | test_crawler_sina.py | 26 | 88% | ✅ |
| TushareCrawler | test_crawler_tushare.py | 29 | 93% | ✅ |
| WebSocketConnector | test_crawler_websocket.py | ~30 | - | ⚠️ 需修复 |
| **小计** | - | **85+** | **~90%** | **大部分通过** |

**详细文档**: [Data_Crawler测试总结.md](../docs/测试文档/Data_Crawler测试总结.md)

## 持续集成

### GitHub Actions配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install uv
        uv sync

    - name: Run tests
      run: |
        uv run pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 常见问题

### Q: 测试失败,提示数据库连接错误

**A**: 确保PostgreSQL服务正在运行,并且测试数据库已创建:

```bash
# 检查PostgreSQL状态
pg_ctl status

# 创建测试数据库
createdb sadviser_test
```

### Q: 测试失败,提示缺少ta-lib

**A**: 安装TA-Lib库:

```bash
# macOS
brew install ta-lib

# Linux
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 然后安装Python包
pip install ta-lib
```

### Q: 异步测试失败

**A**: 确保安装了pytest-asyncio:

```bash
pip install pytest-asyncio
```

### Q: 如何调试失败的测试?

**A**: 使用pytest的调试功能:

```bash
# 显示详细输出
pytest -v -s tests/test_foo.py

# 进入调试器
pytest --pdb tests/test_foo.py

# 只运行失败的测试
pytest --lf
```

## 贡献指南

### 添加新测试

1. 在相应的测试文件中添加测试类或测试方法
2. 使用清晰的测试名称和文档字符串
3. 确保测试独立且可重复
4. 更新此README文档

### 测试审查清单

- [ ] 测试名称清晰描述测试内容
- [ ] 测试独立且可重复
- [ ] 使用适当的fixtures
- [ ] 包含正常情况和边缘情况
- [ ] 包含错误处理测试
- [ ] 有清晰的断言和错误消息
- [ ] 测试运行快速(<1秒)

## 下一步计划

### 待添加的测试

- [x] ~~WebSocket连接测试~~ (已完成,需修复语法错误)
- [ ] MongoDB存储测试
- [ ] Redis缓存测试
- [ ] API端点集成测试
- [ ] 前端组件测试
- [ ] 端到端测试

### 待修复的测试

- [ ] test_crawler_websocket.py - 修复async with patch语法错误
- [ ] test_crawler_sina.py - 修复3个失败的测试
- [ ] test_crawler_tushare.py - 修复2个失败的测试

### 测试改进

- [x] ~~提高测试覆盖率到65%+~~ (已达到)
- [ ] 提高测试覆盖率到85%+
- [ ] 添加性能基准测试
- [ ] 添加模糊测试
- [ ] 实现测试数据工厂
- [ ] 添加可视化测试报告
- [ ] 设置CI/CD测试管道

## 资源链接

- [pytest文档](https://docs.pytest.org/)
- [pytest-asyncio文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [Python测试最佳实践](https://docs.python-guide.org/writing/tests/)

---

**最后更新**: 2026-01-02
**维护者**: sadviser开发团队
