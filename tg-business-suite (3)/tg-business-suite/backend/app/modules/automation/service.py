"""
Automation service
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundException, ForbiddenException
from app.core.constants import TaskStatus, TaskType
from app.modules.automation.models import AutomationTask
from app.modules.telegram.models import TelegramAccount


class AutomationService:
    """Automation service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_account_ownership(
        self,
        account_id: UUID,
        organization_id: UUID
    ) -> TelegramAccount:
        """Verify account belongs to organization"""
        result = await self.db.execute(
            select(TelegramAccount).where(
                TelegramAccount.id == account_id,
                TelegramAccount.organization_id == organization_id
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            raise NotFoundException("Account not found")

        return account

    async def create_task(
        self,
        account_id: UUID,
        user_id: UUID,
        task_type: TaskType,
        payload: dict,
        scheduled_for: Optional[datetime] = None
    ) -> AutomationTask:
        """Create a single automation task"""
        task = AutomationTask(
            organization_id=(
                await self.verify_account_ownership(
                    account_id,
                    (
                        await self.db.execute(
                            select(TelegramAccount).where(
                                TelegramAccount.id == account_id
                            )
                        )
                    ).scalar_one().organization_id
                )
            ).organization_id,
            account_id=account_id,
            user_id=user_id,
            type=task_type,
            payload=payload,
            status=TaskStatus.PENDING,
            scheduled_for=scheduled_for,
            progress=0,
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def create_bulk_tasks(
        self,
        account_ids: List[UUID],
        user_id: UUID,
        task_type: TaskType,
        payload: dict,
        scheduled_for: Optional[datetime] = None
    ) -> List[AutomationTask]:
        """Create multiple automation tasks"""
        tasks = []

        # Get organization from first account
        first_account = await self.verify_account_ownership(
            account_ids[0],
            (
                await self.db.execute(
                    select(TelegramAccount).where(
                        TelegramAccount.id == account_ids[0]
                    )
                )
            ).scalar_one().organization_id
        )

        organization_id = first_account.organization_id

        for account_id in account_ids:
            # Verify ownership
            await self.verify_account_ownership(account_id, organization_id)

            task = AutomationTask(
                organization_id=organization_id,
                account_id=account_id,
                user_id=user_id,
                type=task_type,
                payload=payload,
                status=TaskStatus.PENDING,
                scheduled_for=scheduled_for,
                progress=0,
            )
            self.db.add(task)
            tasks.append(task)

        await self.db.commit()

        for task in tasks:
            await self.db.refresh(task)

        return tasks

    async def get_task(
        self,
        task_id: UUID,
        organization_id: UUID
    ) -> AutomationTask:
        """Get task by ID"""
        result = await self.db.execute(
            select(AutomationTask).where(
                AutomationTask.id == task_id,
                AutomationTask.organization_id == organization_id
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundException("Task not found")

        return task

    async def get_tasks(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None
    ) -> List[AutomationTask]:
        """Get tasks for organization"""
        query = select(AutomationTask).where(
            AutomationTask.organization_id == organization_id
        )

        if status:
            query = query.where(AutomationTask.status == status)

        query = query.offset(skip).limit(limit).order_by(
            AutomationTask.created_at.desc()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cancel_task(
        self,
        task_id: UUID,
        organization_id: UUID
    ) -> AutomationTask:
        """Cancel a pending task"""
        task = await self.get_task(task_id, organization_id)

        if task.status != TaskStatus.PENDING:
            raise ForbiddenException("Only pending tasks can be cancelled")

        task.status = TaskStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task_stats(
        self,
        organization_id: UUID
    ) -> dict:
        """Get task statistics for organization"""
        from sqlalchemy import func

        # Total tasks
        total_result = await self.db.execute(
            select(func.count(AutomationTask.id)).where(
                AutomationTask.organization_id == organization_id
            )
        )
        total = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(
                AutomationTask.status,
                func.count(AutomationTask.id)
            ).where(
                AutomationTask.organization_id == organization_id
            ).group_by(AutomationTask.status)
        )

        stats = {
            "total": total,
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }

        for status, count in status_result.fetchall():
            stats[status.value] = count

        return stats
