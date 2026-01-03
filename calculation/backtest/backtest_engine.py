from typing import Dict, Any, Optional, Union
import pandas as pd
from .normal_backtest import NormalBacktest
from ..strategies.base_strategy import BaseStrategy

class BacktestEngine:
    """Backtest Engine Facade"""

    @staticmethod
    def run(data: pd.DataFrame, 
            strategy: BaseStrategy, 
            initial_capital: float = 100000.0,
            **kwargs) -> Dict[str, Any]:
        """
        Run a backtest
        """
        backtest = NormalBacktest(
            data=data,
            strategy=strategy,
            initial_capital=initial_capital,
            **kwargs
        )
        backtest.run()
        
        # In a real engine, we would return a result object with analyzer and visualizer attached
        # For now, return the performance dict
        return backtest.get_performance()
