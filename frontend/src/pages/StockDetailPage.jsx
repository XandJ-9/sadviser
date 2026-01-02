/**
 * 股票详情页
 */
import { useState, useEffect } from 'react';
import { useParams } from 'wouter';
import { getStockDetail, getStockHistory } from '../api/stock';
import { getTradingSignals } from '../api/strategy';
import '../styles/StockDetailPage.css';

function StockDetailPage() {
  const { symbol } = useParams();
  const [stock, setStock] = useState(null);
  const [history, setHistory] = useState([]);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // 并行获取数据
        const [stockData, historyData, signalsData] = await Promise.all([
          getStockDetail(symbol),
          getStockHistory(symbol, { limit: 100 }),
          getTradingSignals(symbol).catch(() => ({ signals: [] })),
        ]);

        setStock(stockData);
        setHistory(historyData.data || []);
        setSignals(signalsData.signals || []);
      } catch (err) {
        console.error('获取股票详情失败:', err);
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

  return (
    <div className="stock-detail-page">
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
          <h2>基本信息</h2>
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
          <h2>技术指标</h2>
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
          <h2>交易信号</h2>
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
    </div>
  );
}

export default StockDetailPage;
