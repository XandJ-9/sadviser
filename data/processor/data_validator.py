import pandas as pd
import numpy as np
import logging
from typing import List

logger = logging.getLogger(__name__)

class DataValidator:
    """Data validation utility class"""

    @staticmethod
    def validate_columns(data: pd.DataFrame, required_columns: List[str]) -> bool:
        """Check if required columns exist"""
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            logger.error(f"Missing columns: {missing}")
            return False
        return True

    @staticmethod
    def check_outliers(data: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.DataFrame:
        """Check for outliers using Z-score"""
        z_scores = np.abs((data[column] - data[column].mean()) / data[column].std())
        outliers = data[z_scores > threshold]
        if not outliers.empty:
            logger.warning(f"Found {len(outliers)} outliers in {column}")
        return outliers
