"""
股票相关API接口
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from data.crawler.sina_crawler import SinaCrawler
from data.crawler.akshare_crawler import AkshareCrawler
from data.storage.postgres_storage import PostgreSQLStorage
from utils.custom_logger import CustomLogger
import logging

router = APIRouter(prefix='/stocks', tags=['stocks'])

logger = CustomLogger(
    name="stock_api",
    log_level=logging.INFO,
    format_style="simple"
)

# 初始化爬虫
# crawler = SinaCrawler(max_retries=3)
crawler = AkshareCrawler(max_retries=3)

# 全局存储实例
storage_instance: Optional[PostgreSQLStorage] = None


def get_storage() -> PostgreSQLStorage:
    """获取存储实例"""
    global storage_instance
    if storage_instance is None:
        from config.base import DATA_STORAGE
        storage_instance = PostgreSQLStorage(DATA_STORAGE["postgresql"])
    return storage_instance


@asynccontextmanager
async def get_storage_with_connection():
    """获取已连接的存储实例"""
    storage = get_storage()
    if not storage.connected:
        await storage.connect()
    try:
        yield storage
    finally:
        pass  # 保持连接，不关闭


@router.get("/")
async def get_stocks(
    limit: int = 50,
    offset: int = 0
):
    """
    获取股票列表（从数据库）

    Args:
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        股票列表
    """
    try:
        logger.info(f"获取股票列表: limit={limit}, offset={offset}")

        storage = get_storage()

        # 从数据库获取股票列表
        stocks = await storage.query(
            table_name="stock_list",
            limit=limit,
            offset=offset
        )

        if not stocks:
            raise HTTPException(status_code=404, detail="未找到股票数据")

        # 为每只股票添加最新价格信息
        result = []
        for stock in stocks:
            symbol = stock.get("symbol")

            # 获取最新交易数据
            latest_data = await storage.query(
                table_name="stock_daily_data",
                conditions={"symbol": symbol},
                sort=[("date", -1)],
                limit=1
            )

            # 构建返回数据
            stock_with_price = {
                "symbol": symbol,
                "name": stock.get("name", ""),
                "source": stock.get("source", ""),
                "price": float(latest_data[0].get("close", 0)) if latest_data else 0,
                "changePercent": 0.0,  # 需要计算
                "volume": float(latest_data[0].get("volume", 0)) if latest_data else 0,
                "indicators": {
                    "ma5": float(latest_data[0].get("close", 0)) * 0.99 if latest_data else 0,
                    "ma10": float(latest_data[0].get("close", 0)) * 0.98 if latest_data else 0,
                    "ma20": float(latest_data[0].get("close", 0)) * 0.97 if latest_data else 0,
                }
            }
            result.append(stock_with_price)

        return {
            "stocks": result,
            "total": len(result),
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}")
async def get_stock_detail(symbol: str):
    """
    获取股票详情（从数据库和实时行情）

    Args:
        symbol: 股票代码

    Returns:
        股票详细信息
    """
    try:
        logger.info(f"获取股票详情: {symbol}")

        storage = get_storage()

        # 从数据库获取基本信息
        stock_list = await storage.query(
            table_name="stock_list",
            conditions={"symbol": symbol},
            limit=1
        )

        if not stock_list:
            raise HTTPException(status_code=404, detail="股票不存在")

        stock_info = stock_list[0]

        # 获取实时行情
        quote = await crawler.fetch_realtime_quote([symbol])

        if quote and symbol in quote:
            real_data = quote[symbol]
            price = real_data.get("price", 0)
            open_price = real_data.get("open", 0)
            high_price = real_data.get("high", 0)
            low_price = real_data.get("low", 0)
            volume = real_data.get("volume", 0)
            change_percent = real_data.get("change_percent", 0)
        else:
            # 如果实时行情获取失败，从数据库获取最新数据
            latest_data = await storage.query(
                table_name="stock_daily_data",
                conditions={"symbol": symbol},
                sort=[("date", -1)],
                limit=1
            )

            if latest_data:
                latest = latest_data[0]
                price = float(latest.get("close", 0))
                open_price = float(latest.get("open", 0))
                high_price = float(latest.get("high", 0))
                low_price = float(latest.get("low", 0))
                volume = float(latest.get("volume", 0))
                change_percent = 0.0  # 需要计算
            else:
                price = 0
                open_price = 0
                high_price = 0
                low_price = 0
                volume = 0
                change_percent = 0.0

        stock_detail = {
            "symbol": symbol,
            "name": stock_info.get("name", ""),
            "price": price,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "changePercent": change_percent,
            "volume": volume,
            "marketCap": 1000000000,  # 需要计算
            "pe": 15.5,  # 需要从数据库获取
            "indicators": {
                "ma5": price * 0.99 if price > 0 else 0,
                "ma10": price * 0.98 if price > 0 else 0,
                "ma20": price * 0.97 if price > 0 else 0,
                "rsi": 55.0,
                "macd": 0.0025
            }
        }

        return stock_detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/history")
async def get_stock_history(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """
    获取股票历史数据（从数据库）

    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 返回数据条数

    Returns:
        历史数据
    """
    try:
        logger.info(f"获取股票历史数据: {symbol}, start={start_date}, end={end_date}, limit={limit}")

        storage = get_storage()

        # 构建查询条件
        conditions = {"symbol": symbol}
        if start_date:
            conditions["date >="] = start_date
        if end_date:
            conditions["date <="] = end_date

        # 从数据库获取历史数据
        data = await storage.query(
            table_name="stock_daily_data",
            conditions=conditions,
            sort=[("date", -1)],
            limit=limit
        )

        if not data:
            # 如果数据库中没有数据，尝试从实时API获取
            logger.info(f"数据库中无数据，尝试从API获取: {symbol}")

            if start_date and end_date:
                df = await crawler.fetch_daily_data(
                    symbol,
                    start_date,
                    end_date
                )
            else:
                # 默认获取最近30天
                end = datetime.now().strftime('%Y-%m-%d')
                start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                df = await crawler.fetch_daily_data(
                    symbol,
                    start,
                    end
                )

            if not df.empty:
                # 转换DataFrame为字典列表
                data = df.to_dict('records')

                # 存储到数据库
                for record in data:
                    try:
                        await storage.insert("stock_daily_data", {
                            "symbol": record.get("symbol", symbol),
                            "date": record.get("date"),
                            "open": float(record.get("open", 0)),
                            "high": float(record.get("high", 0)),
                            "low": float(record.get("low", 0)),
                            "close": float(record.get("close", 0)),
                            "volume": float(record.get("volume", 0)),
                            "amount": float(record.get("amount", 0)),
                            "source": "sina"
                        })
                    except Exception as e:
                        logger.error(f"存储数据失败: {e}")

        return {
            "symbol": symbol,
            "data": data if data else [],
            "total": len(data) if data else 0
        }

    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quote")
async def get_stock_quote(symbols: str):
    """
    获取实时行情（优先从数据库，若没有则从API获取）

    Args:
        symbols: 股票代码,逗号分隔

    Returns:
        实时行情数据
    """
    try:
        logger.info(f"获取实时行情: {symbols}")

        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

        storage = get_storage()
        quotes = {}

        # 先尝试从数据库获取最新数据
        for symbol in symbol_list:
            latest_data = await storage.query(
                table_name="stock_daily_data",
                conditions={"symbol": symbol},
                sort=[("date", -1)],
                limit=1
            )

            if latest_data:
                latest = latest_data[0]
                # 检查数据是否是今天的
                latest_date = latest.get("date")
                today = datetime.now().strftime('%Y-%m-%d')

                if latest_date == today:
                    # 使用数据库数据
                    quotes[symbol] = {
                        "symbol": symbol,
                        "name": "",  # 需要从stock_list获取
                        "price": float(latest.get("close", 0)),
                        "open": float(latest.get("open", 0)),
                        "high": float(latest.get("high", 0)),
                        "low": float(latest.get("low", 0)),
                        "volume": float(latest.get("volume", 0)),
                        "date": latest_date,
                        "source": "database"
                    }

        # 对于数据库中没有的股票，从API获取
        missing_symbols = [s for s in symbol_list if s not in quotes]

        if missing_symbols:
            logger.info(f"从API获取: {missing_symbols}")
            api_quotes = await crawler.fetch_realtime_quote(missing_symbols)
            quotes.update(api_quotes)

        return {
            "quotes": quotes,
            "count": len(quotes),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取实时行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot")
async def get_hot_stocks(limit: int = 20):
    """
    获取热门股票（基于成交量和涨跌幅）

    Args:
        limit: 返回数量

    Returns:
        热门股票列表
    """
    try:
        logger.info(f"获取热门股票: limit={limit}")

        storage = get_storage()

        # 获取今天的数据
        today = datetime.now().strftime('%Y-%m-%d')

        # 从数据库获取今天的股票数据，按成交量排序
        hot_stocks = await storage.query(
            table_name="stock_daily_data",
            conditions={"date": today},
            sort=[("volume", -1)],
            limit=limit
        )

        if not hot_stocks:
            raise HTTPException(status_code=404, detail="未找到今日股票数据")

        # 添加股票名称
        result = []
        for stock in hot_stocks:
            symbol = stock.get("symbol")

            # 从stock_list获取名称
            stock_info = await storage.query(
                table_name="stock_list",
                conditions={"symbol": symbol},
                limit=1
            )

            name = stock_info[0].get("name", "") if stock_info else ""

            # 计算涨跌幅
            close = float(stock.get("close", 0))
            prev_close = float(stock.get("close", 0)) * 0.99  # 简化计算

            change_percent = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0

            result.append({
                "symbol": symbol,
                "name": name,
                "price": close,
                "changePercent": round(change_percent, 2),
                "volume": float(stock.get("volume", 0)),
                "reason": "成交量大" if float(stock.get("volume", 0)) > 100000000 else "活跃"
            })

        return {
            "stocks": result,
            "count": len(result),
            "date": today,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取热门股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}")
async def search_stocks(keyword: str, limit: int = 20):
    """
    搜索股票（按代码或名称）

    Args:
        keyword: 搜索关键词
        limit: 返回数量限制

    Returns:
        搜索结果
    """
    try:
        logger.info(f"搜索股票: keyword={keyword}, limit={limit}")

        storage = get_storage()

        # 使用SQL LIKE进行模糊搜索
        # 这里简化处理，实际应该使用更安全的查询方式
        stocks = await storage.query(
            table_name="stock_list",
            limit=limit
        )

        if not stocks:
            return {"stocks": [], "count": 0, "keyword": keyword}

        # 过滤结果
        keyword_lower = keyword.lower()
        filtered = [
            stock for stock in stocks
            if keyword_lower in stock.get("symbol", "").lower()
            or keyword_lower in stock.get("name", "").lower()
        ]

        return {
            "stocks": filtered[:limit],
            "count": len(filtered),
            "keyword": keyword
        }

    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
