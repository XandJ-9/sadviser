/**
 * 分页组件
 */
import '../styles/Pagination.css';

function Pagination({
  currentPage = 1,
  totalPages = 1,
  pageSize = 20,
  total = 0,
  onPageChange,
  onPageSizeChange
}) {
  // 计算显示的页码范围
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 7; // 最多显示7个页码

    if (totalPages <= maxPagesToShow) {
      // 如果总页数小于等于最大显示数，显示所有页码
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 否则需要省略显示
      if (currentPage <= 4) {
        // 当前页在前部
        for (let i = 1; i <= 5; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 3) {
        // 当前页在后部
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        // 当前页在中部
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  const handlePageClick = (page) => {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      onPageChange(page);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  const startRecord = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endRecord = Math.min(currentPage * pageSize, total);

  return (
    <div className="pagination">
      <div className="pagination-info">
        <span>
          显示 {startRecord} - {endRecord} 条，共 {total} 条
        </span>
      </div>

      <div className="pagination-controls">
        {/* 每页显示数量选择器 */}
        {onPageSizeChange && (
          <div className="page-size-selector">
            <span>每页显示：</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="page-size-select"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        )}

        {/* 分页按钮 */}
        <div className="page-buttons">
          <button
            className="page-btn page-btn-prev"
            onClick={handlePrevPage}
            disabled={currentPage === 1}
          >
            上一页
          </button>

          {getPageNumbers().map((page, index) => (
            <button
              key={index}
              className={`page-btn ${page === currentPage ? 'page-btn-active' : ''} ${page === '...' ? 'page-btn-ellipsis' : ''}`}
              onClick={() => handlePageClick(page)}
              disabled={page === '...'}
            >
              {page}
            </button>
          ))}

          <button
            className="page-btn page-btn-next"
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
}

export default Pagination;
