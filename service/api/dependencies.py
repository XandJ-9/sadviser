"""
FastAPI 依赖注入 - 使用 FastAPI 的 Depends 系统
"""
from fastapi import Depends
from service.core.container import container
from service.services.stock_service import StockService
from service.services.task_service import TaskService


def get_stock_service() -> StockService:
    """
    获取 StockService 实例的依赖函数

    FastAPI 会自动调用这个函数，并将返回值注入到路由函数中

    Returns:
        StockService 实例（单例）
    """
    return container.get_stock_service()


def get_task_service() -> TaskService:
    """
    获取 TaskService 实例的依赖函数

    FastAPI 会自动调用这个函数，并将返回值注入到路由函数中

    Returns:
        TaskService 实例（单例）
    """
    return container.get_task_service()


# 导出依赖函数，供 API 路由使用
__all__ = ["get_stock_service", "get_task_service"]
