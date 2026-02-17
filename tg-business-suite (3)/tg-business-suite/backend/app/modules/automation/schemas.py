"""
Pydantic schemas for Automation
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import TaskType, TaskStatus


class TaskPayload(BaseModel):
    """Task payload schema"""
    # For PROFILE_PHOTO
    photo_path: Optional[str] = None
    # For BIO_UPDATE
    bio: Optional[str] = None
    # For USERNAME_UPDATE
    username: Optional[str] = None
    # For MEDIA_SEND
    media_path: Optional[str] = None
    media_type: Optional[str] = None
    # For MESSAGE_SEND
    message: Optional[str] = None
    peer_id: Optional[int] = None
    peer_ids: Optional[List[int]] = None


class AutomationTaskBase(BaseModel):
    """Base automation task schema"""
    account_id: str
    type: TaskType
    payload: Dict[str, Any]


class AutomationTaskCreate(AutomationTaskBase):
    """Automation task creation schema"""
    scheduled_for: Optional[datetime] = None


class AutomationTaskUpdate(BaseModel):
    """Automation task update schema"""
    status: Optional[TaskStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)


class AutomationTaskResponse(AutomationTaskBase):
    """Automation task response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: str
    status: TaskStatus
    scheduled_for: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    progress: int
    created_at: datetime


class BulkTaskCreate(BaseModel):
    """Bulk task creation schema"""
    account_ids: List[str]
    type: TaskType
    payload: Dict[str, Any]
    scheduled_for: Optional[datetime] = None


class TaskProgressResponse(BaseModel):
    """Task progress response schema"""
    task_id: str
    status: TaskStatus
    progress: int
    error_message: Optional[str] = None
