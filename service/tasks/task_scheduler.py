import asyncio
import logging
from typing import List, Callable, Awaitable

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Simple async task scheduler"""
    
    def __init__(self):
        self.tasks = []

    def add_task(self, task_func: Callable[[], Awaitable[None]], interval_seconds: int):
        self.tasks.append((task_func, interval_seconds))

    async def start(self):
        """Start the scheduler"""
        logger.info("Starting task scheduler...")
        # In a real implementation, this would loop and run tasks
        # For now, just a placeholder
        pass
