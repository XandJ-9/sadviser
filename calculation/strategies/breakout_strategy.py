import pandas as pd
import numpy as np
from typing import Dict, Optional, Any, List

from .base_strategy import BaseStrategy
from ..indicators.base_indicator import BaseIndicator

class BreakoutStrategy(BaseStrategy):
    """Breakout strategy (e.g., Donchian Channel Breakout)"""

    def __init__(self, name: str = "breakout", params: Optional[Dict[str, Any]] = None, indicators: Optional[List[BaseIndicator]] = None):
        default_params = {
            "window": 20
        }
        if params:
            default_params.update(params)
        super().__init__(name, default_params, indicators)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        window = self.params["window"]
        
        # Calculate Donchian Channels
        data["upper"] = data["high"].rolling(window=window).max()
        data["lower"] = data["low"].rolling(window=window).min()
        
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0
        
        # Breakout logic
        # Buy when close > previous upper channel
        # Sell when close < previous lower channel
        signals.loc[data["close"] > data["upper"].shift(1), "signal"] = 1
        signals.loc[data["close"] < data["lower"].shift(1), "signal"] = -1
        
        return signals
