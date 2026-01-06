/**
 * 股票相关API
 */
import api from './index';

/**
 * 获取股票列表
 */
export async function getStockList(params = {}) {
  return api.get('/api/v1/stocks', params);
}

/**
 * 获取股票详情
 */
export async function getStockDetail(symbol) {
  return api.get(`/api/v1/stocks/${symbol}`);
}

/**
 * 获取股票历史数据
 */
export async function getStockHistory(symbol, params = {}) {
  return api.get(`/api/v1/stocks/${symbol}/history`, params);
}

/**
 * 获取实时行情
 */
export async function getStockQuote(symbols) {
  const symbolList = Array.isArray(symbols) ? symbols.join(',') : symbols;
  return api.get('/api/v1/stocks/quote', { symbols: symbolList });
}

/**
 * 搜索股票
 */
export async function searchStocks(keyword, params = {}) {
  return api.get(`/api/v1/stocks/search/${keyword}`, params);
}

/**
 * 获取热门股票
 */
export async function getHotStocks(params = {}) {
  return api.get('/api/v1/stocks/hot', params);
}

/**
 * 获取市场概览
 */
export async function getMarketOverview() {
  return api.get('/api/v1/stocks/market/overview');
}
