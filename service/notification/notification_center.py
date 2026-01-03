from typing import List, Dict, Any
from .email_service import EmailService
from .websocket_service import WebSocketService
from .sms_service import SMSService

class NotificationCenter:
    """Unified notification center"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.websocket_service = WebSocketService()
        self.sms_service = SMSService()

    def notify_user(self, user_contact: Dict[str, str], message: str, channels: List[str] = None):
        """Notify user through specified channels"""
        if channels is None:
            channels = ["email"]
            
        if "email" in channels and "email" in user_contact:
            self.email_service.send_email(user_contact["email"], "Notification", message)
            
        if "sms" in channels and "phone" in user_contact:
            self.sms_service.send_sms(user_contact["phone"], message)
            
        if "websocket" in channels:
            self.websocket_service.broadcast({"user": user_contact.get("id"), "message": message})
