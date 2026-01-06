"""
任务数据 Repository - 封装所有任务相关的数据库查询
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .base_repository import BaseRepository

import json

class TaskRepository(BaseRepository):
    """
    任务数据仓库，处理所有与任务相关的数据库操作
    """

    async def create_task(
        self,
        task_id: str,
        task_type: str,
        meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建新任务

        Args:
            task_id: 任务ID
            task_type: 任务类型
            meta: 任务元数据

        Returns:
            创建的任务记录
        """
        task_data = {
            "id": task_id,
            "type": task_type,
            "status": "pending",
            "message": "任务已创建",
            "progress": 0,
            "total": meta.get("total", 0),
            "success": 0,
            "failed": 0,
            "meta": json.dumps(meta)
        }

        await self.storage.insert("tasks", task_data)
        return task_data

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息，如果不存在返回 None
        """
        return await self.find_one(
            table_name="tasks",
            conditions={"id": task_id}
        )

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
        conditions = {}
        if status:
            conditions["status"] = status

        return await self.find_many(
            table_name="tasks",
            conditions=conditions,
            sort=[("created_at", -1)],
            limit=limit,
            offset=offset
        )

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
        try:
            await self.storage.update(
                table_name="tasks",
                conditions={"id": task_id},
                data=data
            )
            return True
        except Exception as e:
            self.logger.error(f"更新任务失败: {task_id}, error={e}")
            return False

    async def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            统计信息
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            # 获取最近100条任务进行统计
            query = """
                SELECT status, COUNT(*) as count
                FROM (
                    SELECT status
                    FROM tasks
                    ORDER BY created_at DESC
                    LIMIT 100
                ) subquery
                GROUP BY status
            """
            results = await conn.fetch(query)
            await self.storage.pool.release(conn)

            stats = {row["status"]: row["count"] for row in results}

            return stats
        except Exception as e:
            self.logger.error(f"获取任务统计失败: {e}")
            return {}

    async def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的任务

        Args:
            limit: 返回数量

        Returns:
            任务列表
        """
        return await self.find_many(
            table_name="tasks",
            sort=[("created_at", -1)],
            limit=limit
        )
