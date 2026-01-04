# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**sadviser** is a stock investment advisory platform based on technical indicators. The system provides stock screening, strategy backtesting, and investment recommendations through a full-stack architecture with Python backend and React frontend.

### Core Architecture

The codebase follows a modular pipeline architecture: **Data → Calculation → Service → Frontend**

- **Data Layer**: Multi-source data crawling (Sina, Tushare, WebSocket) with flexible storage backends (PostgreSQL, MongoDB, Redis, Parquet)
- **Calculation Layer**: Technical indicators, trading strategies, and backtesting engine
- **Service Layer**: FastAPI REST APIs with async task scheduling
- **Frontend**: React 19 + Vite with Tailwind CSS

## Development Commands

### Backend (Python)

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run backend development server
uv run main.py

# Run specific tests
uv run pytest tests/test_simple_logging.py
uv run pytest tests/test_sina_stock.py
```

### Frontend (React)

```bash
cd frontend

# Install dependencies (uses pnpm)
pnpm install

# Run development server
pnpm dev

# Build for production
pnpm build

# Run linter
pnpm lint
```

## Code Architecture

### Base Class Pattern

The codebase extensively uses abstract base classes to define interfaces. When implementing new features:

1. **Data Crawlers** (`data/crawler/`): Inherit from `BaseCrawler`
   - Implement `fetch_daily_data()` for historical data
   - Implement `fetch_realtime_quote()` for real-time quotes
   - Supports async context managers with automatic retry logic

2. **Storage Backends** (`data/storage/`): Inherit from `BaseStorage`
   - All CRUD operations are async: `connect()`, `insert()`, `query()`, etc.
   - Automatic timestamp management via `_add_timestamps()`
   - Unified exception handling via `_handle_exception()`

3. **Technical Indicators** (`calculation/indicators/`): Inherit from `BaseIndicator`
   - Implement `calculate()` method
   - Override `validate_params()` for parameter validation
   - Use `check_required_data()` to validate input data
   - Access results via `get_results()`

4. **Trading Strategies** (`calculation/strategies/`): Inherit from `BaseStrategy`
   - Implement `generate_signals()` returning signals (1=buy, 0=hold, -1=sell)
   - Override `validate_params()` for parameter validation
   - Use `calculate_indicators()` to compute required indicators
   - Built-in performance evaluation via `evaluate()`

5. **Backtesting** (`calculation/backtest/`): Inherit from `BaseBacktest`
   - Implement `run()` with actual backtest logic
   - Implement `calculate_metrics()` for performance statistics
   - Data validation via `_validate_and_prepare_data()`

### Combiner Pattern

- **IndicatorCombiner**: Calculate multiple indicators simultaneously
- **StrategyCombiner**: Combine multiple strategies with voting methods:
  - `majority_vote`: Buy when majority says buy, sell when majority says sell
  - `weighted_average`: Weighted signal sum with threshold-based decision
  - `consensus`: Only signal when all strategies agree

### Logging System

Uses `CustomLogger` from `utils/custom_logger.py`:

```python
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="module_name",
    log_level=logging.INFO,
    log_dir="logs",  # None for console only
    format_style="verbose"  # or "simple"
)
```

Features:
- Color-coded console output (via colorama)
- Optional file logging with level separation
- Automatic log directory creation

### Data Flow

1. **Data Collection**: Crawlers fetch data from external APIs
2. **Storage**: Data stored in PostgreSQL/MongoDB with Redis caching
3. **Processing**: Data cleaned and features engineered
4. **Calculation**: Indicators computed → Strategies generate signals
5. **Backtesting**: Historical validation of strategies
6. **API**: FastAPI exposes results to frontend

## Key Design Patterns

### Dependency Injection

Strategies accept indicators via constructor:

```python
strategy = BaseStrategy(
    name="my_strategy",
    params={"window": 20},
    indicators=[ma_indicator, rsi_indicator]
)
```

### Async/Await

All I/O operations use async/await:
- Database operations
- HTTP requests
- WebSocket connections

Always use `async def` for data layer methods.

### DataFrame Convention

OHLCV data columns must be: `["open", "high", "low", "close", "volume"]`

Index should be DatetimeIndex for time series operations.

### Parameter Validation Pattern

All base classes support parameter validation through `validate_params()`:

```python
def validate_params(self) -> None:
    """Validate strategy parameters, raise ValueError if invalid"""
    if not isinstance(self.params["window"], int) or self.params["window"] < 2:
        raise ValueError(f"窗口大小必须是大于1的整数，当前值: {self.params['window']}")
