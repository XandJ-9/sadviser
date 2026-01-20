"""
Strategy-related Pydantic schemas

Defines all request/response models for strategy endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class TradingSignal(BaseModel):
    """Trading signal information"""
    date: str = Field(..., description="Signal date (YYYY-MM-DD)")
    type: Literal["buy", "sell", "hold"] = Field(..., description="Signal type")
    price: float = Field(..., description="Signal price", ge=0)
    strength: Literal["strong", "weak", "neutral"] = Field(..., description="Signal strength")
    reason: str = Field(..., description="Reason for signal")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-01-19",
                "type": "buy",
                "price": 10.20,
                "strength": "strong",
                "reason": "MA金叉"
            }
        }


class StrategyInfo(BaseModel):
    """Basic strategy information"""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    price: float = Field(..., description="Current price", ge=0)
    change_percent: float = Field(..., description="Change percentage")
    volume: float = Field(..., description="Volume", ge=0)
    score: float = Field(..., description="Strategy score", ge=0, le=100)
    reasons: List[str] = Field(..., description="Reasons for recommendation")
    recommendation: str = Field(..., description="Recommendation text")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Technical indicators")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "name": "浦发银行",
                "price": 10.50,
                "change_percent": 2.35,
                "volume": 150000000,
                "score": 85.5,
                "reasons": ["均线多头排列", "MACD金叉"],
                "recommendation": "技术指标强势,均线呈多头排列,MACD出现金叉信号,短期看涨",
                "indicators": {
                    "ma5": 10.45,
                    "ma20": 10.30,
                    "rsi": 55.0,
                    "macd": 0.0025
                }
            }
        }


class DailyRecommendationsResponse(BaseModel):
    """Response for daily recommendations endpoint"""
    date: str = Field(..., description="Recommendation date (YYYY-MM-DD)")
    stocks: List[StrategyInfo] = Field(..., description="Recommended stocks")
    total: int = Field(..., description="Total recommendations", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-01-19",
                "stocks": [],
                "total": 50
            }
        }


class StockScreenRequest(BaseModel):
    """Request for stock screening"""
    min_price: Optional[float] = Field(None, description="Minimum price", ge=0)
    max_price: Optional[float] = Field(None, description="Maximum price", ge=0)
    min_volume: Optional[float] = Field(None, description="Minimum volume", ge=0)
    strategy: Optional[str] = Field(None, description="Strategy filter")
    market_cap: Optional[str] = Field(None, description="Market cap filter (small/mid/large)")
    sector: Optional[str] = Field(None, description="Sector filter")
    sort_by: Optional[str] = Field("volume", description="Sort field")
    sort_order: Literal["asc", "desc"] = Field("desc", description="Sort order")
    limit: int = Field(50, description="Result limit", ge=1, le=500)

    @field_validator('max_price')
    @classmethod
    def validate_price_range(cls, v: Optional[float], info) -> Optional[float]:
        """Validate max_price is greater than min_price"""
        if v is not None and 'min_price' in info.data and info.data['min_price'] is not None:
            if v < info.data['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "min_price": 10.0,
                "max_price": 50.0,
                "min_volume": 10000000,
                "strategy": "ma_cross",
                "market_cap": "mid",
                "sort_by": "volume",
                "sort_order": "desc",
                "limit": 50
            }
        }


class StockScreenResult(BaseModel):
    """Stock screen result item"""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    price: float = Field(..., description="Current price", ge=0)
    change_percent: float = Field(..., description="Change percentage")
    volume: float = Field(..., description="Volume", ge=0)
    reason: str = Field(..., description="Reason for inclusion")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600036",
                "name": "招商银行",
                "price": 35.50,
                "change_percent": 1.85,
                "volume": 85000000,
                "reason": "符合ma_cross策略筛选条件"
            }
        }


class StockScreenResponse(BaseModel):
    """Response for stock screening endpoint"""
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    stocks: List[StockScreenResult] = Field(..., description="Screened stocks")
    total: int = Field(..., description="Total results", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "filters": {},
                "stocks": [],
                "total": 20
            }
        }


class StrategyParameter(BaseModel):
    """Strategy parameter definition"""
    name: str = Field(..., description="Parameter name")
    type: Literal["int", "float", "str", "bool"] = Field(..., description="Parameter type")
    default: Any = Field(..., description="Default value")
    description: str = Field(..., description="Parameter description")
    min_value: Optional[float] = Field(None, description="Minimum value for numeric types")
    max_value: Optional[float] = Field(None, description="Maximum value for numeric types")
    options: Optional[List[Any]] = Field(None, description="Options for enum types")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "short_window",
                "type": "int",
                "default": 5,
                "description": "短期均线周期",
                "min_value": 1,
                "max_value": 100
            }
        }


class StrategyListItem(BaseModel):
    """Strategy list item"""
    id: str = Field(..., description="Strategy ID")
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    category: Optional[str] = Field(None, description="Strategy category")
    parameters: List[StrategyParameter] = Field(default_factory=list, description="Strategy parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ma_cross",
                "name": "均线交叉策略",
                "description": "基于短期和长期移动平均线的交叉产生买卖信号",
                "category": "trend",
                "parameters": [
                    {
                        "name": "short_window",
                        "type": "int",
                        "default": 5,
                        "description": "短期均线周期"
                    },
                    {
                        "name": "long_window",
                        "type": "int",
                        "default": 20,
                        "description": "长期均线周期"
                    }
                ]
            }
        }


class StrategyListResponse(BaseModel):
    """Response for strategy list endpoint"""
    strategies: List[StrategyListItem] = Field(..., description="Available strategies")
    total: int = Field(..., description="Total strategies", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "strategies": [],
                "total": 10
            }
        }
