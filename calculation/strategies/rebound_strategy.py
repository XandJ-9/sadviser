import pandas as pd
import numpy as np
import talib
from typing import Dict, Optional, Any, List

from .base_strategy import BaseStrategy
from ..indicators.base_indicator import BaseIndicator

class ReboundStrategy(BaseStrategy):
    """Rebound strategy (e.g., RSI Rebound)"""

    def __init__(self, name: str = "rebound", params: Optional[Dict[str, Any]] = None, indicators: Optional[List[BaseIndicator]] = None):
        default_params = {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70
        }
        if params:
            default_params.update(params)
        super().__init__(name, default_params, indicators)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        period = self.params["rsi_period"]
        oversold = self.params["oversold"]
        overbought = self.params["overbought"]
        
        # Calculate RSI if not present
        if "rsi" not in data.columns:
            data["rsi"] = talib.RSI(data["close"].values, timeperiod=period)
            
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0
        
        # Rebound logic
        # Buy when RSI crosses above oversold level
        # Sell when RSI crosses below overbought level
        
        rsi = data["rsi"]
        prev_rsi = rsi.shift(1)
        
        signals.loc[(prev_rsi < oversold) & (rsi >= oversold), "signal"] = 1
        signals.loc[(prev_rsi > overbought) & (rsi <= overbought), "signal"] = -1
        
        return signals
