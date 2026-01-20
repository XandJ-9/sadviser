"""
Pydantic schemas for request/response validation

This module contains all Pydantic models used for:
- Request validation (incoming API requests)
- Response serialization (outgoing API responses)
- Database models (ORM models)

Following FastAPI best practices for type safety and automatic documentation.
"""

from service.schemas.stock import (
    StockInfo,
    StockQuote,
    StockDailyData,
    StockListResponse,
    StockDetailResponse,
    StockHistoryResponse,
    MarketOverviewResponse,
    HotStockResponse,
    StockSearchResponse
)

from service.schemas.strategy import (
    StrategyInfo,
    TradingSignal,
    DailyRecommendationsResponse,
    StockScreenRequest,
    StockScreenResponse,
    StrategyListResponse
)

from service.schemas.backtest import (
    BacktestRequest,
    BacktestResult,
    BacktestResponse,
    BacktestMetrics
)

from service.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse
)

__all__ = [
    # Stock schemas
    "StockInfo",
    "StockQuote",
    "StockDailyData",
    "StockListResponse",
    "StockDetailResponse",
    "StockHistoryResponse",
    "MarketOverviewResponse",
    "HotStockResponse",
    "StockSearchResponse",

    # Strategy schemas
    "StrategyInfo",
    "TradingSignal",
    "DailyRecommendationsResponse",
    "StockScreenRequest",
    "StockScreenResponse",
    "StrategyListResponse",

    # Backtest schemas
    "BacktestRequest",
    "BacktestResult",
    "BacktestResponse",
    "BacktestMetrics",

    # Task schemas
    "TaskCreateRequest",
    "TaskResponse",
    "TaskListResponse",
]
