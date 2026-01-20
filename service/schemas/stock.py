"""
Stock-related Pydantic schemas

Defines all request/response models for stock endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class StockInfo(BaseModel):
    """Basic stock information"""
    symbol: str = Field(..., description="Stock symbol (e.g., sh600000)")
    name: str = Field(..., description="Stock name")
    source: Optional[str] = Field(None, description="Data source")
    price: Optional[float] = Field(None, description="Current price")
    volume: Optional[float] = Field(None, description="Current volume")
    open: Optional[float] = Field(None, description="Open price")
    high: Optional[float] = Field(None, description="High price")
    low: Optional[float] = Field(None, description="Low price")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "name": "浦发银行",
                "source": "sina",
                "price": 10.50,
                "volume": 150000000,
                "open": 10.45,
                "high": 10.60,
                "low": 10.40
            }
        }


class StockQuote(BaseModel):
    """Stock quote for real-time data"""
    symbol: str = Field(..., description="Stock symbol")
    name: Optional[str] = Field(None, description="Stock name")
    price: float = Field(..., description="Current price", ge=0)
    change: Optional[float] = Field(None, description="Price change")
    change_percent: Optional[float] = Field(None, description="Price change percentage")
    volume: Optional[float] = Field(None, description="Volume", ge=0)
    open: Optional[float] = Field(None, description="Open price", ge=0)
    high: Optional[float] = Field(None, description="High price", ge=0)
    low: Optional[float] = Field(None, description="Low price", ge=0)
    timestamp: Optional[datetime] = Field(None, description="Data timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "name": "浦发银行",
                "price": 10.50,
                "change": 0.25,
                "change_percent": 2.35,
                "volume": 150000000,
                "open": 10.45,
                "high": 10.60,
                "low": 10.40,
                "timestamp": "2026-01-19T09:30:00"
            }
        }


class StockDailyData(BaseModel):
    """Stock daily OHLCV data"""
    symbol: str = Field(..., description="Stock symbol")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    open: float = Field(..., description="Open price", ge=0)
    high: float = Field(..., description="High price", ge=0)
    low: float = Field(..., description="Low price", ge=0)
    close: float = Field(..., description="Close price", ge=0)
    volume: float = Field(..., description="Volume", ge=0)

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
                "symbol": "sh600000",
                "date": "2026-01-19",
                "open": 10.45,
                "high": 10.60,
                "low": 10.40,
                "close": 10.50,
                "volume": 150000000
            }
        }


class StockListResponse(BaseModel):
    """Response for stock list endpoint"""
    stocks: List[StockInfo] = Field(..., description="List of stocks")
    total: int = Field(..., description="Total number of stocks", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "stocks": [
                    {
                        "symbol": "sh600000",
                        "name": "浦发银行",
                        "price": 10.50,
                        "volume": 150000000
                    }
                ],
                "total": 5000
            }
        }


class StockDetailResponse(StockInfo):
    """Detailed stock information"""
    daily_data: Optional[List[StockDailyData]] = Field(None, description="Recent daily data")
    market_cap: Optional[float] = Field(None, description="Market capitalization", ge=0)
    pe_ratio: Optional[float] = Field(None, description="P/E ratio", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "name": "浦发银行",
                "price": 10.50,
                "volume": 150000000,
                "market_cap": 105000000000,
                "pe_ratio": 8.5,
                "daily_data": []
            }
        }


class StockHistoryResponse(BaseModel):
    """Response for stock history endpoint"""
    symbol: str = Field(..., description="Stock symbol")
    data: List[StockDailyData] = Field(..., description="Historical data")
    total: int = Field(..., description="Total records", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "data": [
                    {
                        "symbol": "sh600000",
                        "date": "2026-01-19",
                        "open": 10.45,
                        "high": 10.60,
                        "low": 10.40,
                        "close": 10.50,
                        "volume": 150000000
                    }
                ],
                "total": 100
            }
        }


class MarketOverviewResponse(BaseModel):
    """Response for market overview endpoint"""
    date: Optional[str] = Field(None, description="Data date")
    total_volume: float = Field(..., description="Total market volume", ge=0)
    total_stocks: int = Field(..., description="Total number of stocks", ge=0)
    limit_up: int = Field(..., description="Number of limit-up stocks", ge=0)
    limit_down: int = Field(..., description="Number of limit-down stocks", ge=0)
    up: int = Field(..., description="Number of stocks up", ge=0)
    down: int = Field(..., description="Number of stocks down", ge=0)
    flat: int = Field(..., description="Number of flat stocks", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-01-19",
                "total_volume": 500000000000,
                "total_stocks": 5000,
                "limit_up": 50,
                "limit_down": 20,
                "up": 2500,
                "down": 2000,
                "flat": 430
            }
        }


class HotStockResponse(BaseModel):
    """Hot stock item response"""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Stock name")
    price: float = Field(..., description="Current price", ge=0)
    change_percent: float = Field(..., description="Change percentage")
    volume: float = Field(..., description="Volume", ge=0)
    reason: str = Field(..., description="Reason for being hot")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "name": "浦发银行",
                "price": 10.50,
                "change_percent": 2.35,
                "volume": 150000000,
                "reason": "成交量大"
            }
        }


class StockSearchResponse(BaseModel):
    """Response for stock search endpoint"""
    stocks: List[StockInfo] = Field(..., description="Search results")
    total: int = Field(..., description="Total results", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "stocks": [
                    {
                        "symbol": "sh600000",
                        "name": "浦发银行",
                        "price": 10.50
                    }
                ],
                "total": 10
            }
        }
