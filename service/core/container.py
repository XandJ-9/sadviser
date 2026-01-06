"""
依赖注入容器 - 统一管理服务实例
"""
from typing import Optional
from data.storage.postgres_storage import PostgreSQLStorage
from ..repositories.stock_repository import StockRepository
from ..repositories.task_repository import TaskRepository
from ..services.stock_service import StockService
from ..services.task_service import TaskService
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="Container",
    log_level=logging.INFO,
)


class Container:
    """
    依赖注入容器，管理所有服务实例
    使用单例模式确保每个服务只有一个实例
    """

    _instance: Optional['Container'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._storage: Optional[PostgreSQLStorage] = None
        self._stock_repository: Optional[StockRepository] = None
        self._stock_service: Optional[StockService] = None
        self._task_repository: Optional[TaskRepository] = None
        self._task_service: Optional[TaskService] = None

    def get_storage(self) -> PostgreSQLStorage:
        """
        获取数据库存储实例

        Returns:
            PostgreSQL 存储实例
        """
        if self._storage is None:
            from config.base import DATA_STORAGE
            self._storage = PostgreSQLStorage(DATA_STORAGE["postgresql"])
            logger.info("创建 PostgreSQL 存储实例")
        return self._storage

    def get_stock_repository(self) -> StockRepository:
        """
        获取股票仓库实例

        Returns:
            StockRepository 实例
        """
        if self._stock_repository is None:
            self._stock_repository = StockRepository(self.get_storage())
            logger.info("创建 StockRepository 实例")
        return self._stock_repository

    def get_stock_service(self) -> StockService:
        """
        获取股票服务实例

        Returns:
            StockService 实例
        """
        if self._stock_service is None:
            self._stock_service = StockService(self.get_stock_repository())
            logger.info("创建 StockService 实例")
        return self._stock_service

    def get_task_repository(self) -> TaskRepository:
        """
        获取任务仓库实例

        Returns:
            TaskRepository 实例
        """
        if self._task_repository is None:
            self._task_repository = TaskRepository(self.get_storage())
            logger.info("创建 TaskRepository 实例")
        return self._task_repository

    def get_task_service(self) -> TaskService:
        """
        获取任务服务实例

        Returns:
            TaskService 实例
        """
        if self._task_service is None:
            self._task_service = TaskService(self.get_task_repository())
            logger.info("创建 TaskService 实例")
        return self._task_service

    async def close(self):
        """
        关闭所有连接和资源
        """
        if self._storage and self._storage.connected:
            await self._storage.close()
            logger.info("关闭数据库连接")


# 全局容器实例
container = Container()
