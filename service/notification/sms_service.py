import logging

logger = logging.getLogger(__name__)

class SMSService:
    """SMS notification service"""
    
    def send_sms(self, phone_number: str, message: str):
        logger.info(f"Sending SMS to {phone_number}: {message}")
        # Implementation placeholder
