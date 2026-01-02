/**
 * 策略相关API
 */
import api from './index';

/**
 * 获取每日推荐
 */
export async function getDailyRecommendations(params = {}) {
  return api.get('/api/v1/strategy/recommendations', params);
}

/**
 * 股票筛选
 */
export async function screenStocks(filters = {}) {
  return api.post('/api/v1/strategy/screen', filters);
}

/**
 * 获取交易信号
 */
export async function getTradingSignals(symbol, params = {}) {
  return api.get(`/api/v1/strategy/signals/${symbol}`, params);
}

/**
 * 获取策略列表
 */
export async function getStrategies() {
  return api.get('/api/v1/strategy/list');
}

/**
 * 执行策略回测
 */
export async function runBacktest(backtestConfig) {
  return api.post('/api/v1/backtest/create', backtestConfig);
}

/**
 * 获取回测结果
 */
export async function getBacktestResult(taskId) {
  return api.get(`/api/v1/backtest/${taskId}`);
}

/**
 * 获取回测交易记录
 */
export async function getBacktestTrades(taskId) {
  return api.get(`/api/v1/backtest/${taskId}/trades`);
}

/**
 * 获取回测绩效指标
 */
export async function getBacktestMetrics(taskId) {
  return api.get(`/api/v1/backtest/${taskId}/metrics`);
}
