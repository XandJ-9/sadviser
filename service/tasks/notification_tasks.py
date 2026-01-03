import asyncio
import logging

logger = logging.getLogger(__name__)

class NotificationTasks:
    """Notification tasks"""
    
    async def send_daily_report(self):
        """Send daily report to subscribed users"""
        logger.info("Sending daily reports...")
        await asyncio.sleep(1)
        logger.info("Daily reports sent")
