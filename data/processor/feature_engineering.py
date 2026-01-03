import pandas as pd
import numpy as np
from typing import List

class FeatureEngineering:
    """Feature engineering utility class"""

    @staticmethod
    def add_log_return(data: pd.DataFrame, column: str = 'close') -> pd.DataFrame:
        """Add log return column"""
        data[f'log_return_{column}'] = np.log(data[column] / data[column].shift(1))
        return data

    @staticmethod
    def add_moving_average(data: pd.DataFrame, window: int, column: str = 'close') -> pd.DataFrame:
        """Add moving average column"""
        data[f'ma_{window}'] = data[column].rolling(window=window).mean()
        return data

    @staticmethod
    def add_volatility(data: pd.DataFrame, window: int, column: str = 'close') -> pd.DataFrame:
        """Add volatility (standard deviation) column"""
        data[f'volatility_{window}'] = data[column].rolling(window=window).std()
        return data
