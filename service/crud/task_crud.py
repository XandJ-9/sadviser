"""
Task CRUD operations

Provides database operations for task management.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from data.storage.postgres_storage import PostgreSQLStorage
from utils.custom_logger import CustomLogger
import logging,json
import uuid

logger = CustomLogger(
    name="task_crud",
    log_level=logging.INFO
)


class TaskCRUD:
    """
    Task CRUD operations

    This class provides methods for performing database operations
    on task-related tables.
    """

    def __init__(self, storage: PostgreSQLStorage):
        """
        Initialize TaskCRUD with storage instance

        Args:
            storage: Database storage instance
        """
        self.storage = storage
        self.logger = logger

    async def create_task(
        self,
        task_type: str,
        meta: Dict[str, Any],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create a new task

        Args:
            task_type: Type of task
            meta: Task metadata
            priority: Task priority

        Returns:
            Created task data
        """
        try:
            await self._ensure_connection()

            task_id = f"task_{uuid.uuid4().hex[:12]}"
            now = datetime.now()

            task_data = {
                "id": task_id,
                "type": task_type,
                "status": "pending",
                "message": "任务已创建",
                "meta": json.dumps(meta),  # Will be stored as JSONB
                "priority": priority,
                "progress": 0,
                "total": meta.get("total", 0),
                "success": 0,
                "failed": 0,
                "created_at": now,
                "error": None
            }

            await self.storage.insert("tasks", task_data)

            self.logger.info(f"Created task: {task_id}")
            return task_data

        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task by ID

        Args:
            task_id: Task ID

        Returns:
            Task data or None if not found
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()
            query = """
                SELECT id, type, status, message, meta, priority, progress, total,
                       success, failed, created_at, error
                FROM tasks
                WHERE id = $1
            """
            row = await conn.fetchrow(query, task_id)
            await self.storage.pool.release(conn)
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get task {task_id}: {e}")
            raise

    async def get_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get list of tasks

        Args:
            status: Filter by status
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List of tasks
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            conditions = []
            params = []
            param_count = 0

            if status:
                param_count += 1
                conditions.append(f"status = ${param_count}")
                params.append(status)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # Select only columns that exist in the table
            query = f"""
                SELECT id, type, status, message, progress, total, success, failed,
                       created_at
                FROM tasks
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)
            await self.storage.pool.release(conn)

            return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get tasks: {e}")
            raise

    async def update_task(
        self,
        task_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update task

        Args:
            task_id: Task ID
            updates: Fields to update
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            # Build SET clause
            set_clauses = []
            params = []
            param_count = 0

            for key, value in updates.items():
                param_count += 1
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)

            param_count += 1
            params.append(task_id)

            query = f"""
                UPDATE tasks
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count}
            """

            await conn.execute(query, *params)
            await self.storage.pool.release(conn)

            self.logger.debug(f"Updated task {task_id}")

        except Exception as e:
            self.logger.error(f"Failed to update task {task_id}: {e}")
            raise

    async def get_task_stats(self) -> Dict[str, int]:
        """
        Get task statistics

        Returns:
            Task statistics
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
                FROM tasks
            """

            row = await conn.fetchrow(query)
            await self.storage.pool.release(conn)

            return {
                "total": row.get("total", 0) or 0,
                "pending": row.get("pending", 0) or 0,
                "running": row.get("running", 0) or 0,
                "completed": row.get("completed", 0) or 0,
                "failed": row.get("failed", 0) or 0,
                "cancelled": row.get("cancelled", 0) or 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get task stats: {e}")
            raise

    async def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent tasks

        Args:
            limit: Maximum records to return

        Returns:
            List of recent tasks
        """
        try:
            await self._ensure_connection()
            conn = await self.storage._get_connection()

            query = """
                SELECT id, type, status, message, progress, created_at
                FROM tasks
                ORDER BY created_at DESC
                LIMIT $1
            """

            rows = await conn.fetch(query, limit)
            await self.storage.pool.release(conn)

            return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get recent tasks: {e}")
            raise

    async def _ensure_connection(self) -> None:
        """Ensure database connection is established"""
        if not self.storage.connected:
            await self.storage.connect()
