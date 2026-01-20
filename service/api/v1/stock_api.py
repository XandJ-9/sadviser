"""
股票相关API接口 - 使用Pydantic schemas和CRUD模式

遵循FastAPI最佳实践：
- 使用Pydantic schemas进行请求/响应验证
- 使用依赖注入管理数据库连接
- 直接使用CRUD操作而非复杂的service/repository层次
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from service.database import get_storage
from service.crud.stock_crud import StockCRUD
from service.schemas.stock import (
    StockListResponse,
    StockDetailResponse,
    StockHistoryResponse,
    StockQuote,
    MarketOverviewResponse,
    HotStockResponse,
    StockSearchResponse
)
from data.storage.postgres_storage import PostgreSQLStorage
from utils.custom_logger import CustomLogger
import logging

router = APIRouter(prefix='/stocks', tags=['stocks'])

logger = CustomLogger(
    name="stock_api",
    log_level=logging.INFO
)


# ==================== 固定路径（优先匹配） ====================

@router.get("/", response_model=StockListResponse)
async def get_stocks(
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取股票列表（从数据库）

    Args:
        limit: 返回数量限制 (1-500)
        offset: 偏移量
        storage: 注入的数据库实例

    Returns:
        股票列表和总数
    """
    try:
        crud = StockCRUD(storage)
        stocks = await crud.get_stock_list(limit=limit, offset=offset)
        total = await crud.get_stock_list_count()

        # 添加最新价格信息
        stocks_with_price = []
        for stock in stocks:
            symbol = stock.get("symbol")
            latest_data = await crud.get_stock_latest_data(symbol)

            stock_info = {
                "symbol": symbol,
                "name": stock.get("name", ""),
                "source": stock.get("source", ""),
                "price": float(latest_data.get("close", 0)) if latest_data else 0,
                "volume": float(latest_data.get("volume", 0)) if latest_data else 0,
                "open": float(latest_data.get("open", 0)) if latest_data else 0,
                "high": float(latest_data.get("high", 0)) if latest_data else 0,
                "low": float(latest_data.get("low", 0)) if latest_data else 0,
            }
            stocks_with_price.append(stock_info)

        return StockListResponse(stocks=stocks_with_price, total=total)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote")
