"""
Celery tasks for automation engine
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Dict, Any

from celery import Celery
from celery.utils.log import get_task_logger

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.encryption import encryption_service
from app.core.constants import (
    TaskStatus,
    TaskType,
    AccountStatus,
    MIN_DELAY_SECONDS,
    MAX_DELAY_SECONDS,
    MAX_RETRY_ATTEMPTS,
)

settings = get_settings()

# Initialize Celery
celery_app = Celery(
    "tg_business_suite",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
)

logger = get_task_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def execute_automation_task(self, task_id: str) -> Dict[str, Any]:
    """
    Execute automation task
    """
    logger.info(f"Starting task {task_id}")

    async def _execute():
        from sqlalchemy import select, update
        from app.modules.automation.models import AutomationTask
        from app.modules.telegram.models import TelegramAccount

        db = await get_db_session()

        try:
            # Get task
            result = await db.execute(
                select(AutomationTask).where(AutomationTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"Task {task_id} not found")
                return {"error": "Task not found"}

            # Get account
            account_result = await db.execute(
                select(TelegramAccount).where(TelegramAccount.id == task.account_id)
            )
            account = account_result.scalar_one_or_none()

            if not account:
                logger.error(f"Account {task.account_id} not found")
                task.status = TaskStatus.FAILED
                task.error_message = "Account not found"
                await db.commit()
                return {"error": "Account not found"}

            # Check if account is active
            if account.status != AccountStatus.ACTIVE:
                task.status = TaskStatus.FAILED
                task.error_message = f"Account is {account.status.value}"
                await db.commit()
                return {"error": f"Account is {account.status.value}"}

            # Check daily limit
            if account.actions_today >= account.daily_limit:
                task.status = TaskStatus.FAILED
                task.error_message = "Daily limit exceeded"
                await db.commit()
                return {"error": "Daily limit exceeded"}

            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await db.commit()

            # Decrypt session
            session_bytes = encryption_service.decrypt(account.session_encrypted)

            # Execute task based on type
            result_data = await execute_telegram_action(
                session_bytes=session_bytes,
                api_id=account.api_id,
                api_hash=account.api_hash,
                task_type=task.type,
                payload=task.payload,
            )

            # Update task on success
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.progress = 100
            task.error_message = None

            # Update account stats
            account.actions_today += 1
            account.last_action_at = datetime.utcnow()

            await db.commit()

            logger.info(f"Task {task_id} completed successfully")
            return {"status": "completed", "result": result_data}

        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")

            # Get task to update
            result = await db.execute(
                select(AutomationTask).where(AutomationTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if task:
                task.retry_count += 1

                if task.retry_count >= MAX_RETRY_ATTEMPTS:
                    task.status = TaskStatus.FAILED
                    task.error_message = str(e)
                else:
                    task.status = TaskStatus.PENDING

                await db.commit()

            # Retry task
            raise self.retry(exc=e)

        finally:
            await db.close()

    # Run async function
    return asyncio.run(_execute())


async def execute_telegram_action(
    session_bytes: bytes,
    api_id: int,
    api_hash: str,
    task_type: TaskType,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Telegram action based on task type
    """
    from telethon import TelegramClient

    # Create client
    client = TelegramClient(
        session=session_bytes,
        api_id=api_id,
        api_hash=api_hash,
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            return {"error": "Not authorized"}

        # Apply random delay for anti-ban
        delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
        logger.info(f"Applying delay of {delay} seconds")
        await asyncio.sleep(delay)

        if task_type == TaskType.PROFILE_PHOTO:
            # Upload profile photo
            photo_path = payload.get("photo_path")
            if photo_path:
                await client.upload_profile_photo(file=photo_path)
                return {"status": "photo_uploaded"}

        elif task_type == TaskType.BIO_UPDATE:
            # Update bio
            bio = payload.get("bio")
            if bio:
                await client(
                    lambda: client.functions.account.UpdateProfileRequest(
                        about=bio
                    )
                )
                return {"status": "bio_updated"}

        elif task_type == TaskType.USERNAME_UPDATE:
            # Update username
            username = payload.get("username")
            if username:
                await client(
                    lambda: client.functions.account.UpdateUsernameRequest(
                        username=username
                    )
                )
                return {"status": "username_updated"}

        elif task_type == TaskType.MEDIA_SEND:
            # Send media
            media_path = payload.get("media_path")
            peer_id = payload.get("peer_id")
            caption = payload.get("caption")

            if media_path and peer_id:
                await client.send_file(
                    peer_id,
                    media_path,
                    caption=caption
                )
                return {"status": "media_sent"}

        elif task_type == TaskType.MESSAGE_SEND:
            # Send message
            message = payload.get("message")
            peer_id = payload.get("peer_id")

            if message and peer_id:
                await client.send_message(peer_id, message)
                return {"status": "message_sent"}

        return {"error": "Invalid task parameters"}

    finally:
        await client.disconnect()


@celery_app.task
def cleanup_daily_limits():
    """
    Reset daily action limits for all accounts
    Called once per day via Celery Beat
    """
    logger.info("Running daily limits cleanup")

    async def _cleanup():
        from sqlalchemy import update
        from app.modules.telegram.models import TelegramAccount

        db = await get_db_session()

        try:
            await db.execute(
                update(TelegramAccount)
                .values(actions_today=0)
            )
            await db.commit()
            logger.info("Daily limits reset completed")

        finally:
            await db.close()

    asyncio.run(_cleanup())


@celery_app.task
def check_account_health(account_id: str):
    """
    Check account health and connectivity
    """
    logger.info(f"Checking health for account {account_id}")

    async def _check():
        from sqlalchemy import select, update
        from app.modules.telegram.models import TelegramAccount
        from app.core.constants import AccountStatus

        db = await get_db_session()

        try:
            result = await db.execute(
                select(TelegramAccount).where(
                    TelegramAccount.id == account_id
                )
            )
            account = result.scalar_one_or_none()

            if not account:
                return {"error": "Account not found"}

            # Try to connect and check status
            session_bytes = encryption_service.decrypt(account.session_encrypted)

            from telethon import TelegramClient

            client = TelegramClient(
                session=session_bytes,
                api_id=account.api_id,
                api_hash=account.api_hash,
            )

            try:
                await client.connect()

                if await client.is_user_authorized():
                    me = await client.get_me()
                    account.status = AccountStatus.ACTIVE
                    account.last_active = datetime.utcnow()
                    await db.commit()
                    return {"status": "active", "username": me.username}
                else:
                    account.status = AccountStatus.AUTH_REQUIRED
                    await db.commit()
                    return {"status": "auth_required"}

            except Exception as e:
                account.status = AccountStatus.CONNECTION_ERROR
                await db.commit()
                return {"status": "error", "error": str(e)}

            finally:
                await client.disconnect()

        finally:
            await db.close()

    asyncio.run(_check())


# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-daily-limits": {
        "task": "app.modules.automation.tasks.cleanup_daily_limits",
        "schedule": 0,  # Run at midnight UTC - configure with cron
    },
}
