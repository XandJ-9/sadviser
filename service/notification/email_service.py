import logging
from typing import List

logger = logging.getLogger(__name__)

class EmailService:
    """Email notification service"""
    
    def send_email(self, to: str, subject: str, content: str):
        logger.info(f"Sending email to {to}: {subject}")
        # Implementation placeholder
