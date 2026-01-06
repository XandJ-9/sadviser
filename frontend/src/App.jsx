import { Route, Router } from 'wouter';
import HomePage from './pages/HomePage';
import StockListPage from './pages/StockListPage';
import StockDetailPage from './pages/StockDetailPage';
import DataManagementPage from './pages/DataManagementPage';
import './styles/App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <a href="/" className="nav-logo">
              📈 sadviser
            </a>
            <div className="nav-links">
              <a href="/" className="nav-link">首页</a>
              <a href="/stocks" className="nav-link">A股列表</a>
              <a href="/data" className="nav-link">数据管理</a>
              <a href="/backtest" className="nav-link">回测分析</a>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Route path="/" component={HomePage} />
          <Route path="/stocks" component={StockListPage} />
          <Route path="/stocks/:symbol" component={StockDetailPage} />
          <Route path="/data" component={DataManagementPage} />
        </main>

        <footer className="footer">
          <div className="footer-container">
            <p>© 2026 sadviser - 股票投资建议平台</p>
            <p className="footer-note">
              ⚠️ 投资有风险,本平台内容仅供参考,不构成投资建议
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
