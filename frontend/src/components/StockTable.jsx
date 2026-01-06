/**
 * 股票表格组件 - 按行展示
 */
import { Link } from 'wouter';
import '../styles/StockTable.css';

function StockTable({ stocks }) {
  // 判断涨跌
  const getChangeClass = (changePercent) => {
    if (changePercent > 0) return 'positive';
    if (changePercent < 0) return 'negative';
    return '';
  };

  // 格式化数字
  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  // 格式化成交量
  const formatVolume = (volume) => {
    if (!volume) return '-';
    if (volume >= 100000000) {
      return `${(volume / 100000000).toFixed(2)}亿`;
    } else if (volume >= 10000) {
      return `${(volume / 10000).toFixed(2)}万`;
    }
    return volume.toLocaleString();
  };

  if (!stocks || stocks.length === 0) {
    return (
      <div className="stock-table-container">
        <div className="stock-table-empty">
          <p>暂无数据</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-table-container">
      <table className="stock-table">
        <thead>
          <tr>
            <th className="col-symbol">代码</th>
            <th className="col-name">名称</th>
            <th className="col-price">现价</th>
            <th className="col-change">涨跌幅</th>
            <th className="col-volume">成交量</th>
            <th className="col-ma5">MA5</th>
            <th className="col-ma20">MA20</th>
            <th className="col-action">操作</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, index) => {
            const changeClass = getChangeClass(stock.changePercent);
            const changeSign = stock.changePercent >= 0 ? '+' : '';

            return (
              <tr key={stock.symbol || index} className="stock-table-row">
                <td className="col-symbol">
                  <span className="symbol-text">{stock.symbol}</span>
                </td>
                <td className="col-name">
                  <span className="name-text">{stock.name}</span>
                </td>
                <td className="col-price">
                  <span className="price-text">¥{formatNumber(stock.price)}</span>
                </td>
                <td className="col-change">
                  <span className={`change-text ${changeClass}`}>
                    {changeSign}{formatNumber(stock.changePercent)}%
                  </span>
                </td>
                <td className="col-volume">
                  <span className="volume-text">{formatVolume(stock.volume)}</span>
                </td>
                <td className="col-ma5">
                  <span className="indicator-text">
                    {stock.indicators?.ma5 ? formatNumber(stock.indicators.ma5) : '-'}
                  </span>
                </td>
                <td className="col-ma20">
                  <span className="indicator-text">
                    {stock.indicators?.ma20 ? formatNumber(stock.indicators.ma20) : '-'}
                  </span>
                </td>
                <td className="col-action">
                  <Link href={`/stocks/${stock.symbol}`} className="detail-btn">
                    详情
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default StockTable;
