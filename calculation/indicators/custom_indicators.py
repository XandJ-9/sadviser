import pandas as pd
import numpy as np
from typing import Dict, Optional, Any

from .base_indicator import BaseIndicator

class CustomIndicators(BaseIndicator):
    """Custom composite indicators"""

    def __init__(self, name: str = "custom", params: Optional[Dict[str, Any]] = None):
        default_params = {
            "type": "pvt" # Price Volume Trend
        }
        if params:
            default_params.update(params)
        super().__init__(name, default_params)

    def validate_params(self) -> None:
        pass

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.check_required_data(data):
            return pd.DataFrame()
            
        ind_type = self.params["type"].lower()
        column_name = self.name

        if ind_type == "pvt":
            # PVT = (Close - PreviousClose) / PreviousClose * Volume + PreviousPVT
            close_diff = data["close"].diff()
            close_shift = data["close"].shift(1)
            pvt = (close_diff / close_shift) * data["volume"]
            data[column_name] = pvt.cumsum()
        
        self.results = data[[column_name]]
        return data
