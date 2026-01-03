/**
 * 股票列表组件
 */
import StockCard from './StockCard';
import '../styles/StockList.css';

function StockList({ stocks, loading = false, emptyMessage = '暂无数据' }) {
  // 骨架屏组件
  const SkeletonCard = () => (
    <div className="stock-card stock-card-skeleton">
      <div className="stock-header">
        <div className="stock-title">
          <div className="skeleton skeleton-title"></div>
          <div className="skeleton skeleton-symbol"></div>
        </div>
        <div className="stock-price-skeleton">
          <div className="skeleton skeleton-price"></div>
          <div className="skeleton skeleton-change"></div>
        </div>
      </div>
      <div className="stock-body">
        <div className="stock-info">
          <div className="info-item">
            <div className="skeleton skeleton-label"></div>
            <div className="skeleton skeleton-value"></div>
          </div>
          <div className="info-item">
            <div className="skeleton skeleton-label"></div>
            <div className="skeleton skeleton-value"></div>
          </div>
          <div className="info-item">
            <div className="skeleton skeleton-label"></div>
            <div className="skeleton skeleton-value"></div>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="stock-list">
        <div className="stock-grid">
          {Array.from({ length: 12 }).map((_, index) => (
            <SkeletonCard key={index} />
          ))}
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
