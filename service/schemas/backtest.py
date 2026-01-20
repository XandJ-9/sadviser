"""
Backtest-related Pydantic schemas

Defines all request/response models for backtest endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class BacktestRequest(BaseModel):
    """Request for backtesting"""
    symbol: str = Field(..., description="Stock symbol")
    strategy_id: str = Field(..., description="Strategy ID")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(100000.0, description="Initial capital", gt=0)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Strategy parameters")
    commission_rate: float = Field(0.0003, description="Commission rate", ge=0, le=0.1)
    slippage_rate: float = Field(0.0001, description="Slippage rate", ge=0, le=0.1)

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        """Validate end_date is after start_date"""
        if 'start_date' in info.data:
            start_date = info.data['start_date']
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(v, '%Y-%m-%d')
                if end <= start:
                    raise ValueError('end_date must be after start_date')
            except ValueError as e:
                if 'must be after' not in str(e):
                    raise e
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "strategy_id": "ma_cross",
                "start_date": "2025-01-01",
                "end_date": "2026-01-19",
                "initial_capital": 100000.0,
                "parameters": {
                    "short_window": 5,
                    "long_window": 20
                },
                "commission_rate": 0.0003,
                "slippage_rate": 0.0001
            }
        }


class BacktestMetrics(BaseModel):
    """Backtest performance metrics"""
    total_return: float = Field(..., description="Total return percentage")
    annual_return: float = Field(..., description="Annualized return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    win_rate: float = Field(..., description="Win rate percentage", ge=0, le=100)
    profit_factor: float = Field(..., description="Profit factor", ge=0)
    total_trades: int = Field(..., description="Total number of trades", ge=0)
    profitable_trades: int = Field(..., description="Number of profitable trades", ge=0)
    loss_trades: int = Field(..., description="Number of loss trades", ge=0)
    avg_trade_return: float = Field(..., description="Average trade return percentage")
    final_capital: float = Field(..., description="Final capital amount", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "total_return": 25.5,
                "annual_return": 18.2,
                "sharpe_ratio": 1.5,
                "max_drawdown": -8.5,
                "win_rate": 65.0,
                "profit_factor": 2.1,
                "total_trades": 50,
                "profitable_trades": 32,
                "loss_trades": 18,
                "avg_trade_return": 0.51,
                "final_capital": 125500.0
            }
        }


class BacktestTrade(BaseModel):
    """Individual backtest trade"""
    entry_date: str = Field(..., description="Entry date (YYYY-MM-DD)")
    exit_date: Optional[str] = Field(None, description="Exit date (YYYY-MM-DD)")
    type: Literal["buy", "sell"] = Field(..., description="Trade type")
    price: float = Field(..., description="Trade price", ge=0)
    quantity: int = Field(..., description="Trade quantity", gt=0)
    value: float = Field(..., description="Trade value", ge=0)
    return_pct: Optional[float] = Field(None, description="Return percentage")
    profit: Optional[float] = Field(None, description="Profit/Loss amount")

    class Config:
        json_schema_extra = {
            "example": {
                "entry_date": "2025-01-05",
                "exit_date": "2025-01-15",
                "type": "buy",
                "price": 10.50,
                "quantity": 1000,
                "value": 10500.0,
                "return_pct": 2.5,
                "profit": 250.0
            }
        }


class BacktestResult(BaseModel):
    """Detailed backtest result"""
    symbol: str = Field(..., description="Stock symbol")
    strategy_id: str = Field(..., description="Strategy ID")
    start_date: str = Field(..., description="Backtest start date")
    end_date: str = Field(..., description="Backtest end date")
    metrics: BacktestMetrics = Field(..., description="Performance metrics")
    trades: List[BacktestTrade] = Field(default_factory=list, description="Trade history")
    equity_curve: Optional[List[Dict[str, Any]]] = Field(None, description="Equity curve data")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "strategy_id": "ma_cross",
                "start_date": "2025-01-01",
                "end_date": "2026-01-19",
                "metrics": {},
                "trades": [],
                "equity_curve": []
            }
        }


class BacktestResponse(BaseModel):
    """Response for backtest endpoint"""
    success: bool = Field(..., description="Whether backtest succeeded")
    message: str = Field(..., description="Response message")
    result: Optional[BacktestResult] = Field(None, description="Backtest result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Backtest completed successfully",
                "result": None,
                "error": None
            }
        }


class BacktestListRequest(BaseModel):
    """Request for backtest list"""
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    strategy_id: Optional[str] = Field(None, description="Filter by strategy ID")
    limit: int = Field(20, description="Result limit", ge=1, le=100)
    offset: int = Field(0, description="Result offset", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "sh600000",
                "strategy_id": "ma_cross",
                "limit": 20,
                "offset": 0
            }
        }


class BacktestSummary(BaseModel):
    """Backtest summary item for list view"""
    backtest_id: str = Field(..., description="Backtest ID")
    symbol: str = Field(..., description="Stock symbol")
    strategy_id: str = Field(..., description="Strategy ID")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    total_return: float = Field(..., description="Total return percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    created_at: datetime = Field(..., description="Backtest creation time")

    class Config:
        json_schema_extra = {
            "example": {
                "backtest_id": "bt_123456",
                "symbol": "sh600000",
                "strategy_id": "ma_cross",
                "start_date": "2025-01-01",
                "end_date": "2026-01-19",
                "total_return": 25.5,
                "sharpe_ratio": 1.5,
                "max_drawdown": -8.5,
                "created_at": "2026-01-19T10:30:00"
            }
        }


class BacktestListResponse(BaseModel):
    """Response for backtest list endpoint"""
    backtests: List[BacktestSummary] = Field(..., description="Backtest summaries")
    total: int = Field(..., description="Total backtests", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "backtests": [],
                "total": 10
            }
        }
