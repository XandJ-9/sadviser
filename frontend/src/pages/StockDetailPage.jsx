/**
 * 股票详情页
 */
import { useState, useEffect } from 'react';
import { useParams } from 'wouter';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getStockDetail, getStockHistory } from '../api/stock';
import { getTradingSignals } from '../api/strategy';
import '../styles/StockDetailPage.css';

function StockDetailPage() {
  const { symbol } = useParams();
  const [stock, setStock] = useState(null);
  const [history, setHistory] = useState([]);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // 获取股票详情
  const fetchStockDetail = async () => {
    try {
      const data = await getStockDetail(symbol);
      setStock(data);
    } catch (err) {
      console.error('获取股票详情失败:', err);
      throw err;
    }
  };

  // 获取历史数据
  const fetchStockHistory = async () => {
    try {
      const data = await getStockHistory(symbol, { limit: 100 });
      setHistory(data.data || []);
    } catch (err) {
      console.error('获取历史数据失败:', err);
      // 历史数据失败不影响主流程
    }
  };

  // 获取交易信号
  const fetchTradingSignals = async () => {
    try {
      const data = await getTradingSignals(symbol);
      setSignals(data.signals || []);
    } catch (err) {
      console.error('获取交易信号失败:', err);
      // 交易信号失败不影响主流程
    }
  };

  // 刷新所有数据
  const refreshAllData = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        fetchStockDetail(),
        fetchStockHistory(),
        fetchTradingSignals(),
      ]);
    } catch (err) {
      console.error('刷新数据失败:', err);
      setError(err.message || '刷新数据失败');
    } finally {
      setRefreshing(false);
    }
  };

  // 初始加载
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        await Promise.all([
          fetchStockDetail(),
          fetchStockHistory(),
          fetchTradingSignals(),
        ]);
      } catch (err) {
        setError(err.message || '获取股票详情失败');
      } finally {
        setLoading(false);
      }
    };

    if (symbol) {
      fetchData();
    }
  }, [symbol]);

  if (loading) {
    return (
      <div className="stock-detail-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  if (error || !stock) {
    return (
      <div className="stock-detail-page">
        <div className="error-container">
          <p>{error || '股票不存在'}</p>
        </div>
      </div>
    );
  }

  const isPositive = stock.changePercent >= 0;

  // 准备图表数据
  const chartData = history.slice().reverse().map(item => ({
    date: new Date(item.date).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }),
    收盘价: item.close || 0,
    开盘价: item.open || 0,
    最高价: item.high || 0,
    最低价: item.low || 0,
  }));

  return (
    <div className="stock-detail-page">
      {/* 顶部控制栏 */}
      <div className="detail-controls">
        <button
          className="refresh-btn"
          onClick={refreshAllData}
          disabled={refreshing}
        >
          {refreshing ? (
            <>
              <span className="spinner-small"></span>
              刷新中...
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
              </svg>
              刷新数据
            </>
          )}
        </button>
      </div>

      {/* 实时报价部分 */}
      <div className="detail-header">
        <div>
          <h1 className="stock-title">{stock.name}</h1>
          <p className="stock-symbol">{symbol}</p>
        </div>
        <div className={`price-info ${isPositive ? 'positive' : 'negative'}`}>
          <span className="current-price">¥{stock.price?.toFixed(2)}</span>
          <span className="price-change">
            {isPositive ? '+' : ''}{(stock.changePercent || 0).toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-section">
          <div className="section-header">
            <h2>基本信息</h2>
            <button
              className="section-refresh-btn"
              onClick={fetchStockDetail}
              title="刷新基本信息"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
              </svg>
            </button>
          </div>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">开盘价</span>
              <span className="value">¥{stock.open?.toFixed(2)}</span>
            </div>
            <div className="info-item">
              <span className="label">最高价</span>
              <span className="value">¥{stock.high?.toFixed(2)}</span>
            </div>
            <div className="info-item">
              <span className="label">最低价</span>
              <span className="value">¥{stock.low?.toFixed(2)}</span>
            </div>
            <div className="info-item">
              <span className="label">成交量</span>
              <span className="value">{stock.volume?.toLocaleString()}</span>
            </div>
            <div className="info-item">
              <span className="label">市值</span>
              <span className="value">
                ¥{((stock.marketCap || 0) / 100000000).toFixed(2)}亿
              </span>
            </div>
            <div className="info-item">
              <span className="label">市盈率</span>
              <span className="value">{stock.pe?.toFixed(2) || '-'}</span>
            </div>
          </div>
        </div>

        <div className="detail-section">
          <div className="section-header">
            <h2>技术指标</h2>
            <button
              className="section-refresh-btn"
              onClick={fetchStockDetail}
              title="刷新技术指标"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
              </svg>
            </button>
          </div>
          {stock.indicators ? (
            <div className="indicators-grid">
              {stock.indicators.ma5 && (
                <div className="indicator-item">
                  <span className="indicator-name">MA5</span>
                  <span className="indicator-value">
                    {stock.indicators.ma5.toFixed(2)}
                  </span>
                </div>
              )}
              {stock.indicators.ma20 && (
                <div className="indicator-item">
                  <span className="indicator-name">MA20</span>
                  <span className="indicator-value">
                    {stock.indicators.ma20.toFixed(2)}
                  </span>
                </div>
              )}
              {stock.indicators.rsi && (
                <div className="indicator-item">
                  <span className="indicator-name">RSI</span>
                  <span className="indicator-value">
                    {stock.indicators.rsi.toFixed(2)}
                  </span>
                </div>
              )}
              {stock.indicators.macd && (
                <div className="indicator-item">
                  <span className="indicator-name">MACD</span>
                  <span className="indicator-value">
                    {stock.indicators.macd.toFixed(4)}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="no-data">暂无技术指标数据</p>
          )}
        </div>

        <div className="detail-section">
          <div className="section-header">
            <h2>交易信号</h2>
            <button
              className="section-refresh-btn"
              onClick={fetchTradingSignals}
              title="刷新交易信号"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
              </svg>
            </button>
          </div>
          {signals && signals.length > 0 ? (
            <div className="signals-list">
              {signals.slice(0, 10).map((signal, index) => (
                <div key={index} className={`signal-item signal-${signal.type}`}>
                  <span className="signal-date">
                    {new Date(signal.date).toLocaleDateString('zh-CN')}
                  </span>
                  <span className="signal-type">
                    {signal.type === 'buy' ? '买入' : signal.type === 'sell' ? '卖出' : '持有'}
                  </span>
                  <span className="signal-price">
                    ¥{signal.price?.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data">暂无交易信号</p>
          )}
        </div>
      </div>

      {/* 历史行情趋势图 */}
      <div className="history-chart-section">
        <div className="section-header">
          <h2>历史行情</h2>
          <button
            className="section-refresh-btn"
            onClick={fetchStockHistory}
            title="刷新历史数据"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
              <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
            </svg>
          </button>
        </div>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="收盘价" stroke="#ef4444" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="开盘价" stroke="#3b82f6" strokeWidth={1} dot={false} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">暂无历史数据</p>
        )}
      </div>
    </div>
  );
}

export default StockDetailPage;
