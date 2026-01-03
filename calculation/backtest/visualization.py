import pandas as pd
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt

class BacktestVisualization:
    """Backtest result visualization"""

    @staticmethod
    def plot_equity_curve(portfolio: pd.DataFrame, title: str = "Equity Curve", save_path: Optional[str] = None):
        """Plot equity curve"""
        plt.figure(figsize=(12, 6))
        plt.plot(portfolio.index, portfolio['total'], label='Total Equity')
        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel('Equity')
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
            
    @staticmethod
    def plot_drawdown(portfolio: pd.DataFrame, save_path: Optional[str] = None):
        """Plot drawdown"""
        # Assuming drawdown is calculated in portfolio or calculate it here
        if 'drawdown' not in portfolio.columns:
             # Simple calculation if not present
             cum_max = portfolio['total'].cummax()
             drawdown = (portfolio['total'] - cum_max) / cum_max
        else:
            drawdown = portfolio['drawdown']
            
        plt.figure(figsize=(12, 4))
        plt.fill_between(portfolio.index, drawdown, 0, color='red', alpha=0.3)
        plt.title('Drawdown')
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
