/**
 * 数据管理相关API
 * 已更新为使用后台任务模式 - 所有数据获取操作都是异步非阻塞的
 */
import api from './index';

/**
 * 获取历史数据并存储（创建后台任务）
 * @param {Object} data - 任务参数
 * @param {string[]} data.symbols - 股票代码列表
 * @param {string} data.start_date - 开始日期 (YYYY-MM-DD)
 * @param {string} data.end_date - 结束日期 (YYYY-MM-DD)
 * @param {string} data.source - 数据源 (akshare, tushare, sina)
 * @param {string} data.priority - 任务优先级 (low, medium, high)
 * @returns {Promise<Object>} 返回任务信息 {task_id, status, message, ...}
 */
export async function fetchHistoryData(data) {
  return api.post('/api/tasks/fetch/history', data);
}

/**
 * 获取实时行情并存储（创建后台任务）
 * @param {Object} data - 任务参数
 * @param {string[]} data.symbols - 股票代码列表
 * @param {string} data.source - 数据源 (akshare, tushare, sina)
 * @param {boolean} data.store - 是否存储到数据库
 * @returns {Promise<Object>} 返回任务信息 {task_id, status, message, ...}
 */
export async function fetchRealtimeData(data) {
  const { symbols, source = 'akshare', store = true } = data;

  return api.post('/api/tasks/fetch/realtime', {
    symbols,
    source,
    store
  });
}

/**
 * 获取股票列表（创建后台任务）
 * @param {Object} options - 任务参数
 * @param {string} options.source - 数据源 (akshare, tushare)
 * @param {boolean} options.store - 是否存储到数据库
 * @param {boolean} options.force_refresh - 是否强制刷新
 * @returns {Promise<Object>} 返回任务信息 {task_id, status, message, ...}
 */
export async function fetchStockList(options = {}) {
  const { source = 'akshare', store = false, force_refresh = false } = options;

  return api.post('/api/tasks/fetch/stocklist', {
    source,
    store,
    force_refresh
  });
}

/**
 * 获取所有任务
 * @param {Object} params - 查询参数
 * @param {string} params.status - 任务状态过滤 (pending, running, completed, failed)
 * @param {number} params.limit - 返回数量限制
 * @param {number} params.offset - 偏移量
 * @returns {Promise<Object>} 返回任务列表 {tasks, total, count, ...}
 */
export async function getTasks(params = {}) {
  const response = await api.get('/api/tasks', { params });
  return response.tasks || [];
}

/**
 * 查询任务状态
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>} 返回任务详情
 */
export async function getTaskStatus(taskId) {
  return api.get(`/api/tasks/${taskId}`);
}

/**
 * 获取最近任务
 * @param {number} limit - 返回数量
 * @returns {Promise<Object>} 返回最近任务列表 {tasks, count}
 */
export async function getRecentTasks(limit = 10) {
  const response = await api.get('/api/tasks/recent', {
    params: { limit }
  });
  return response.tasks || [];
}

/**
 * 获取任务统计
 * @returns {Promise<Object>} 返回任务统计数据 {stats, timestamp}
 */
export async function getTaskStats() {
  const response = await api.get('/api/tasks/stats');
  return response.stats || {};
}

/**
 * 创建自定义任务
 * @param {Object} data - 任务参数
 * @param {string} data.task_type - 任务类型
 * @param {Object} data.meta - 任务元数据
 * @param {string} data.priority - 任务优先级
 * @returns {Promise<Object>} 返回任务信息
 */
export async function createTask(data) {
  return api.post('/api/tasks', data);
}

/**
 * 获取系统状态
 * @returns {Promise<Object>} 返回系统状态信息
 */
export async function getSystemStatus() {
  return api.get('/api/tasks/status');
}

/**
 * 批量存储数据（保留用于兼容性）
 * @deprecated 此接口在新版本中可能不再使用
 */
export async function batchStoreData(data) {
  return api.post('/api/data/store/batch', data);
}

/**
 * 查询数据（保留用于兼容性）
 * @deprecated 此接口在新版本中可能不再使用
 */
export async function queryData(params) {
  return api.get('/api/data/query', params);
}
