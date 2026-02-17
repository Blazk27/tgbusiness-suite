"""
Automation module
"""

from app.modules.automation.router import router
from app.modules.automation.service import AutomationService
from app.modules.automation.schemas import (
    AutomationTaskCreate,
    AutomationTaskResponse,
    BulkTaskCreate,
    TaskProgressResponse,
)
from app.modules.automation.tasks import (
    celery_app,
    execute_automation_task,
    cleanup_daily_limits,
    check_account_health,
)

__all__ = [
    "router",
    "AutomationService",
    "AutomationTaskCreate",
    "AutomationTaskResponse",
    "BulkTaskCreate",
    "TaskProgressResponse",
    "celery_app",
    "execute_automation_task",
    "cleanup_daily_limits",
    "check_account_health",
]
