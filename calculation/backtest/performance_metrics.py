import pandas as pd
import numpy as np
from typing import Dict, Any

class PerformanceMetrics:
    """Performance metrics calculation"""

    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods: int = 252) -> float:
        """Calculate Sharpe Ratio"""
        if returns.std() == 0:
            return 0.0
        return np.sqrt(periods) * (returns.mean() - risk_free_rate) / returns.std()

    @staticmethod
    def calculate_max_drawdown(returns: pd.Series) -> float:
        """Calculate Maximum Drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    @staticmethod
    def calculate_win_rate(trades: pd.DataFrame) -> float:
        """Calculate Win Rate"""
        if trades.empty:
            return 0.0
        winning_trades = len(trades[trades['net_profit'] > 0])
        return winning_trades / len(trades)
