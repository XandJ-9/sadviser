/**
 * 任务列表组件
 */
import { useState, useEffect } from 'react';
import { getTasks } from '../api/data';
import '../styles/TaskList.css';

function TaskList({ refreshKey }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 获取任务列表
  const fetchTasks = async () => {
    // Only show loading on initial load or if explicitly refreshed, not during auto-refresh
    if (tasks.length === 0) {
      setLoading(true);
    }
    setError(null);

    try {
      const taskList = await getTasks();
      setTasks(taskList);
    } catch (err) {
      console.error('获取任务列表失败:', err);
      // Don't show error if it's just a background refresh failure
      if (tasks.length === 0) {
        setError(err.message || '获取任务列表失败');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    // 每3秒刷新一次任务状态
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, [refreshKey]);

  // 获取状态样式
  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'status-completed';
      case 'running':
        return 'status-running';
      case 'failed':
        return 'status-failed';
      case 'pending':
        return 'status-pending';
      default:
        return '';
    }
  };

  // 获取状态文本
  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'running':
        return '进行中';
      case 'failed':
        return '失败';
      case 'pending':
        return '等待中';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="task-list task-list-loading">
        <div className="loading-spinner"></div>
        <p>加载任务列表...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="task-list task-list-error">
        <p>{error}</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="task-list task-list-empty">
        <p>暂无任务</p>
        <small>创建数据获取任务后将在此显示</small>
      </div>
    );
  }

  return (
    <div className="task-list">
      <div className="task-list-header">
        <h3>任务列表</h3>
        <button className="refresh-btn" onClick={fetchTasks}>
          刷新
        </button>
      </div>

      <div className="task-items">
        {tasks.map((task) => (
          <div key={task.id} className="task-item">
            <div className="task-header">
              <span className="task-id">{task.id}</span>
              <span className={`task-status ${getStatusClass(task.status)}`}>
                {getStatusText(task.status)}
              </span>
            </div>

            <div className="task-body">
              {task.message && (
                <div className="task-message">{task.message}</div>
              )}

              {task.progress !== undefined && (
                <div className="task-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${task.progress}%` }}
                    ></div>
                  </div>
                  <span className="progress-text">{task.progress}%</span>
                </div>
              )}

              <div className="task-details">
                {task.created_at && (
                  <div className="task-detail">
                    <span className="detail-label">创建时间:</span>
                    <span className="detail-value">
                      {new Date(task.created_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                )}

                {task.success !== undefined && (
                  <div className="task-detail">
                    <span className="detail-label">成功:</span>
                    <span className="detail-value success-count">{task.success}</span>
                  </div>
                )}

                {task.failed !== undefined && (
                  <div className="task-detail">
                    <span className="detail-label">失败:</span>
                    <span className="detail-value failed-count">{task.failed}</span>
                  </div>
                )}

                {task.total !== undefined && (
                  <div className="task-detail">
                    <span className="detail-label">总计:</span>
                    <span className="detail-value">{task.total}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TaskList;
