import pandas as pd
import numpy as np
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    """Data cleaning utility class"""
    
    @staticmethod
    def remove_duplicates(data: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """Remove duplicate rows"""
        initial_len = len(data)
        data = data.drop_duplicates(subset=subset)
        if len(data) < initial_len:
            logger.info(f"Removed {initial_len - len(data)} duplicate rows")
        return data

    @staticmethod
    def fill_missing_values(data: pd.DataFrame, method: str = 'ffill') -> pd.DataFrame:
        """Fill missing values"""
        if data.isnull().any().any():
            data = data.fillna(method=method).fillna(method='bfill')
            logger.info("Filled missing values")
        return data

    @staticmethod
    def normalize_columns(data: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to lowercase"""
        data.columns = [col.lower().strip() for col in data.columns]
        return data
