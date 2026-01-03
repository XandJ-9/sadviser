/**
 * 系统状态组件
 */
import '../styles/SystemStatus.css';

function SystemStatus({ status, loading }) {
  if (loading) {
    return (
      <div className="system-status system-status-loading">
        <div className="status-loading">加载中...</div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="system-status system-status-error">
        <div className="status-error">无法获取系统状态</div>
      </div>
    );
  }

  return (
    <div className="system-status">
      <div className="status-header">
        <h3>系统状态</h3>
        <span className={`status-indicator ${status.storage_connected ? 'connected' : 'disconnected'}`}>
          {status.storage_connected ? '已连接' : '未连接'}
        </span>
      </div>

      <div className="status-metrics">
        <div className="metric">
          <div className="metric-label">活跃任务</div>
          <div className="metric-value">{status.active_tasks || 0}</div>
        </div>

        <div className="metric">
          <div className="metric-label">已完成任务</div>
          <div className="metric-value">{status.completed_tasks || 0}</div>
        </div>

        <div className="metric">
          <div className="metric-label">总任务数</div>
          <div className="metric-value">{status.total_tasks || 0}</div>
        </div>

        <div className="metric">
          <div className="metric-label">更新时间</div>
          <div className="metric-value metric-time">
            {new Date(status.timestamp).toLocaleString('zh-CN')}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SystemStatus;
