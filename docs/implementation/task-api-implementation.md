# Task API 实现文档

> **原文档**: [TASK_API_IMPLEMENTATION.md](../TASK_API_IMPLEMENTATION.md)
>
> **更新日期**: 2026-01-06

## 概述

成功创建了 `task_api.py` 来替换旧的 `data_api.py`，实现了完整的数据任务管理系统。

---

## 实现内容

### 1. 创建的文件

#### `service/repositories/task_repository.py`
- **TaskRepository** 类，封装所有任务相关的数据库操作
- 方法：
  - `create_task()` - 创建新任务
  - `get_task()` - 获取单个任务
  - `get_tasks()` - 获取任务列表（支持状态过滤）
  - `update_task()` - 更新任务信息
  - `get_task_stats()` - 获取任务统计
  - `get_recent_tasks()` - 获取最近任务

#### `service/services/task_service.py`
- **TaskService** 类，提供任务相关的业务逻辑
- 方法：
  - `create_task()` - 创建任务（含业务逻辑）
  - `get_task()` - 查询任务
  - `get_tasks()` - 查询任务列表
  - `update_task()` - 更新任务
  - `get_task_stats()` - 获取统计
  - `get_recent_tasks()` - 获取最近任务
  - `get_system_status()` - 获取系统状态

#### `service/api/v1/task_api.py`
- **task_api** 路由，提供所有任务管理的HTTP接口
- 端点：
  - `GET /tasks/stats` - 获取任务统计
  - `GET /tasks/status` - 获取系统状态
  - `GET /tasks/recent` - 获取最近任务
  - `POST /tasks/fetch/history` - 创建历史数据获取任务（后台）
  - `POST /tasks/fetch/realtime` - 获取实时行情
  - `GET /tasks/fetch/stocklist` - 获取股票列表
  - `GET /tasks` - 获取任务列表
  - `POST /tasks` - 创建新任务
  - `GET /tasks/{task_id}` - 获取指定任务

### 2. 更新的文件

#### `service/core/container.py`
- 添加了 TaskRepository 和 TaskService 的管理
- 新增方法：
  - `get_task_repository()` - 获取任务仓库实例
  - `get_task_service()` - 获取任务服务实例

#### `service/api/dependencies.py`
- 添加了 `get_task_service()` 依赖注入函数
- 供 FastAPI 的 Depends 系统使用

#### `service/api/api_router.py`
- 移除了对 `data_api` 的引用
- 添加了对 `task_api` 的引用

#### `service/main.py`
- 移除了对 `data_api` 的导入
- 简化了生命周期管理，使用容器统一管理资源

### 3. 废弃的文件

#### `service/api/v1/data_api.py` → `data_api.py.deprecated`
- 旧的数据管理API已被重命名为 `.deprecated`
- 功能已完全迁移到新的 task_api.py

---

## 架构设计

### 分层架构

```
┌─────────────────────────────────┐
│   task_api.py (FastAPI Routes)  │  ← HTTP接口层
├─────────────────────────────────┤
│  task_service.py (Business)     │  ← 业务逻辑层
├─────────────────────────────────┤
│ task_repository.py (Data Access)│  ← 数据访问层
├─────────────────────────────────┤
│  PostgreSQL Storage             │  ← 存储层
└─────────────────────────────────┘
```

### 依赖注入

使用 FastAPI 的 `Depends()` 系统：

```python
@router.get("/tasks")
async def get_all_tasks(
    service: TaskService = Depends(get_task_service)
):
    ...
```

---

## 路由顺序

按照最佳实践，固定路径在前，参数路径在后：

```
1. GET    /tasks/stats              ← 固定路径
2. GET    /tasks/status             ← 固定路径
3. GET    /tasks/recent             ← 固定路径
4. POST   /tasks/fetch/history      ← 固定路径
5. POST   /tasks/fetch/realtime     ← 固定路径
6. GET    /tasks/fetch/stocklist    ← 固定路径
7. GET    /tasks                    ← 固定路径
8. POST   /tasks                    ← 固定路径
9. GET    /tasks/{task_id}          ← 参数路径（最后）
```

---

## 功能对比

| 功能 | 旧 data_api | 新 task_api |
|------|-------------|-------------|
| 获取任务列表 | ✅ | ✅ |
| 获取任务状态 | ✅ | ✅ |
| 创建历史数据任务 | ✅ | ✅ |
| 获取实时行情 | ✅ | ✅ |
| 获取股票列表 | ✅ | ✅ |
| 获取任务统计 | ⚠️ 简单实现 | ✅ 完整实现 |
| 获取系统状态 | ⚠️ 简单实现 | ✅ 完整实现 |
| 获取最近任务 | ❌ | ✅ 新增 |
| Repository 模式 | ❌ | ✅ 使用 |
| Service 层 | ❌ | ✅ 使用 |
| 依赖注入 | ❌ | ✅ FastAPI Depends |
| 后台任务 | ✅ | ✅ |

---

## 验证测试

创建了 `tests/test_task_api.py` 用于验证路由配置：

```bash
PYTHONPATH=/Users/xujia/MyCode/sadviser uv run python tests/test_task_api.py
```

测试结果：
- ✅ 所有固定路径在参数路径之前
- ✅ 参数路径 `/{task_id}` 在最后位置
- ✅ 没有路由冲突

---

## 使用示例

### 1. 获取任务列表

```bash
GET /api/tasks?status=completed&limit=10
```

### 2. 创建历史数据获取任务

```bash
POST /api/tasks/fetch/history
{
  "symbols": ["000001", "000002"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "source": "akshare"
}
```

### 3. 查询任务状态

```bash
GET /api/tasks/{task_id}
```

### 4. 获取实时行情

```bash
POST /api/tasks/fetch/realtime?symbols=000001,000002&source=akshare&store=true
```

### 5. 获取系统状态

```bash
GET /api/tasks/status
```

---

## 优势

1. **清晰的架构**：Repository → Service → API 三层分离
2. **易于测试**：每层可独立测试
3. **依赖注入**：使用 FastAPI 标准，解耦合
4. **代码复用**：业务逻辑集中在 Service 层
5. **易于扩展**：添加新功能只需在对应层添加代码
6. **统一管理**：容器统一管理所有服务实例

---

## 后续工作建议

1. **添加单元测试**：为 TaskService 和 TaskRepository 添加完整测试
2. **性能优化**：添加缓存层（Redis）减少数据库查询
3. **任务队列**：考虑使用 Celery 替代 FastAPI 的 BackgroundTasks
4. **错误处理**：统一异常处理机制
5. **文档完善**：添加更详细的 API 文档和示例

---

## 总结

✅ **成功实现 task_api.py，完全替换旧的 data_api.py**

- 遵循 Repository → Service → API 分层架构
- 使用 FastAPI 依赖注入系统
- 路由顺序正确，无冲突
- 所有功能完整实现
- 代码质量高，易于维护和扩展

---

*最后更新: 2026-01-06*
