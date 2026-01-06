/**
 * 数据管理相关API
 * 已更新为使用新的 task_api 接口
 */
import api from './index';

/**
 * 获取历史数据并存储（创建后台任务）
 */
export async function fetchHistoryData(data) {
  return api.post('/api/v1/tasks/fetch/history', data);
}

/**
 * 获取实时行情并存储
 */
export async function fetchRealtimeData(data) {
  const { symbols, source = 'akshare', store = true } = data;

  // 后端现在接收逗号分隔的字符串
  const symbolString = Array.isArray(symbols) ? symbols.join(',') : symbols;

  return api.post('/api/v1/tasks/fetch/realtime', null, {
    params: {
      symbols: symbolString,
      source,
      store
    }
  });
}

/**
 * 获取股票列表
 */
export async function fetchStockList(source = 'akshare', store = false) {
  return api.get('/api/v1/tasks/fetch/stocklist', {
    params: { source, store }
  });
}

/**
 * 获取所有任务
 */
export async function getTasks() {
  const response = await api.get('/api/v1/tasks');
  return response.tasks || [];
}

/**
 * 查询任务状态
 */
export async function getTaskStatus(taskId) {
  return api.get(`/api/v1/tasks/${taskId}`);
}

/**
 * 获取最近任务
 */
export async function getRecentTasks(limit = 10) {
  const response = await api.get('/api/v1/tasks/recent', {
    params: { limit }
  });
  return response.tasks || [];
}

/**
 * 获取任务统计
 */
export async function getTaskStats() {
  const response = await api.get('/api/v1/tasks/stats');
  return response.stats || {};
}

/**
 * 批量存储数据（保留用于兼容性）
 * @deprecated 此接口在新版本中可能不再使用
 */
export async function batchStoreData(data) {
  return api.post('/api/v1/data/store/batch', data);
}

/**
 * 查询数据（保留用于兼容性）
 * @deprecated 此接口在新版本中可能不再使用
 */
export async function queryData(params) {
  return api.get('/api/v1/data/query', params);
}

/**
 * 获取系统状态
 */
export async function getSystemStatus() {
  return api.get('/api/v1/tasks/status');
}
