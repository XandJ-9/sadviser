# 测试文档索引

本目录包含sadviser项目的所有测试相关文档。

## 📚 文档目录

### Data模块测试

#### [Data_Crawler测试总结.md](./Data_Crawler测试总结.md)
**模块**: `data/crawler/`

测试数据获取层的完整文档：
- **SinaCrawler测试** (26个测试, 88%通过率)
  - 日线数据获取
  - 实时行情获取
  - 批量处理
  - 订单簿数据
  - 错误处理

- **TushareCrawler测试** (29个测试, 93%通过率)
  - Token认证
  - API接口封装
  - 代码格式转换
  - POST请求重试

- **WebSocketConnector测试** (~30个测试)
  - 连接管理
  - 订阅系统
  - 自动重连
  - 回调机制

**运行测试**:
```bash
PYTHONPATH=. uv run pytest tests/test_crawler_*.py -v
```

---

## 📊 测试统计概览

| 模块 | 测试文件 | 测试数量 | 通过率 | 状态 |
|------|---------|---------|--------|------|
| data/crawler | test_crawler_*.py | 85+ | ~90% | ✅ 良好 |
| calculation/indicators | test_trend_indicators.py | 40+ | ~95% | ✅ 优秀 |
| calculation/strategies | test_strategies.py | 50+ | ~90% | ✅ 良好 |
| calculation/backtest | test_backtest.py | 40+ | ~85% | ✅ 良好 |
| data/storage | test_postgres_storage.py | 30+ | ~90% | ✅ 良好 |

---

## 🧪 测试类型说明

### 单元测试
测试单个函数或方法的功能，不依赖外部系统。

### 集成测试
测试多个模块协作，可能需要数据库或网络。

### 参数化测试
使用多组输入测试同一功能，提高覆盖率。

### 标记说明
- `@pytest.mark.asyncio` - 异步测试
- `@pytest.mark.slow` - 慢速测试(>1秒)
- `@pytest.mark.requires_network` - 需要网络
- `@pytest.mark.requires_db` - 需要数据库

---

## 🚀 快速开始

### 安装测试依赖
```bash
uv sync --extra test
```

### 运行所有测试
```bash
PYTHONPATH=. uv run pytest tests/ -v
```

### 运行特定模块测试
```bash
# Data模块
PYTHONPATH=. uv run pytest tests/test_crawler_*.py -v

# Calculation模块
PYTHONPATH=. uv run pytest tests/test_*_indicators.py -v
PYTHONPATH=. uv run pytest tests/test_strategies.py -v
PYTHONPATH=. uv run pytest tests/test_backtest.py -v

# Storage模块
PYTHONPATH=. uv run pytest tests/test_postgres_storage.py -v
```

### 生成覆盖率报告
```bash
# HTML报告
PYTHONPATH=. uv run pytest tests/ --cov=. --cov-report=html

# 终端报告
PYTHONPATH=. uv run pytest tests/ --cov=. --cov-report=term
```

### 运行特定类型的测试
```bash
# 只运行快速测试
PYTHONPATH=. uv run pytest tests/ -m "not slow"

# 运行网络测试
PYTHONPATH=. uv run pytest tests/ -m requires_network

# 运行异步测试
PYTHONPATH=. uv run pytest tests/ -m asyncio
```

---

## 📖 相关文档

### 项目文档
- [开发计划与实施路线图](../开发计划与实施路线图.md) - 项目整体规划
- [回测模块设计思路与功能说明](../回测模块设计思路与功能说明.md) - 回测系统设计
- [股票投资建议平台：指标计算与策略框架设计思路](../股票投资建议平台：指标计算与策略框架设计思路.md) - 策略框架设计

### 测试相关
- [tests/README.md](../../tests/README.md) - 测试目录说明
- [pytest.ini](../../pytest.ini) - pytest配置文件
- [conftest.py](../../tests/conftest.py) - 测试配置和fixtures

---

## 🛠️ 测试工具

### 主要测试框架
- **pytest**: 测试运行器
- **pytest-asyncio**: 异步测试支持
- **pytest-mock**: Mock和patch支持
- **pytest-cov**: 覆盖率报告
- **pytest-xdist**: 并行测试执行

### Mock工具
- **unittest.mock**: Python标准库mock工具
- **AsyncMock**: 异步函数mock
- **MagicMock**: 通用mock对象

---

## 📝 测试编写规范

### 测试文件命名
```
test_<module_name>.py
例如: test_crawler_sina.py
```

### 测试类命名
```python
class Test<ClassName>:
    例如: class TestSinaCrawler:
```

### 测试方法命名
```python
def test_<feature>_<scenario>():
    例如: def test_fetch_daily_data_success():
```

### 测试文档字符串
```python
def test_feature_scenario():
    """测试功能的特定场景"""
    pass
```

---

## 🔍 测试调试技巧

### 打印调试
```bash
# 显示print输出
pytest tests/ -v -s
```

### 只运行失败的测试
```bash
# 只运行上次失败的测试
pytest tests/ --lf

# 先运行失败的，再运行其他的
pytest tests/ --ff
```

### 停止在第一个失败
```bash
# 遇到失败立即停止
pytest tests/ -x
```

### 详细输出
```bash
# 极详细输出
pytest tests/ -vv

# 显示traceback
pytest tests/ --tb=long
```

### 进入调试器
```bash
# 在失败时进入pdb
pytest tests/ --pdb
```

---

## 📈 持续改进

### 待完成
- [ ] 修复WebSocket测试的语法错误
- [ ] 增加更多的集成测试
- [ ] 添加性能基准测试
- [ ] 完善错误场景测试

### 计划中
- [ ] 添加mutation testing
- [ ] 设置CI/CD测试管道
- [ ] 增加测试覆盖率监控
- [ ] 编写测试最佳实践指南

---

## 💡 贡献指南

### 添加新测试
1. 在对应tests/目录下创建测试文件
2. 使用pytest fixtures复用测试数据
3. 添加适当的测试标记
4. 确保测试独立且可重复运行
5. 更新相关文档

### 测试审查要点
- [ ] 测试名称清晰描述测试内容
- [ ] 使用适当的断言方法
- [ ] 测试覆盖正常和异常情况
- [ ] Mock对象正确清理
- [ ] 异步测试正确使用asyncio标记

---

**文档维护**: 测试文档应随代码更新同步维护
**最后更新**: 2026-01-02
**文档版本**: v1.0
