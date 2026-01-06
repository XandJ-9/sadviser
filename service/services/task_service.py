"""
任务服务层 - 封装任务相关的业务逻辑
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="TaskService",
    log_level=logging.INFO,
)


class TaskService:
    """
    任务服务类，处理任务相关的业务逻辑
    """

    def __init__(self, task_repository):
        """
        初始化任务服务

        Args:
            task_repository: 任务仓库实例
        """
        self.repository = task_repository
        logger.info("任务服务已初始化")

    async def create_task(
        self,
        task_type: str,
        meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建新任务

        Args:
            task_type: 任务类型 (fetch_history, fetch_realtime, fetch_stocklist)
            meta: 任务元数据

        Returns:
            创建的任务信息
        """
        import time
        task_id = f"task_{int(time.time() * 1000)}"

        logger.info(f"创建任务: {task_id}, 类型: {task_type}")

        task_data = await self.repository.create_task(task_id, task_type, meta)

        return task_data

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息，如果不存在返回 None
        """
        logger.debug(f"查询任务: {task_id}")
        return await self.repository.get_task(task_id)

    async def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取任务列表

        Args:
            status: 任务状态过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            任务列表
        """
        logger.debug(f"查询任务列表: status={status}, limit={limit}")
        return await self.repository.get_tasks(status, limit, offset)

    async def update_task(
        self,
        task_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        更新任务信息

        Args:
            task_id: 任务ID
            data: 更新的数据

        Returns:
            是否更新成功
        """
        logger.debug(f"更新任务: {task_id}")
        return await self.repository.update_task(task_id, data)

    async def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            统计信息
        """
        logger.debug("查询任务统计")
        return await self.repository.get_task_stats()

    async def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的任务

        Args:
            limit: 返回数量

        Returns:
            任务列表
        """
        logger.debug(f"查询最近任务: limit={limit}")
        return await self.repository.get_recent_tasks(limit)

    async def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态

        Returns:
            系统状态信息
        """
        logger.debug("查询系统状态")

        try:
            # 获取任务统计
            stats = await self.get_task_stats()
            recent_tasks = await self.get_recent_tasks(limit=100)

            # 统计各状态任务数量
            running_count = stats.get("running", 0)
            completed_count = stats.get("completed", 0)
            pending_count = stats.get("pending", 0)
            failed_count = stats.get("failed", 0)

            return {
                "storage_connected": True,  # 如果能查询到数据说明连接正常
                "active_tasks": running_count,
                "completed_tasks": completed_count,
                "pending_tasks": pending_count,
                "failed_tasks": failed_count,
                "total_tasks": len(recent_tasks),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                "storage_connected": False,
                "active_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "failed_tasks": 0,
                "total_tasks": 0,
                "timestamp": datetime.now().isoformat()
            }
