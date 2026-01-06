"""
股票相关API接口 - 重构版
使用 FastAPI 依赖注入系统

路由顺序说明：
- 固定路径必须放在参数路径之前
- 更具体的路径放在更通用的路径之前
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from service.api.dependencies import get_stock_service
from service.services.stock_service import StockService
from utils.custom_logger import CustomLogger
import logging

router = APIRouter(prefix='/stocks', tags=['stocks'])

logger = CustomLogger(
    name="stock_api",
    log_level=logging.INFO
)


# ==================== 固定路径（优先匹配） ====================

@router.get("/")
async def get_stocks(
    limit: int = 50,
    offset: int = 0,
    service: StockService = Depends(get_stock_service)
):
    """
    获取股票列表（从数据库）

    Args:
        limit: 返回数量限制
        offset: 偏移量
        service: 注入的 StockService 实例（由 FastAPI 自动提供）

    Returns:
        股票列表
    """
    try:
        return await service.get_stock_list(limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote")
async def get_stock_quote(
    symbols: str,
    service: StockService = Depends(get_stock_service)
):
    """
    获取实时行情（从数据库最新数据）

    Args:
        symbols: 股票代码,逗号分隔
        service: 注入的 StockService 实例（由 FastAPI 自动提供）

    Returns:
        实时行情数据
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
        return await service.get_stock_quote(symbol_list)
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot")
async def get_hot_stocks(
    limit: int = 20,
    service: StockService = Depends(get_stock_service)
):
    """
    获取热门股票（基于成交量）

    Args:
        limit: 返回数量
        service: 注入的 StockService 实例（由 FastAPI 自动提供）

    Returns:
        热门股票列表
    """
    try:
        return await service.get_hot_stocks(limit=limit)
    except Exception as e:
        logger.error(f"获取热门股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}")
async def search_stocks(
    keyword: str,
    limit: int = 20,
    service: StockService = Depends(get_stock_service)
):
    """
    搜索股票（按代码或名称）

    Args:
        keyword: 搜索关键词
        limit: 返回数量限制
        service: 注入的 StockService 实例（由 FastAPI 自动提供）

    Returns:
        搜索结果
    """
    try:
        return await service.search_stocks(keyword=keyword, limit=limit)
    except Exception as e:
        logger.error(f"搜索股票失败: {keyword}, error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/overview")
async def get_market_overview(
    service: StockService = Depends(get_stock_service)
):
    """
    获取A股市场概览

    Args:
        service: 注入的 StockService 实例（由 FastAPI 自动提供）

    Returns:
        市场统计数据：成交量、涨停跌停数等
    """
    try:
        return await service.get_market_overview()
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 参数路径（后匹配） ====================

@router.get("/{symbol}/history")
async def get_stock_history(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    service: StockService = Depends(get_stock_service)
):
    """
    获取股票历史数据（从数据库）

    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 返回数据条数
        service: 注入的 StockService 实例（由 FastAPI 自动提供）

    Returns:
        历史数据
    """
    try:
        return await service.get_stock_history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    except Exception as e:
        logger.error(f"获取历史数据失败: {symbol}, error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}")
async def get_stock_detail(
    symbol: str,
    service: StockService = Depends(get_stock_service)
):
    """
    获取股票详情（从数据库）

    注意：此路由必须放在最后，因为它会匹配所有路径

    Args:
        symbol: 股票代码
        service: 注入的 StockService 实例（由 FastAPI 自动提供）

    Returns:
        股票详细信息
    """
    try:
        detail = await service.get_stock_detail(symbol)

        if not detail:
            raise HTTPException(status_code=404, detail="股票不存在")

        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {symbol}, error={e}")
        raise HTTPException(status_code=500, detail=str(e))
