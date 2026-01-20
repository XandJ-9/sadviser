/**
 * 数据获取表单组件
 * 已更新为后台任务模式 - 所有接口都返回任务信息，数据在后台异步获取
 */
import { useState } from 'react';
import { fetchHistoryData, fetchRealtimeData, fetchStockList } from '../api/data';
import '../styles/DataFetchForm.css';

function DataFetchForm({ onTaskCreated }) {
  const [taskType, setTaskType] = useState('history'); // history, realtime, stocklist
  const [symbols, setSymbols] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [source, setSource] = useState('akshare');
  const [priority, setPriority] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      let response;

      if (taskType === 'history') {
        // 获取历史数据 - 创建后台任务
        const symbolList = symbols.split(',').map(s => s.trim()).filter(s => s);
        if (symbolList.length === 0) {
          throw new Error('请输入至少一个股票代码');
        }

        response = await fetchHistoryData({
          symbols: symbolList,
          start_date: startDate,
          end_date: endDate,
          source,
          priority
        });
      } else if (taskType === 'realtime') {
        // 获取实时行情 - 创建后台任务
        const symbolList = symbols.split(',').map(s => s.trim()).filter(s => s);
        if (symbolList.length === 0) {
          throw new Error('请输入至少一个股票代码');
        }

        response = await fetchRealtimeData({
          symbols: symbolList,
          source,
          store: true  // 默认存储到数据库
        });
      } else if (taskType === 'stocklist') {
        // 获取股票列表 - 创建后台任务
        response = await fetchStockList({
          source,
          store: true,  // 默认存储到数据库
          force_refresh: false
        });
      }

      setResult(response);
      if (onTaskCreated) {
        onTaskCreated();
      }
    } catch (err) {
      console.error('创建任务失败:', err);
      setError(err.response?.data?.detail || err.message || '创建任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 设置默认日期（最近30天）
  const setDefaultDates = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);

    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
  };

  return (
    <form className="data-fetch-form" onSubmit={handleSubmit}>
      {/* 任务类型选择 */}
      <div className="form-group">
        <label className="form-label">任务类型</label>
        <div className="task-type-selector">
          <button
            type="button"
            className={`task-type-btn ${taskType === 'history' ? 'active' : ''}`}
            onClick={() => setTaskType('history')}
          >
            历史数据
          </button>
          <button
            type="button"
            className={`task-type-btn ${taskType === 'realtime' ? 'active' : ''}`}
            onClick={() => setTaskType('realtime')}
          >
            实时行情
          </button>
          <button
            type="button"
            className={`task-type-btn ${taskType === 'stocklist' ? 'active' : ''}`}
            onClick={() => setTaskType('stocklist')}
          >
            股票列表
          </button>
        </div>
      </div>

      {/* 股票代码（历史数据和实时行情需要） */}
      {taskType !== 'stocklist' && (
        <div className="form-group">
          <label className="form-label">股票代码</label>
          <input
            type="text"
            className="form-input"
            placeholder="例如: 000001, 000002, 600000（用逗号分隔）"
            value={symbols}
            onChange={(e) => setSymbols(e.target.value)}
            required
          />
          <small className="form-hint">多个股票代码用逗号分隔</small>
        </div>
      )}

      {/* 日期范围（仅历史数据需要） */}
      {taskType === 'history' && (
        <>
          <div className="form-group">
            <label className="form-label">开始日期</label>
            <input
              type="date"
              className="form-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              结束日期
              <button
                type="button"
                className="date-hint-btn"
                onClick={setDefaultDates}
              >
                设置最近30天
              </button>
            </label>
            <input
              type="date"
              className="form-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
          </div>
        </>
      )}

      {/* 数据源选择 */}
      <div className="form-group">
        <label className="form-label">数据源</label>
        <select
          className="form-select"
          value={source}
          onChange={(e) => setSource(e.target.value)}
        >
          <option value="akshare">Akshare (东方财富)</option>
          <option value="sina">Sina (新浪财经)</option>
          <option value="tushare">Tushare (需要Token)</option>
        </select>
      </div>

      {/* 任务优先级选择（仅历史数据任务） */}
      {taskType === 'history' && (
        <div className="form-group">
          <label className="form-label">任务优先级</label>
          <select
            className="form-select"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="low">低</option>
            <option value="medium">中</option>
            <option value="high">高</option>
          </select>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="form-error">
          {error}
        </div>
      )}

      {/* 成功结果 */}
      {result && (
        <div className="form-success">
          <div className="result-title">任务创建成功</div>
          {result.task_id && (
            <div className="result-item">
              <span className="result-label">任务ID:</span>
              <span className="result-value">{result.task_id}</span>
            </div>
          )}
          {result.message && (
            <div className="result-item">
              <span className="result-label">消息:</span>
              <span className="result-value">{result.message}</span>
            </div>
          )}
          {result.count !== undefined && (
            <div className="result-item">
              <span className="result-label">数量:</span>
              <span className="result-value">{result.count}</span>
            </div>
          )}
        </div>
      )}

      {/* 提交按钮 */}
      <div className="form-actions">
        <button
          type="submit"
          className="submit-btn"
          disabled={loading}
        >
          {loading ? '创建中...' : '创建任务'}
        </button>
      </div>
    </form>
  );
}

export default DataFetchForm;
