"""
事件響應系統
提供數據洩露和網絡安全事件的響應機制
"""

from .breach_notification import BreachNotification
from .incident_manager import IncidentManager
from .incident_templates import NotificationTemplate

__all__ = ["IncidentManager", "BreachNotification", "NotificationTemplate"]
