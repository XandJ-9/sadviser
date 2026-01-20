/**
 * 股票列表页面
 */
import { useState, useEffect } from 'react';
import FilterPanel from '../components/FilterPanel';
import StockList from '../components/StockList';
import Pagination from '../components/Pagination';
import { getStockList } from '../api/stock';

function StockListPage() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);

  // 计算总页数
  const totalPages = Math.ceil(total / pageSize);

  // 获取股票列表
  const fetchStocks = async (params = {}) => {
    setLoading(true);
    setError(null);

    try {
      const data = await getStockList(params);
      setStocks(data.stocks || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('获取股票列表失败:', err);
      setError(err.message || '获取股票列表失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const offset = (currentPage - 1) * pageSize;
    fetchStocks({ limit: pageSize, offset });
  }, [currentPage, pageSize]);

  // 处理筛选
  const handleFilter = async (filters) => {
    // 重置到第一页
    setCurrentPage(1);
    const offset = 0;
    fetchStocks({ ...filters, limit: pageSize, offset });
  };

  // 处理页码变化
  const handlePageChange = (page) => {
    setCurrentPage(page);
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // 处理每页数量变化
  const handlePageSizeChange = (newPageSize) => {
    setPageSize(newPageSize);
    setCurrentPage(1); // 重置到第一页
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">股票列表</h1>
        <p className="mt-2 text-gray-600">实时股票数据浏览</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => {
                setCurrentPage(1);
                fetchStocks({ limit: pageSize, offset: 0 });
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
            >
              重试
            </button>
          </div>
        </div>
      )}

      {/* Filter Panel */}
      <FilterPanel onFilter={handleFilter} loading={loading} />

      {/* Results Section */}
      <div className="mt-6">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              股票列表 {total > 0 && <span className="text-sm font-normal text-gray-500">(共 {total.toLocaleString()} 条)</span>}
            </h2>
          </div>

          {/* Stock List */}
          <StockList stocks={stocks} loading={loading} />

          {/* Pagination */}
          {!loading && stocks.length > 0 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                pageSize={pageSize}
                total={total}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StockListPage;
