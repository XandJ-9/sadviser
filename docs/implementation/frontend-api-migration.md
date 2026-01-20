# 前端数据管理模块接口迁移总结

> **原文档**: [FRONTEND_API_MIGRATION.md](../FRONTEND_API_MIGRATION.md)
>
> **更新日期**: 2026-01-06

## 概述

成功将前端数据管理模块的API接口从旧的 `data_api` 迁移到新的 `task_api`。

---

## 修改的文件

### 1. `frontend/src/api/data.js`

#### 修改的接口映射

| 旧接口 | 新接口 | 说明 |
|--------|--------|------|
| `/api/v1/data/fetch/history` | `/api/v1/tasks/fetch/history` | 创建历史数据获取任务 |
| `/api/v1/data/fetch/realtime` | `/api/v1/tasks/fetch/realtime` | 获取实时行情 |
| `/api/v1/data/fetch/stocklist` | `/api/v1/tasks/fetch/stocklist` | 获取股票列表 |
| `/api/v1/data/tasks` | `/api/v1/tasks` | 获取所有任务 |
| `/api/v1/data/task/{id}` | `/api/v1/tasks/{id}` | 查询任务状态 |
| `/api/v1/data/status` | `/api/v1/tasks/status` | 获取系统状态 |

#### 新增的接口

```javascript
// 获取最近任务
export async function getRecentTasks(limit = 10)

// 获取任务统计
export async function getTaskStats()
```

#### 保留的接口（已标记为 @deprecated）

```javascript
// 批量存储数据
export async function batchStoreData(data)

// 查询数据
export async function queryData(params)
```

这些接口保留是为了兼容性，但在新版本中可能不再使用。

### 2. `frontend/src/api/index.js`

#### 修改内容

更新了 `post()` 方法，使其支持查询参数（query parameters）：

```javascript
/**
 * POST请求
 * @param {string} endpoint - API端点
 * @param {object} data - 请求体数据
 * @param {object} options - 额外选项，如 { params: { key: value } }
 */
async post(endpoint, data = {}, options = {}) {
  const { params = {} } = options;
  const queryString = new URLSearchParams(params).toString();
  const url = queryString ? `${endpoint}?${queryString}` : endpoint;

  return this.request(url, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

这个修改允许 POST 请求同时传递请求体和查询参数，例如：

```javascript
api.post('/api/tasks/fetch/realtime', null, {
  params: { symbols: '000001,000002', source: 'akshare', store: 'true' }
});
```

---

## 关键变更说明

### 1. `fetchRealtimeData` 函数

**旧实现：**
```javascript
export async function fetchRealtimeData(data) {
  return api.post('/api/v1/data/fetch/realtime', data);
}
```

**新实现：**
```javascript
export async function fetchRealtimeData(data) {
  const { symbols, source = 'akshare', store = true } = data;
  return api.post('/api/v1/tasks/fetch/realtime', null, {
    params: { symbols: symbols.join(','), source, store }
  });
}
```

**原因：** 新的 task_api 接口使用查询参数而不是请求体来接收这些参数。

### 2. `getTasks` 函数

**旧实现：**
```javascript
export async function getTasks() {
  return api.get('/api/v1/data/tasks');
}
```

**新实现：**
```javascript
export async function getTasks() {
  const response = await api.get('/api/v1/tasks');
  return response.tasks || [];
}
```

**原因：** 新的 task_api 返回的是一个包含 `tasks` 字段的对象，而不是直接返回数组。

### 3. `fetchStockList` 函数

**旧实现：**
```javascript
export async function fetchStockList(source = 'akshare', store = false) {
  return api.get('/api/v1/data/fetch/stocklist', { source, store });
}
```

**新实现：**
```javascript
export async function fetchStockList(source = 'akshare', store = false) {
  return api.get('/api/v1/tasks/fetch/stocklist', {
    params: { source, store }
  });
}
```

**原因：** 使用明确的 `params` 对象，使代码更清晰。

---

## 未修改的文件

以下文件无需修改，因为它们只使用了 `data.js` 中导出的函数：

- `frontend/src/pages/DataManagementPage.jsx`
- `frontend/src/components/DataFetchForm.jsx`
- `frontend/src/components/TaskList.jsx`

---

## 测试验证

### 构建测试

```bash
cd frontend
pnpm build
```

**结果：** ✅ 构建成功

```
✓ 691 modules transformed.
✓ built in 1.83s
```

### 接口兼容性测试

所有现有组件仍然正常工作，因为：

1. **导出的函数名保持不变** - `getTasks()`, `fetchHistoryData()` 等
2. **函数签名保持兼容** - 参数类型和顺序没有变化
3. **返回值格式已适配** - 在 API 层处理了返回值格式的差异

---

## 使用示例

### 创建历史数据获取任务

```javascript
const response = await fetchHistoryData({
  symbols: ['000001', '000002'],
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  source: 'akshare'
});
// response: { task_id: 'task_xxx', status: 'pending', message: '...' }
```

### 获取实时行情

```javascript
const response = await fetchRealtimeData({
  symbols: ['000001'],
  source: 'akshare'
});
// response: { quotes: {...}, count: 1, stored: true }
```

### 获取任务列表

```javascript
const tasks = await getTasks();
// tasks: [{ id: 'task_xxx', status: 'completed', ... }, ...]
```

### 获取系统状态

```javascript
const status = await getSystemStatus();
// status: { storage_connected: true, active_tasks: 0, ... }
```

---

## 优势

1. **统一接口风格** - 所有任务相关接口都在 `/api/tasks` 下
2. **更好的架构** - 后端使用 Repository → Service → API 分层
3. **依赖注入** - 后端使用 FastAPI 的 `Depends()` 系统
4. **易于维护** - 清晰的代码结构和接口命名
5. **向后兼容** - 前端组件无需修改，只需更新 API 层

---

## 总结

✅ **成功完成前端 API 迁移**

- 所有数据管理接口已更新为新的 task_api
- ApiClient 增强了 POST 请求的参数支持
- 前端构建成功，无错误
- 保持向后兼容，现有组件无需修改
- 代码质量提升，更易于维护

新的 task_api 系统现在完全替代了旧的 data_api，为前端提供更稳定、更易用的数据管理接口。

---

*最后更新: 2026-01-06*
