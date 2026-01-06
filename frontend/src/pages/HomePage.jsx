/**
 * 首页 - 市场概览
 */
import { useState, useEffect } from 'react';
import { getMarketOverview, getHotStocks } from '../api/stock';
import '../styles/HomePage.css';

function HomePage() {
  const [marketData, setMarketData] = useState(null);
  const [hotStocks, setHotStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 获取市场概览数据
  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [overview, hot] = await Promise.all([
        getMarketOverview(),
        getHotStocks({ limit: 10 })
      ]);

      setMarketData(overview);
      setHotStocks(hot.stocks || []);
    } catch (err) {
      console.error('获取市场数据失败:', err);
      setError(err.message || '获取市场数据失败,请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // 每30秒刷新一次
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // 格式化成交量
  const formatVolume = (volume) => {
    if (volume >= 100000000) {
      return `${(volume / 100000000).toFixed(2)}亿`;
    } else if (volume >= 10000) {
      return `${(volume / 10000).toFixed(2)}万`;
    }
    return volume.toString();
  };

  if (loading) {
    return (
      <div className="market-overview-page">
        <div className="page-header">
          <h1>市场概览</h1>
          <p className="page-subtitle">A股整体行情实时监控</p>
        </div>
        <div className="loading-skeleton">
          <div className="skeleton-card"></div>
          <div className="skeleton-card"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="market-overview-page">
        <div className="page-header">
          <h1>市场概览</h1>
          <p className="page-subtitle">A股整体行情实时监控</p>
        </div>
        <div className="error-message">
          {error}
          <button onClick={fetchData} className="retry-btn">重试</button>
        </div>
      </div>
    );
  }

  return (
    <div className="market-overview-page">
      <div className="page-header">
        <h1>市场概览</h1>
        <p className="page-subtitle">A股整体行情实时监控</p>
        <p className="update-time">
          更新时间: {marketData?.timestamp ? new Date(marketData.timestamp).toLocaleString('zh-CN') : '-'}
        </p>
      </div>

      {/* 市场统计卡片 */}
      <div className="market-stats">
        <div className="stat-card stat-primary">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-label">总成交量</div>
            <div className="stat-value">{formatVolume(marketData?.totalVolume || 0)}</div>
          </div>
        </div>

        <div className="stat-card stat-up">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-label">涨停</div>
            <div className="stat-value">{marketData?.limitUp || 0}</div>
          </div>
        </div>

        <div className="stat-card stat-down">
          <div className="stat-icon">📉</div>
          <div className="stat-content">
            <div className="stat-label">跌停</div>
            <div className="stat-value">{marketData?.limitDown || 0}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💹</div>
          <div className="stat-content">
            <div className="stat-label">上涨</div>
            <div className="stat-value">{marketData?.up || 0}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📉</div>
          <div className="stat-content">
            <div className="stat-label">下跌</div>
            <div className="stat-value">{marketData?.down || 0}</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">➖</div>
          <div className="stat-content">
            <div className="stat-label">平盘</div>
            <div className="stat-value">{marketData?.flat || 0}</div>
          </div>
        </div>
      </div>

      {/* 热门股票 */}
      <div className="hot-stocks-section">
        <h2 className="section-title">热门股票</h2>
        <div className="hot-stocks-list">
          {hotStocks.length > 0 ? (
            hotStocks.map((stock, index) => (
              <a
                key={stock.symbol}
                href={`/stocks/${stock.symbol}`}
                className="hot-stock-item"
              >
                <div className="stock-rank">{index + 1}</div>
                <div className="stock-info">
                  <div className="stock-name">{stock.name}</div>
                  <div className="stock-symbol">{stock.symbol}</div>
                </div>
                <div className="stock-price">{stock.price?.toFixed(2) || '-'}</div>
                <div className={`stock-change ${stock.changePercent >= 0 ? 'positive' : 'negative'}`}>
                  {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent?.toFixed(2) || '0.00'}%
                </div>
                <div className="stock-reason">{stock.reason || '热门'}</div>
              </a>
            ))
          ) : (
            <div className="empty-state">暂无热门股票数据</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HomePage;
