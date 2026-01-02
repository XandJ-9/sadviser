/**
 * 股票卡片组件
 */
import { Link } from 'wouter';
import '../styles/StockCard.css';

function StockCard({ stock }) {
  const {
    symbol,
    name,
    price,
    changePercent,
    volume,
    indicators = {},
    recommendation = ''
  } = stock;

  // 判断涨跌
  const isPositive = changePercent >= 0;
  const changeClass = isPositive ? 'positive' : 'negative';
  const changeSign = isPositive ? '+' : '';

  // 格式化数字
  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="stock-card">
      <div className="stock-header">
        <div className="stock-title">
          <h3 className="stock-name">{name}</h3>
          <span className="stock-symbol">{symbol}</span>
        </div>
        <div className={`stock-price ${changeClass}`}>
          <span className="price">¥{formatNumber(price)}</span>
          <span className="change">
            {changeSign}{formatNumber(changePercent)}%
          </span>
        </div>
      </div>

      <div className="stock-body">
        <div className="stock-info">
          <div className="info-item">
            <span className="label">成交量</span>
            <span className="value">{volume ? formatNumber(volume) : '-'}</span>
          </div>

          {indicators.ma5 && (
            <div className="info-item">
              <span className="label">MA5</span>
              <span className="value">{formatNumber(indicators.ma5)}</span>
            </div>
          )}

          {indicators.ma20 && (
            <div className="info-item">
              <span className="label">MA20</span>
              <span className="value">{formatNumber(indicators.ma20)}</span>
            </div>
          )}
        </div>

        {recommendation && (
          <div className="stock-recommendation">
            <span className="recommendation-label">推荐理由:</span>
            <p className="recommendation-text">{recommendation}</p>
          </div>
        )}
      </div>

      <div className="stock-footer">
        <Link href={`/stocks/${symbol}`} className="detail-link">
          查看详情 →
        </Link>
      </div>
    </div>
  );
}

export default StockCard;
