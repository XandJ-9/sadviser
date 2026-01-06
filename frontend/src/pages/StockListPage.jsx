/**
 * 首页 - 股票列表
 */
import { useState, useEffect } from 'react';
import FilterPanel from '../components/FilterPanel';
import StockList from '../components/StockList';
import Pagination from '../components/Pagination';
import { getStockList } from '../api/stock';
import '../styles/HomePage.css';

function HomePage() {
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
      setError(err.message || '获取股票列表失败,请稍后重试');
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
    <div className="home-page">
      <div className="page-header">
        <h1>股票列表</h1>
        <p className="page-subtitle">实时股票数据浏览</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => {
            setCurrentPage(1);
            fetchStocks({ limit: pageSize, offset: 0 });
          }} className="retry-btn">
            重试
          </button>
        </div>
      )}

      <FilterPanel onFilter={handleFilter} loading={loading} />

      <div className="results-section">
        <h2 className="results-title">
          股票列表 {total > 0 && `(共 ${total} 条)`}
        </h2>
        <StockList stocks={stocks} loading={loading} />

        {/* 分页组件 */}
        {!loading && stocks.length > 0 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            pageSize={pageSize}
            total={total}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        )}
      </div>
    </div>
  );
}

export default HomePage;
