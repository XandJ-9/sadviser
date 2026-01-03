/**
 * 数据管理页面
 */
import { useState, useEffect } from 'react';
import DataFetchForm from '../components/DataFetchForm';
import TaskList from '../components/TaskList';
import SystemStatus from '../components/SystemStatus';
import { getSystemStatus } from '../api/data';
import '../styles/DataManagementPage.css';

function DataManagementPage() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  // 获取系统状态
  const fetchSystemStatus = async () => {
    try {
      const status = await getSystemStatus();
      setSystemStatus(status);
    } catch (err) {
      console.error('获取系统状态失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    // 每5秒刷新一次系统状态
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // 处理任务创建
  const handleTaskCreated = () => {
    setRefreshKey(prev => prev + 1);
    fetchSystemStatus();
  };

  return (
    <div className="data-management-page">
      <div className="page-header">
        <h1>数据管理</h1>
        <p className="page-subtitle">数据获取与存储任务管理</p>
      </div>

      {/* 系统状态卡片 */}
      <SystemStatus status={systemStatus} loading={loading} />

      <div className="management-content">
        {/* 左侧：数据获取表单 */}
        <div className="form-section">
          <h2>创建数据获取任务</h2>
          <DataFetchForm onTaskCreated={handleTaskCreated} />
        </div>

        {/* 右侧：任务列表 */}
        <div className="tasks-section">
          <h2>任务列表</h2>
          <TaskList refreshKey={refreshKey} />
        </div>
      </div>
    </div>
  );
}

export default DataManagementPage;
