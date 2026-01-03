import pandas as pd
from typing import List

class FeatureSelector:
    """Feature selection utility"""
    
    @staticmethod
    def select_k_best(X: pd.DataFrame, y: pd.Series, k: int = 10) -> List[str]:
        """Select top k features"""
        # Placeholder for actual implementation using sklearn
        return list(X.columns[:k])
