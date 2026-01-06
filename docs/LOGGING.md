# 统一日志格式规范

## 概述

项目使用统一的日志格式，确保所有模块的控制台输出保持一致性和可读性。

## 日志格式

### 控制台格式

控制台日志采用简洁、颜色化的格式，便于快速识别和定位问题。

```
HH:MM:SS [LEVEL] ModuleName - Message
```

**示例**：
```
22:26:46 [INFO ] StockService - 获取股票列表: limit=50
22:26:46 [ERROR] StockRepository - 数据库连接失败
22:26:46 [WARN ] stock_api - 请求参数无效: limit=-1
```

**组成部分**：
1. **时间戳** (`HH:MM:SS`): 只显示时分秒，精确到秒
2. **日志级别** (`[LEVEL]`): 带颜色和固定宽度
   - `DEBUG` - 青色
   - `INFO ` - 绿色
   - `WARN ` - 黄色
   - `ERROR` - 红色
   - `CRIT ` - 红底白字
3. **模块名** (`ModuleName`): 自动提取最后部分
   - `service.api.v1.stock_api` → `stock_api`
   - `StockService` → `StockService`
4. **消息** (`Message`): 实际的日志内容

### 文件格式

文件日志采用详细的格式，包含完整的调试信息。

```
YYYY-MM-DD HH:MM:SS - LEVEL - module.py:line - function() - Message
```

**示例**：
```
2025-01-06 22:26:46 - INFO - stock_service.py:123 - get_stock_list() - 获取股票列表成功
2025-01-06 22:26:46 - ERROR - stock_repository.py:45 - _query() - 数据库连接失败
```

**组成部分**：
1. **完整时间戳** (`YYYY-MM-DD HH:MM:SS`): 包含日期和时间
2. **日志级别** (`LEVEL`): 5字符宽度，左对齐
3. **文件位置** (`module.py:line`): 文件名和行号
4. **函数名** (`function()`): 调用日志的函数
5. **消息** (`Message`): 日志内容

## 颜色方案

| 级别 | 颜色 | 用途 |
|------|------|------|
| DEBUG | 青色 | 调试信息，开发时使用 |
| INFO | 绿色 | 一般信息，正常流程 |
| WARNING | 黄色 | 警告信息，需要关注 |
| ERROR | 红色 | 错误信息，需要处理 |
| CRITICAL | 红底白字 | 严重错误，系统级问题 |

## 使用方法

### 创建日志器

```python
from utils.custom_logger import CustomLogger
import logging

# 创建日志器（只输出到控制台）
logger = CustomLogger(
    name="ModuleName",
    log_level=logging.INFO
)

# 创建日志器（同时输出到文件）
logger = CustomLogger(
    name="ModuleName",
    log_level=logging.INFO,
    log_dir="logs",           # 日志目录
    enable_file=True          # 启用文件日志
)
```

### 记录日志

```python
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 格式化消息

```python
# 使用 f-string
symbol = "000001"
logger.info(f"获取股票详情: symbol={symbol}")

# 格式化参数
limit = 50
offset = 0
logger.info(f"获取股票列表: limit={limit}, offset={offset}")

# 异常信息
try:
    result = await api_call()
except Exception as e:
    logger.error(f"请求失败: {e}")
```

## 最佳实践

### 1. 选择合适的日志级别

```python
# DEBUG - 详细的调试信息
logger.debug(f"处理数据: data={data}")

# INFO - 重要的流程信息
logger.info("处理用户请求: GET /api/v1/stocks")
logger.info("股票列表获取成功: count=50")

# WARNING - 潜在问题
logger.warning("使用默认配置: config_file not found")
logger.warning("缓存未命中，从数据库获取")

# ERROR - 错误但可恢复
logger.error(f"数据库查询失败: {e}")
logger.error(f"API调用失败: status={status_code}")

# CRITICAL - 严重错误，可能影响系统运行
logger.critical("数据库连接池耗尽")
logger.critical("磁盘空间不足")
```

### 2. 日志消息要清晰

```python
# ❌ 不好 - 不清楚发生了什么
logger.info("done")
logger.error("error")

# ✅ 好 - 清楚描述发生了什么
logger.info("股票列表获取成功: count=50, duration=123ms")
logger.error(f"数据库连接失败: host={host}, port={port}, error={e}")
```

### 3. 包含关键信息

```python
# ✅ 包含关键参数
logger.info(f"获取股票列表: limit={limit}, offset={offset}")
logger.info(f"股票详情: symbol={symbol}, price={price}")
logger.error(f"查询失败: sql={sql}, error={e}")

