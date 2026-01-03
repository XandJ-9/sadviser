/**
 * 数据管理相关API
 */
import api from './index';

/**
 * 获取历史数据并存储
 */
export async function fetchHistoryData(data) {
  return api.post('/api/v1/data/fetch/history', data);
}

/**
 * 获取实时行情并存储
 */
export async function fetchRealtimeData(data) {
  return api.post('/api/v1/data/fetch/realtime', data);
}

/**
 * 获取股票列表
 */
export async function fetchStockList(source = 'akshare', store = false) {
  return api.get('/api/v1/data/fetch/stocklist', { source, store });
}

/**
 * 获取所有任务
 */
export async function getTasks() {
  return api.get('/api/v1/data/tasks');
}

/**
 * 查询任务状态
 */
export async function getTaskStatus(taskId) {
  return api.get(`/api/v1/data/task/${taskId}`);
}

/**
 * 批量存储数据
 */
export async function batchStoreData(data) {
  return api.post('/api/v1/data/store/batch', data);
}

/**
 * 查询数据
 */
export async function queryData(params) {
  return api.get('/api/v1/data/query', params);
}

/**
 * 获取系统状态
 */
export async function getSystemStatus() {
  return api.get('/api/v1/data/status');
}
