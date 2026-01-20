"""
任务管理API接口 - 使用Pydantic schemas和CRUD模式

遵循FastAPI最佳实践
- 所有数据获取逻辑封装在 DataTasks 类中
- 使用异步后台任务执行数据获取，不阻塞接口
- 接口只负责创建任务和返回响应
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from service.database import get_storage
from service.crud.task_crud import TaskCRUD
from service.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    FetchHistoryRequest,
    FetchRealtimeRequest,
    FetchStockListRequest,
    TaskListResponse,
    TaskListItem,
    TaskStatistics,
    TaskStatsResponse,
    SystemStatus
)
from service.tasks.data_tasks import DataTasks
from data.storage.postgres_storage import PostgreSQLStorage
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="task_api",
    log_level=logging.INFO,
)

router = APIRouter(prefix='/tasks', tags=['tasks'])


# ==================== API 接口 ====================

# ==================== 固定路径（优先匹配） ====================

@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_statistics(
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取任务统计信息

    Returns:
        任务统计数据
    """
    try:
        crud = TaskCRUD(storage)
        stats_dict = await crud.get_task_stats()

        stats = TaskStatistics(**stats_dict)
        return TaskStatsResponse(stats=stats, timestamp=datetime.now())
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取系统状态

    Returns:
        系统状态信息
    """
    try:
        crud = TaskCRUD(storage)

        # Get running tasks count
        running_tasks = await crud.get_tasks(status="running", limit=100)
        active_tasks = len(running_tasks)

        # Get all tasks count
        all_tasks = await crud.get_tasks(limit=1)
        queue_size = len(all_tasks)

        return SystemStatus(
            status="healthy",
            database_connected=storage.connected,
            active_tasks=active_tasks,
            queue_size=queue_size,
            uptime_seconds=86400.0,  # Placeholder
            last_data_update=datetime.now()
        )
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_tasks_endpoint(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取最近的任务

    Args:
        limit: 返回数量

    Returns:
        最近的任务列表
    """
    try:
        crud = TaskCRUD(storage)
        tasks = await crud.get_recent_tasks(limit=limit)
        return {
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        logger.error(f"获取最近任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/history", response_model=TaskResponse)
async def create_fetch_history_task(
    request: FetchHistoryRequest,
    background_tasks: BackgroundTasks,
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    创建历史数据获取任务（后台执行，使用 DataTasks）

    Args:
        request: 获取历史数据请求
        background_tasks: 后台任务
        storage: 数据库实例

    Returns:
        任务信息
    """
    try:
        logger.info(f"创建历史数据获取任务: {len(request.symbols)}只股票")

        crud = TaskCRUD(storage)
        data_tasks = DataTasks(storage)

        # Create task
        meta = {
            "symbols": request.symbols,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "source": request.source,
            "total": len(request.symbols)
        }

        task_data = await crud.create_task("fetch_history", meta, request.priority)

        # Add background task - 使用 DataTasks 的后台任务方法
        background_tasks.add_task(
            data_tasks.fetch_history_background_task,
            task_data["id"],
            request.symbols,
            request.start_date,
            request.end_date,
            request.source
        )

        return TaskResponse(
            task_id=task_data["id"],
            status=task_data["status"],
            message=f"历史数据获取任务已创建，共{len(request.symbols)}只股票",
            task_type=task_data["type"],
            progress=task_data["progress"],
            total=task_data["total"],
            created_at=task_data.get("created_at"),
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at")
        )

    except Exception as e:
        logger.error(f"创建历史数据获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/realtime", response_model=TaskResponse)
async def create_fetch_realtime_task(
    request: FetchRealtimeRequest,
    background_tasks: BackgroundTasks,
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    创建实时行情获取任务（后台执行，使用 DataTasks）

    Args:
        request: 获取实时行情请求
        background_tasks: 后台任务
        storage: 数据库实例

    Returns:
        任务信息
    """
    try:
        logger.info(f"创建实时行情获取任务: {len(request.symbols)}只股票")

        crud = TaskCRUD(storage)
        data_tasks = DataTasks(storage)

        # Create task
        meta = {
            "symbols": request.symbols,
            "source": request.source,
            "store": request.store,
            "total": len(request.symbols)
        }

        task_data = await crud.create_task("fetch_realtime", meta, priority="medium")

        # Add background task - 使用 DataTasks 的后台任务方法
        background_tasks.add_task(
            data_tasks.fetch_realtime_background_task,
            task_data["id"],
            request.symbols,
            request.source,
            request.store
        )

        return TaskResponse(
            task_id=task_data["id"],
            status=task_data["status"],
            message=f"实时行情获取任务已创建，共{len(request.symbols)}只股票",
            task_type=task_data["type"],
            progress=task_data["progress"],
            total=task_data["total"],
            created_at=task_data.get("created_at"),
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at")
        )

    except Exception as e:
        logger.error(f"创建实时行情获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/stocklist", response_model=TaskResponse)
async def create_fetch_stocklist_task(
    request: FetchStockListRequest,
    background_tasks: BackgroundTasks,
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    创建股票列表获取任务（后台执行，使用 DataTasks）

    Args:
        request: 获取股票列表请求
        background_tasks: 后台任务
        storage: 数据库实例

    Returns:
        任务信息
    """
    try:
        logger.info(f"创建股票列表获取任务，数据源: {request.source}")

        crud = TaskCRUD(storage)
        data_tasks = DataTasks(storage)

        # Create task
        meta = {
            "source": request.source,
            "store": request.store,
            "force_refresh": request.force_refresh
        }

        task_data = await crud.create_task("fetch_stocklist", meta, priority="low")

        # Add background task - 使用 DataTasks 的后台任务方法
        background_tasks.add_task(
            data_tasks.fetch_stocklist_background_task,
            task_data["id"],
            request.source,
            request.store
        )

        return TaskResponse(
            task_id=task_data["id"],
            status=task_data["status"],
            message=f"股票列表获取任务已创建，数据源: {request.source}",
            task_type=task_data["type"],
            progress=task_data["progress"],
            total=None,
            created_at=task_data.get("created_at"),
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at")
        )

    except Exception as e:
        logger.error(f"创建股票列表获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=TaskListResponse)
async def get_all_tasks(
    status: Optional[str] = Query(None, description="任务状态过滤"),
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取任务列表

    Args:
        status: 任务状态过滤 (pending, running, completed, failed)
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        任务列表
    """
    try:
        crud = TaskCRUD(storage)
        tasks = await crud.get_tasks(status=status, limit=limit, offset=offset)

        # Convert to TaskListItem format
        task_items = []
        for task in tasks:
            task_items.append(TaskListItem(
                task_id=task.get("id"),
                task_type=task.get("type"),
                status=task.get("status"),
                message=task.get("message"),
                progress=task.get("progress"),
                created_at=task.get("created_at"),
                started_at=task.get("started_at"),
                completed_at=task.get("completed_at")
            ))

        return TaskListResponse(
            tasks=task_items,
            total=len(task_items),
            count=len(task_items),
            status=status,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    创建新任务

    Args:
        request: 任务创建请求
        storage: 数据库实例

    Returns:
        创建的任务信息
    """
    try:
        crud = TaskCRUD(storage)
        task_data = await crud.create_task(
            task_type=request.task_type,
            meta=request.meta,
            priority=request.priority
        )

        return TaskResponse(
            task_id=task_data["id"],
            status=task_data["status"],
            message="任务已创建",
            task_type=task_data["type"],
            progress=task_data["progress"],
            total=task_data["total"],
            created_at=task_data.get("created_at"),
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at")
        )
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 参数路径（后匹配） ====================

@router.get("/{task_id}")
async def get_task_by_id(
    task_id: str,
    storage: PostgreSQLStorage = Depends(get_storage)
):
    """
    获取指定任务信息

    Args:
        task_id: 任务ID
        storage: 数据库实例

    Returns:
        任务信息
    """
    try:
        crud = TaskCRUD(storage)
        task = await crud.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
