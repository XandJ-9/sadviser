import { Route, Router } from 'wouter';
import HomePage from './pages/HomePage';
import StockListPage from './pages/StockListPage';
import StockDetailPage from './pages/StockDetailPage';
import DataManagementPage from './pages/DataManagementPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-gray-50">
        {/* Navigation */}
        <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <a href="/" className="flex items-center gap-2 text-2xl font-bold text-blue-600 hover:text-blue-700 transition-colors">
                📈 sadviser
              </a>
              <div className="flex items-center gap-1">
                <a href="/" className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-lg transition-all duration-200">
                  首页
                </a>
                <a href="/stocks" className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-lg transition-all duration-200">
                  A股列表
                </a>
                <a href="/data" className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-lg transition-all duration-200">
                  数据管理
                </a>
                <a href="/backtest" className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-blue-600 rounded-lg transition-all duration-200">
                  回测分析
                </a>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 py-8">
          <Route path="/" component={HomePage} />
          <Route path="/stocks" component={StockListPage} />
          <Route path="/stocks/:symbol" component={StockDetailPage} />
          <Route path="/data" component={DataManagementPage} />
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center">
              <p className="text-sm text-gray-600">© 2026 sadviser - 股票投资建议平台</p>
              <p className="mt-1 text-xs text-gray-500">
                ⚠️ 投资有风险，本平台内容仅供参考，不构成投资建议
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
