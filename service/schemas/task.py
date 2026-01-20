"""
Task-related Pydantic schemas

Defines all request/response models for task management endpoints.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class TaskCreateRequest(BaseModel):
    """Request for creating a task"""
    task_type: Literal["fetch_history", "fetch_realtime", "fetch_stocklist", "backtest", "screen"] = Field(
        ...,
        description="Task type"
    )
    meta: Dict[str, Any] = Field(..., description="Task metadata and parameters")
    priority: Literal["low", "medium", "high"] = Field("medium", description="Task priority")
    scheduled_at: Optional[str] = Field(None, description="Scheduled execution time (ISO format)")

    @field_validator('scheduled_at')
    @classmethod
    def validate_scheduled_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate scheduled time format"""
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError('scheduled_at must be in ISO format')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "fetch_history",
                "meta": {
                    "symbols": ["sh600000", "sh600519"],
                    "start_date": "2025-01-01",
                    "end_date": "2026-01-19",
                    "source": "akshare"
                },
                "priority": "medium",
                "scheduled_at": None
            }
        }


class TaskResponse(BaseModel):
    """Response for task operations"""
    task_id: str = Field(..., description="Unique task identifier")
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = Field(
        ...,
        description="Task status"
    )
    message: str = Field(..., description="Task message")
    task_type: Optional[str] = Field(None, description="Task type")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)", ge=0, le=100)
    total: Optional[int] = Field(None, description="Total items to process", ge=0)
    success: Optional[int] = Field(None, description="Number of successful items", ge=0)
    failed: Optional[int] = Field(None, description="Number of failed items", ge=0)
    created_at: Optional[datetime] = Field(None, description="Task creation time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_123456",
                "status": "running",
                "message": "正在获取数据",
                "task_type": "fetch_history",
                "progress": 50,
                "total": 100,
                "success": 50,
                "failed": 0,
                "created_at": "2026-01-19T10:00:00",
                "started_at": "2026-01-19T10:01:00",
                "completed_at": None,
                "error": None
            }
        }


class FetchHistoryRequest(BaseModel):
    """Request for fetching historical data"""
    symbols: List[str] = Field(..., description="List of stock symbols", min_length=1)
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    source: Literal["akshare", "tushare", "sina"] = Field("akshare", description="Data source")
    priority: Literal["low", "medium", "high"] = Field("medium", description="Task priority")

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        """Validate end_date is after start_date"""
        if 'start_date' in info.data:
            start_date = info.data['start_date']
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(v, '%Y-%m-%d')
                if end <= start:
                    raise ValueError('end_date must be after start_date')
            except ValueError as e:
                if 'must be after' not in str(e):
                    raise e
        return v

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v: List[str]) -> List[str]:
        """Validate symbols list is not empty"""
        if not v:
            raise ValueError('symbols list cannot be empty')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["sh600000", "sh600519"],
                "start_date": "2025-01-01",
                "end_date": "2026-01-19",
                "source": "akshare",
                "priority": "medium"
            }
        }


class FetchRealtimeRequest(BaseModel):
    """Request for fetching realtime quotes"""
    symbols: List[str] = Field(..., description="List of stock symbols", min_length=1, max_length=100)
    source: Literal["akshare", "tushare", "sina"] = Field("akshare", description="Data source")
    store: bool = Field(True, description="Whether to store in database")

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v: List[str]) -> List[str]:
        """Validate symbols list is not empty and not too large"""
        if not v:
            raise ValueError('symbols list cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot fetch more than 100 symbols at once')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["sh600000", "sh600519"],
                "source": "akshare",
                "store": True
            }
        }


class FetchStockListRequest(BaseModel):
    """Request for fetching stock list"""
    source: Literal["akshare", "tushare"] = Field("akshare", description="Data source")
    store: bool = Field(False, description="Whether to store in database")
    force_refresh: bool = Field(False, description="Force refresh even if recently updated")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "akshare",
                "store": True,
                "force_refresh": False
            }
        }


class TaskListItem(BaseModel):
    """Task list item"""
    task_id: str = Field(..., description="Task ID")
    task_type: str = Field(..., description="Task type")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Task message")
    progress: Optional[int] = Field(None, description="Progress percentage")
    created_at: datetime = Field(..., description="Creation time")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_123456",
                "task_type": "fetch_history",
                "status": "completed",
                "message": "任务完成",
                "progress": 100,
                "created_at": "2026-01-19T10:00:00",
                "started_at": "2026-01-19T10:01:00",
                "completed_at": "2026-01-19T10:30:00"
            }
        }


class TaskListResponse(BaseModel):
    """Response for task list endpoint"""
    tasks: List[TaskListItem] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks", ge=0)
    count: int = Field(..., description="Number of tasks returned", ge=0)
    status: Optional[str] = Field(None, description="Filter status used")
    limit: int = Field(..., description="Limit used", ge=1)
    offset: int = Field(..., description="Offset used", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [],
                "total": 100,
                "count": 10,
                "status": None,
                "limit": 10,
                "offset": 0
            }
        }


class TaskStatistics(BaseModel):
    """Task statistics"""
    total: int = Field(..., description="Total tasks", ge=0)
    pending: int = Field(..., description="Pending tasks", ge=0)
    running: int = Field(..., description="Running tasks", ge=0)
    completed: int = Field(..., description="Completed tasks", ge=0)
    failed: int = Field(..., description="Failed tasks", ge=0)
    cancelled: int = Field(..., description="Cancelled tasks", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "pending": 10,
                "running": 5,
                "completed": 80,
                "failed": 3,
                "cancelled": 2
            }
        }


class TaskStatsResponse(BaseModel):
    """Response for task statistics endpoint"""
    stats: TaskStatistics = Field(..., description="Task statistics")
    timestamp: datetime = Field(..., description="Statistics timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "stats": {},
                "timestamp": "2026-01-19T10:30:00"
            }
        }


class SystemStatus(BaseModel):
    """System status information"""
    status: Literal["healthy", "degraded", "down"] = Field(..., description="System status")
    database_connected: bool = Field(..., description="Database connection status")
    active_tasks: int = Field(..., description="Number of active tasks", ge=0)
    queue_size: int = Field(..., description="Task queue size", ge=0)
    uptime_seconds: float = Field(..., description="System uptime in seconds", ge=0)
    last_data_update: Optional[datetime] = Field(None, description="Last data update time")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database_connected": True,
                "active_tasks": 2,
                "queue_size": 5,
                "uptime_seconds": 86400.0,
                "last_data_update": "2026-01-19T09:00:00"
            }
        }
