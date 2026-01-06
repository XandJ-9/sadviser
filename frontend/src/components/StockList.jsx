/**
 * 股票列表组件 - 支持卡片和表格两种视图
 */
import { useState } from 'react';
import StockCard from './StockCard';
import StockTable from './StockTable';
import '../styles/StockList.css';

function StockList({ stocks, loading = false, emptyMessage = '暂无数据' }) {
  const [viewMode, setViewMode] = useState('table'); // 'grid' or 'table'

  // 骨架屏组件 - 表格视图
  const SkeletonTable = () => (
    <div className="stock-table-container">
      <table className="stock-table">
        <thead>
          <tr>
            <th>代码</th>
            <th>名称</th>
            <th>现价</th>
            <th>涨跌幅</th>
            <th>成交量</th>
            <th>MA5</th>
            <th>MA20</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 10 }).map((_, index) => (
            <tr key={index}>
              <td><div className="skeleton skeleton-text"></div></td>
              <td><div className="skeleton skeleton-text"></div></td>
              <td><div className="skeleton skeleton-text"></div></td>
              <td><div className="skeleton skeleton-text"></div></td>
              <td><div className="skeleton skeleton-text"></div></td>
              <td><div className="skeleton skeleton-text"></div></td>
              <td><div className="skeleton skeleton-text"></div></td>
              <td><div className="skeleton skeleton-text"></div></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // 骨架屏组件 - 卡片视图
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
        {viewMode === 'table' ? <SkeletonTable /> : (
          <div className="stock-grid">
            {Array.from({ length: 12 }).map((_, index) => (
              <SkeletonCard key={index} />
            ))}
          </div>
        )}
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
      {/* 视图切换按钮 */}
      <div className="view-toggle">
        <button
          className={`view-toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
          onClick={() => setViewMode('table')}
          title="表格视图"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M0 2h16v2H0V2zm0 4h16v2H0V6zm0 4h16v2H0v-2zm0 4h16v2H0v-2z"/>
          </svg>
          表格
        </button>
        <button
          className={`view-toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
          onClick={() => setViewMode('grid')}
          title="卡片视图"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M0 0h7v7H0V0zm9 0h7v7H9V0zM0 9h7v7H0V9zm9 0h7v7H9V9z"/>
          </svg>
          卡片
        </button>
      </div>

      {/* 内容区域 */}
      {viewMode === 'table' ? (
        <StockTable stocks={stocks} />
      ) : (
        <div className="stock-grid">
          {stocks.map((stock, index) => (
            <StockCard key={stock.symbol || index} stock={stock} />
          ))}
        </div>
      )}
    </div>
  );
}

export default StockList;
