import pandas as pd
from typing import Dict, Any
from .performance_metrics import PerformanceMetrics

class ResultAnalyzer:
    """Backtest result analysis"""

    def __init__(self, portfolio: pd.DataFrame, trades: pd.DataFrame):
        self.portfolio = portfolio
        self.trades = trades

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        returns = self.portfolio['returns']
        
        return {
            "total_return": (self.portfolio['total'].iloc[-1] / self.portfolio['total'].iloc[0]) - 1,
            "sharpe_ratio": PerformanceMetrics.calculate_sharpe_ratio(returns),
            "max_drawdown": PerformanceMetrics.calculate_max_drawdown(returns),
            "win_rate": PerformanceMetrics.calculate_win_rate(self.trades),
            "total_trades": len(self.trades)
        }
