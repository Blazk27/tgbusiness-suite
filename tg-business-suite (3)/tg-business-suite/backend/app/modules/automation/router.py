"""
Automation router
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.modules.auth.dependencies import (
    get_current_verified_user,
    require_org_admin,
)
from app.modules.users.models import User
from app.modules.automation.schemas import (
    AutomationTaskCreate,
    AutomationTaskResponse,
    BulkTaskCreate,
    TaskProgressResponse,
)
from app.modules.automation.service import AutomationService
from app.modules.automation.tasks import celery_app

router = APIRouter(prefix="/tasks", tags=["Automation"])


@router.get("", response_model=List[AutomationTaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """List automation tasks for the organization"""
    service = AutomationService(db)
    return await service.get_tasks(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        status=status_filter
    )


@router.post("", response_model=AutomationTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: AutomationTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    request = None
):
    """Create a new automation task"""
    service = AutomationService(db)

    # Verify account ownership
    account = await service.verify_account_ownership(
        data.account_id,
        current_user.organization_id
    )

    # Create task
    task = await service.create_task(
        account_id=data.account_id,
        user_id=current_user.id,
        task_type=data.type,
        payload=data.payload,
        scheduled_for=data.scheduled_for
    )

    # Queue task
    if data.scheduled_for and data.scheduled_for > datetime.utcnow():
        # Schedule for later
        celery_app.send_task(
            "app.modules.automation.tasks.execute_automation_task",
            args=[str(task.id)],
            eta=data.scheduled_for
        )
    else:
        # Execute immediately
        celery_app.send_task(
            "app.modules.automation.tasks.execute_automation_task",
            args=[str(task.id)]
        )

    # Log activity
    from app.modules.auth.dependencies import log_activity
    await log_activity(
        db=db,
        user=current_user,
        action="create_task",
        resource_type="automation_task",
        resource_id=str(task.id),
        request=request
    )

    return task


@router.post("/bulk", response_model=List[AutomationTaskResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_tasks(
    data: BulkTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    request = None
):
    """Create multiple automation tasks"""
    service = AutomationService(db)

    # Verify account ownership
    for account_id in data.account_ids:
        await service.verify_account_ownership(
            account_id,
            current_user.organization_id
        )

    # Create tasks
    tasks = await service.create_bulk_tasks(
        account_ids=data.account_ids,
        user_id=current_user.id,
        task_type=data.type,
        payload=data.payload,
        scheduled_for=data.scheduled_for
    )

    # Queue all tasks
    for task in tasks:
        celery_app.send_task(
            "app.modules.automation.tasks.execute_automation_task",
            args=[str(task.id)]
        )

    # Log activity
    from app.modules.auth.dependencies import log_activity
    await log_activity(
        db=db,
        user=current_user,
        action="create_bulk_tasks",
        resource_type="automation_task",
        metadata={"task_count": len(tasks)},
        request=request
    )

    return tasks


@router.get("/{task_id}", response_model=AutomationTaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Get task details"""
    service = AutomationService(db)
    return await service.get_task(task_id, current_user.organization_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Cancel a pending task"""
    service = AutomationService(db)
    await service.cancel_task(task_id, current_user.organization_id)


@router.get("/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Get task progress"""
    service = AutomationService(db)
    task = await service.get_task(task_id, current_user.organization_id)

    return TaskProgressResponse(
        task_id=str(task.id),
        status=task.status,
        progress=task.progress,
        error_message=task.error_message
    )
