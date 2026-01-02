/**
 * 股票列表组件
 */
import StockCard from './StockCard';
import '../styles/StockList.css';

function StockList({ stocks, loading = false, emptyMessage = '暂无数据' }) {
  if (loading) {
    return (
      <div className="stock-list">
        <div className="stock-list-loading">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  if (!stocks || stocks.length === 0) {
    return (
      <div className="stock-list">
        <div className="stock-list-empty">
          <p>{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-list">
      <div className="stock-grid">
        {stocks.map((stock, index) => (
          <StockCard key={stock.symbol || index} stock={stock} />
        ))}
      </div>
    </div>
  );
}

export default StockList;