# ✅ 包含性能信息
import time
start = time.time()
result = await process()
duration = (time.time() - start) * 1000
logger.info(f"处理完成: count={len(result)}, duration={duration:.2f}ms")
```

### 4. 模块命名规范

```python
# API 层 - 使用小写
CustomLogger(name="stock_api")
CustomLogger(name="strategy_api")

# Service 层 - 使用类名
CustomLogger(name="StockService")
CustomLogger(name="StrategyService")

# Repository 层 - 使用类名
CustomLogger(name="StockRepository")
CustomLogger(name="UserRepository")

# Core 层 - 使用类名
CustomLogger(name="Container")
```

### 5. 避免过度日志

```python
# ❌ 不好 - 循环中打印每条记录
for item in items:
    logger.info(f"处理: {item}")  # 会产生大量日志

# ✅ 好 - 只打印汇总信息
logger.info(f"开始处理: total={len(items)}")
for item in items:
    process(item)
logger.info(f"处理完成: success={success_count}, failed={failed_count}")
```

## 文件日志配置

### 按级别分离

```python
logger = CustomLogger(
    name="MyModule",
    log_dir="logs",
    separate_levels=True  # 不同级别写入不同文件
)

# 生成文件：
# - 20250106_MyModule_debug.log
# - 20250106_MyModule_info.log
# - 20250106_MyModule_warning.log
# - 20250106_MyModule_error.log
# - 20250106_MyModule_critical.log
```

### 合并到一个文件

```python
logger = CustomLogger(
    name="MyModule",
    log_dir="logs",
    separate_levels=False  # 所有级别写入同一文件
)

# 生成文件：
# - 20250106_MyModule.log
```

## 迁移指南

### 从旧版本迁移

如果你使用的是旧版本的 `CustomLogger`，需要做以下调整：

#### 1. 移除 `format_style` 参数

```python
# ❌ 旧版本
logger = CustomLogger(
    name="MyModule",
    format_style="simple"  # 移除这个参数
)

# ✅ 新版本
logger = CustomLogger(
    name="MyModule"
)
```

#### 2. 使用新的日志格式

新版本的格式更简洁：
```
旧格式: 2025-01-06 22:30:45 - stock_api - INFO - 处理请求
新格式: 22:30:45 [INFO ] stock_api - 处理请求
```

#### 3. 模块名自动简化

```python
# 旧版本：显示完整路径
CustomLogger(name="service.api.v1.stock_api")
# 输出: 2025-01-06 22:30:45 - service.api.v1.stock_api - INFO

# 新版本：自动简化
CustomLogger(name="service.api.v1.stock_api")
# 输出: 22:30:45 [INFO ] stock_api -
```

## 示例

### 完整的日志使用示例

```python
from utils.custom_logger import CustomLogger
import logging

class StockService:
    def __init__(self):
        self.logger = CustomLogger(
            name="StockService",
            log_level=logging.INFO
        )

    async def get_stock_list(self, limit: int, offset: int):
        """获取股票列表"""
        self.logger.info(f"获取股票列表: limit={limit}, offset={offset}")

        try:
            # 业务逻辑
            stocks = await self._fetch_stocks(limit, offset)
            self.logger.info(f"获取成功: count={len(stocks)}")
            return stocks

        except Exception as e:
            self.logger.error(f"获取失败: {e}")
            raise

    async def _fetch_stocks(self, limit, offset):
        """内部方法使用 DEBUG 级别"""
        self.logger.debug(f"查询数据库: limit={limit}, offset={offset}")
        # ... 实现代码
```

## 常见问题

### Q1: 如何临时启用 DEBUG 日志？

```python
logger = CustomLogger(
    name="MyModule",
    log_level=logging.DEBUG  # 改为 DEBUG
)
```

### Q2: 如何关闭日志输出？

```python
logger = CustomLogger(
    name="MyModule",
    log_level=logging.CRITICAL + 1  # 设置高于最高级别
)
```

### Q3: 如何同时输出到控制台和文件？

```python
logger = CustomLogger(
    name="MyModule",
    log_dir="logs",       # 设置日志目录
    enable_console=True,   # 启用控制台（默认）
    enable_file=True       # 启用文件
)
```

### Q4: 如何禁用文件日志？

```python
logger = CustomLogger(
    name="MyModule",
    log_dir=None,          # 不设置日志目录
    enable_console=True,
    enable_file=False      # 或不设置 log_dir
)
```

## 总结

统一的日志格式提供了：

✅ **一致性** - 所有模块使用相同的格式
✅ **可读性** - 简洁的控制台格式，易于阅读
✅ **可维护性** - 颜色化输出，快速定位问题
✅ **调试性** - 详细的文件格式，包含完整上下文
✅ **简洁性** - 模块名自动简化，减少冗余

遵循这些规范，可以确保整个项目的日志保持清晰、一致和有用。