async def get_stock_quote(
    symbols: str = Query(..., description="股票代码,逗号分隔"),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取实时行情（从数据库最新数据）

    Args:
        symbols: 股票代码,逗号分隔
        storage: 注入的数据库实例

    Returns:
        实时行情数据字典
    """
    try:
        crud = StockCRUD(storage)
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

        quotes = []
        for symbol in symbol_list:
            latest_data = await crud.get_stock_latest_data(symbol)
            stock_info = await crud.get_stock_by_symbol(symbol)

            if latest_data and stock_info:
                close = float(latest_data.get("close", 0))
                open_price = float(latest_data.get("open", 0))

                # Calculate change percent
                change_percent = 0.0
                if open_price > 0:
                    change_percent = ((close - open_price) / open_price) * 100

                quote = {
                    "symbol": symbol,
                    "name": stock_info.get("name", ""),
                    "price": close,
                    "change": close - open_price,
                    "change_percent": change_percent,
                    "volume": float(latest_data.get("volume", 0)),
                    "open": open_price,
                    "high": float(latest_data.get("high", 0)),
                    "low": float(latest_data.get("low", 0))
                }
                quotes.append(quote)

        return {"quotes": quotes, "count": len(quotes)}
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot", response_model=List[HotStockResponse])
async def get_hot_stocks(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取热门股票（基于成交量）

    Args:
        limit: 返回数量 (1-100)
        storage: 注入的数据库实例

    Returns:
        热门股票列表
    """
    try:
        crud = StockCRUD(storage)
        hot_stocks = await crud.get_hot_stocks(limit=limit)
        return hot_stocks
    except Exception as e:
        logger.error(f"获取热门股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}", response_model=StockSearchResponse)
async def search_stocks(
    keyword: str,
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    搜索股票（按代码或名称）

    Args:
        keyword: 搜索关键词
        limit: 返回数量限制 (1-100)
        storage: 注入的数据库实例

    Returns:
        搜索结果
    """
    try:
        crud = StockCRUD(storage)
        stocks = await crud.search_stocks(keyword=keyword, limit=limit)

        # Convert to StockInfo format
        stock_list = []
        for stock in stocks:
            stock_info = {
                "symbol": stock.get("symbol"),
                "name": stock.get("name", ""),
                "source": stock.get("source", ""),
                "price": 0,  # Search results don't include price
                "volume": 0,
                "open": 0,
                "high": 0,
                "low": 0
            }
            stock_list.append(stock_info)

        return StockSearchResponse(stocks=stock_list, total=len(stock_list))
    except Exception as e:
        logger.error(f"搜索股票失败: {keyword}, error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/overview", response_model=MarketOverviewResponse)
async def get_market_overview(
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取A股市场概览

    Args:
        storage: 注入的数据库实例

    Returns:
        市场统计数据：成交量、涨停跌停数等
    """
    try:
        crud = StockCRUD(storage)
        stats = await crud.get_market_stats()
        return MarketOverviewResponse(**stats)
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 参数路径（后匹配） ====================

@router.get("/{symbol}/history", response_model=StockHistoryResponse)
async def get_stock_history(
    symbol: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="返回数据条数"),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取股票历史数据（从数据库）

    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 返回数据条数 (1-1000)
        storage: 注入的数据库实例

    Returns:
        历史数据
    """
    try:
        crud = StockCRUD(storage)
        daily_data = await crud.get_stock_daily_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        # Convert to StockDailyData format
        data_list = []
        for item in daily_data:
            date_obj = item.get("date")
            # Convert date to string in YYYY-MM-DD format
            if date_obj:
                date_str = str(date_obj)
            else:
                logger.warning(f"Missing date for item in daily_data for {symbol}")
                continue

            data_item = {
                "symbol": symbol,
                "date": date_str,
                "open": float(item.get("open", 0) or 0),
                "high": float(item.get("high", 0) or 0),
                "low": float(item.get("low", 0) or 0),
                "close": float(item.get("close", 0) or 0),
                "volume": float(item.get("volume", 0) or 0)
            }
            data_list.append(data_item)

        return StockHistoryResponse(
            symbol=symbol,
            data=data_list,
            total=len(data_list)
        )
    except Exception as e:
        logger.error(f"获取历史数据失败: {symbol}, error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}", response_model=StockDetailResponse)
async def get_stock_detail(
    symbol: str,
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取股票详情（从数据库）

    注意：此路由必须放在最后，因为它会匹配所有路径

    Args:
        symbol: 股票代码
        storage: 注入的数据库实例

    Returns:
        股票详细信息
    """
    try:
        crud = StockCRUD(storage)
        stock_info = await crud.get_stock_by_symbol(symbol)

        if not stock_info:
            raise HTTPException(status_code=404, detail="股票不存在")

        # Get latest price data
        latest_data = await crud.get_stock_latest_data(symbol)

        detail = {
            "symbol": stock_info.get("symbol"),
            "name": stock_info.get("name", ""),
            "source": stock_info.get("source", ""),
            "price": float(latest_data.get("close", 0)) if latest_data else 0,
            "volume": float(latest_data.get("volume", 0)) if latest_data else 0,
            "open": float(latest_data.get("open", 0)) if latest_data else 0,
            "high": float(latest_data.get("high", 0)) if latest_data else 0,
            "low": float(latest_data.get("low", 0)) if latest_data else 0,
            "market_cap": None,
            "pe_ratio": None,
            "daily_data": []
        }

        return StockDetailResponse(**detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {symbol}, error={e}")
        raise HTTPException(status_code=500, detail=str(e))
