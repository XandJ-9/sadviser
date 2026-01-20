"""
Database dependencies for FastAPI

Provides database session management using FastAPI's dependency injection system.
This replaces the repository pattern with a more direct CRUD approach.
"""
from fastapi import Depends
from typing import AsyncGenerator
from data.storage.postgres_storage import PostgreSQLStorage
from config.base import DATA_STORAGE
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="database",
    log_level=logging.INFO
)


# Global storage instance (singleton)
_storage_instance: PostgreSQLStorage = None


async def get_storage() -> AsyncGenerator[PostgreSQLStorage, None]:
    """
    Get database storage instance (dependency injection)

    This function provides a database connection to API endpoints.
    It ensures the storage is connected and yields the instance.

    Yields:
        PostgreSQLStorage: Database storage instance

    Example:
        @router.get("/stocks")
        async def get_stocks(storage: PostgreSQLStorage = Depends(get_storage)):
            result = await storage.query("stock_list")
            return result
    """
    global _storage_instance

    try:
        # Initialize storage if needed
        if _storage_instance is None:
            _storage_instance = PostgreSQLStorage(DATA_STORAGE["postgresql"])
            logger.info("Initialized PostgreSQL storage")

        # Ensure connection is established
        if not _storage_instance.connected:
            await _storage_instance.connect()
            logger.debug("Database connection established")

        yield _storage_instance

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


async def get_db_connection():
    """
    Get raw database connection (for complex queries)

    This provides direct access to the underlying database connection
    for operations that require raw SQL or advanced features.

    Yields:
        Database connection object

    Example:
        @router.get("/custom-query")
        async def custom_query(conn = Depends(get_db_connection)):
            result = await conn.fetch("SELECT * FROM stock_list WHERE symbol = $1", symbol)
            return result
    """
    storage = await get_storage().__anext__()

    try:
        conn = await storage._get_connection()
        yield conn
    finally:
        await storage.pool.release(conn)


async def close_database():
    """
    Close database connection (called on application shutdown)

    This should be registered in the FastAPI lifespan context manager.
    Uses timeout and force-close to prevent hanging.
    """
    global _storage_instance

    if _storage_instance and _storage_instance.pool:
        try:
            # 先关闭连接标志，阻止新连接
            _storage_instance.connected = False

            # 尝试优雅关闭，设置5秒超时
            import asyncio
            try:
                await asyncio.wait_for(_storage_instance.pool.close(), timeout=5.0)
                logger.info("Database connection closed gracefully")
            except asyncio.TimeoutError:
                # 超时则强制终止所有连接
                logger.warning("Database close timeout, terminating pool")
                _storage_instance.pool.terminate()
                logger.info("Database pool terminated")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")
        finally:
            _storage_instance = None


__all__ = [
    "get_storage",
    "get_db_connection",
    "close_database"
]
