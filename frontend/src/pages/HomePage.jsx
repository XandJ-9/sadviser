/**
 * 首页 - 市场概览
 */
import { useState, useEffect } from 'react';
import { getMarketOverview, getHotStocks } from '../api/stock';
import { StatCard } from '../components/ui';
import { Link } from 'wouter';

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
      setError(err.message || '获取市场数据失败，请稍后重试');
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">市场概览</h1>
          <p className="mt-2 text-gray-600">A股整体行情实时监控</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">市场概览</h1>
          <p className="mt-2 text-gray-600">A股整体行情实时监控</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800 mb-4">{error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">市场概览</h1>
            <p className="mt-2 text-gray-600">A股整体行情实时监控</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">
              更新时间: {marketData?.timestamp ? new Date(marketData.timestamp).toLocaleString('zh-CN') : '-'}
            </p>
          </div>
        </div>
      </div>

      {/* Market Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="总成交量"
          value={formatVolume(marketData?.totalVolume || 0)}
          icon="📊"
          variant="primary"
        />

        <StatCard
          title="涨停"
          value={marketData?.limitUp || 0}
          icon="📈"
          variant="success"
          trend="较昨日"
        />

        <StatCard
          title="跌停"
          value={marketData?.limitDown || 0}
          icon="📉"
          variant="danger"
          trend="较昨日"
        />

        <StatCard
          title="上涨"
          value={marketData?.up || 0}
          icon="💹"
          variant="success"
        />

        <StatCard
          title="下跌"
          value={marketData?.down || 0}
          icon="📉"
          variant="danger"
        />

        <StatCard
          title="平盘"
          value={marketData?.flat || 0}
          icon="➖"
          variant="default"
        />
      </div>

      {/* Hot Stocks Section */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">热门股票</h2>
          <p className="mt-1 text-sm text-gray-500">成交量最大的股票</p>
        </div>

        <div className="divide-y divide-gray-200">
          {hotStocks.length > 0 ? (
            hotStocks.map((stock, index) => (
              <Link
                key={stock.symbol}
                href={`/stocks/${stock.symbol}`}
                className="block hover:bg-gray-50 transition-colors"
              >
                <div className="px-6 py-4 flex items-center gap-4">
                  {/* Rank */}
                  <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-700 rounded-full font-bold text-sm">
                    {index + 1}
                  </div>

                  {/* Stock Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-gray-900 truncate">{stock.name}</p>
                      <span className="text-xs text-gray-500">{stock.symbol}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{stock.reason || '成交活跃'}</p>
                  </div>

                  {/* Price and Change */}
                  <div className="flex-shrink-0 text-right">
                    <p className="text-lg font-semibold text-gray-900">
                      ¥{stock.price?.toFixed(2) || '-'}
                    </p>
                    <p className={`text-sm font-medium ${stock.changePercent >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent?.toFixed(2) || '0.00'}%
                    </p>
                  </div>

                  {/* Arrow */}
                  <div className="flex-shrink-0 text-gray-400">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </Link>
            ))
          ) : (
            <div className="px-6 py-12 text-center">
              <p className="text-gray-500">暂无热门股票数据</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HomePage;
