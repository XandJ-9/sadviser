import pandas as pd
import numpy as np
import talib
from typing import Dict, Optional, Any, List

from .base_indicator import BaseIndicator

class VolumeIndicators(BaseIndicator):
    """Volume based indicators"""

    def __init__(self, name: str = "volume_ind", params: Optional[Dict[str, Any]] = None):
        """
        Initialize volume indicators
        :param name: Indicator name
        :param params: Indicator parameters
                      - type: "obv", "ad", "adosc"
        """
        default_params = {
            "type": "obv",
            "fastperiod": 3,
            "slowperiod": 10
        }
        if params:
            default_params.update(params)
        super().__init__(name, default_params)

    def validate_params(self) -> None:
        valid_types = ["obv", "ad", "adosc"]
        if self.params["type"].lower() not in valid_types:
            raise ValueError(f"Invalid volume indicator type: {self.params['type']}")

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.check_required_data(data):
            return pd.DataFrame()

        ind_type = self.params["type"].lower()
        column_name = self.name

        if ind_type == "obv":
            data[column_name] = talib.OBV(data["close"].values, data["volume"].values)
        elif ind_type == "ad":
            data[column_name] = talib.AD(data["high"].values, data["low"].values, 
                                       data["close"].values, data["volume"].values)
        elif ind_type == "adosc":
            data[column_name] = talib.ADOSC(data["high"].values, data["low"].values,
                                          data["close"].values, data["volume"].values,
                                          fastperiod=self.params["fastperiod"],
                                          slowperiod=self.params["slowperiod"])
        
        self.results = data[[column_name]]
        return data
