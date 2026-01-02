/**
 * 筛选面板组件
 */
import { useState } from 'react';
import '../styles/FilterPanel.css';

function FilterPanel({ onFilter, loading = false }) {
  const [filters, setFilters] = useState({
    minPrice: '',
    maxPrice: '',
    minChange: '',
    maxChange: '',
    minVolume: '',
    strategy: 'all',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onFilter(filters);
  };

  const handleReset = () => {
    const resetFilters = {
      minPrice: '',
      maxPrice: '',
      minChange: '',
      maxChange: '',
      minVolume: '',
      strategy: 'all',
    };
    setFilters(resetFilters);
    onFilter(resetFilters);
  };

  return (
    <div className="filter-panel">
      <h3 className="filter-title">筛选条件</h3>
      <form onSubmit={handleSubmit} className="filter-form">
        <div className="filter-row">
          <div className="filter-group">
            <label>价格区间</label>
            <div className="filter-inputs">
              <input
                type="number"
                name="minPrice"
                placeholder="最低价"
                value={filters.minPrice}
                onChange={handleChange}
              />
              <span>-</span>
              <input
                type="number"
                name="maxPrice"
                placeholder="最高价"
                value={filters.maxPrice}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="filter-group">
            <label>涨跌幅 (%)</label>
            <div className="filter-inputs">
              <input
                type="number"
                name="minChange"
                placeholder="最低"
                value={filters.minChange}
                onChange={handleChange}
              />
              <span>-</span>
              <input
                type="number"
                name="maxChange"
                placeholder="最高"
                value={filters.maxChange}
                onChange={handleChange}
              />
            </div>
          </div>
        </div>

        <div className="filter-row">
          <div className="filter-group">
            <label>最小成交量</label>
            <input
              type="number"
              name="minVolume"
              placeholder="输入成交量"
              value={filters.minVolume}
              onChange={handleChange}
            />
          </div>

          <div className="filter-group">
            <label>策略类型</label>
            <select
              name="strategy"
              value={filters.strategy}
              onChange={handleChange}
            >
              <option value="all">全部策略</option>
              <option value="ma_cross">均线交叉</option>
              <option value="macd">MACD</option>
              <option value="bollinger">布林带</option>
            </select>
          </div>
        </div>

        <div className="filter-actions">
          <button
            type="button"
            onClick={handleReset}
            className="btn-secondary"
            disabled={loading}
          >
            重置
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? '筛选中...' : '筛选'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default FilterPanel;