```

This is called automatically in `__init__()` and should be overridden in subclasses to enforce parameter constraints.

## Configuration

- `config/base.py`: Base configuration including database credentials
- `pyproject.toml`: Python dependencies (managed with uv)
- `frontend/package.json`: Frontend dependencies (managed with pnpm)

## Module-Specific Notes

### calculation Module

- Indicators use **ta-lib** library for efficient computation
- Strategies work with pandas DataFrames
- Backtest supports transaction costs and slippage simulation
- Performance metrics: Sharpe ratio, max drawdown, win rate, profit factor

### data Module

- **Crawlers**: Async HTTP clients with exponential backoff retry
- **Storage**: Multi-backend support for different use cases
  - PostgreSQL: Relational data with structured queries
  - MongoDB: Flexible document storage
  - Redis: High-performance caching layer
  - Parquet: Long-term archival with compression

### service Module

- FastAPI application in `service/main.py`
- API routes organized by version in `service/api/v1/`
- Router aggregation in `service/api/api_router.py`

### frontend Module

- React 19 with modern hooks
- Vite for fast development and optimized builds
- Tailwind CSS v4 for styling
- Component-based architecture in `src/components/`

## Testing

Tests located in `tests/` directory:
- `test_simple_logging.py`: Logger functionality tests
- `test_sina_stock.py`: Sina crawler integration tests

Run with `uv run pytest` or `pytest tests/`

## Common Patterns

### Creating a New Indicator

```python
from calculation.indicators.base_indicator import BaseIndicator

class MyIndicator(BaseIndicator):
    def __init__(self, window: int = 20):
        super().__init__(
            name="my_indicator",
            params={"window": window}
        )

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        # Implementation here
        result = data.copy()
        result["my_indicator"] = ...  # Calculate indicator
        self.results = result
        return result
```

### Creating a New Strategy

```python
from calculation.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, param1: int = 10):
        super().__init__(
            name="my_strategy",
            params={"param1": param1},
            indicators=[]  # List required indicators
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0  # Default: no signal

        # Generate buy/sell signals
        signals.loc[condition, "signal"] = 1   # Buy
        signals.loc[condition, "signal"] = -1  # Sell

        return signals
```

## Important Constraints

- **Python Version**: >=3.10 (uses modern type hints)
- **Database**: Default config uses PostgreSQL on localhost:5432
- **Data Validation**: Always check required columns before computation
- **Error Handling**: Use CustomLogger for consistent error logging
- **Async**: All data layer operations must be async

## Signal Convention

Trading signals follow this convention across the codebase:
- **1**: Buy signal
- **0**: Hold/No signal
- **-1**: Sell signal

This convention is used consistently in:
- Strategy signal generation (`generate_signals()`)
- Backtest signal processing
- Performance evaluation calculations

## File Organization

```
├── calculation/     # Core computation logic
│   ├── indicators/  # Technical indicator calculations
│   ├── strategies/  # Trading strategies
│   └── backtest/    # Backtesting engine
├── data/           # Data acquisition and storage
│   ├── crawler/    # Data source integrations
│   └── storage/    # Storage backend implementations
├── service/        # API and business logic
│   ├── api/        # FastAPI endpoints
│   └── tasks/      # Async task scheduling
├── utils/          # Shared utilities
│   └── custom_logger.py  # Logging system
└── frontend/       # React application
    └── src/
        ├── components/  # Reusable components
        └── pages/       # Page-level components
```

## Environment Setup

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Install Python dependencies: `uv sync`
3. Install frontend dependencies: `cd frontend && pnpm install`
4. Configure database in `config/base.py`
5. Run backend: `uv run main.py`
6. Run frontend (separate terminal): `cd frontend && pnpm dev`

## Adding New Features

1. **New Data Source**: Create crawler class inheriting `BaseCrawler`
2. **New Indicator**: Inherit from `BaseIndicator`, implement `calculate()`
3. **New Strategy**: Inherit from `BaseStrategy`, implement `generate_signals()`
4. **New API Endpoint**: Add to `service/api/v1/`, register in router
5. **New Frontend Page**: Add to `frontend/src/pages/`, update routing

## Testing Strategy

- Unit tests for individual indicators and strategies
- Integration tests for crawlers and storage
- End-to-end tests for complete workflows
- Always test with sample data before production use

## API Structure

The FastAPI application is organized as follows:
- **Main app**: `service/main.py` - Application entry point with CORS and lifespan management
- **Router aggregation**: `service/api/api_router.py` - All v1 routes registered under `/api/v1`
- **API modules**:
  - `stock_api.py` - Stock data endpoints
  - `strategy_api.py` - Strategy recommendation endpoints
  - `backtest_api.py` - Backtesting endpoints
  - `data_api.py` - Data management endpoints (with storage initialization)
  - `user_api.py` - User management endpoints

API docs available at `/docs` when server is running.
