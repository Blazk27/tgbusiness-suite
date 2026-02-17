"""
Telegram service using Telethon
"""

import asyncio
import random
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.encryption import encryption_service
from app.core.exceptions import TelegramException, NotFoundException
from app.core.constants import AccountStatus, ProxyProtocol
from app.modules.telegram.models import TelegramAccount
from app.modules.proxies.models import Proxy

settings = get_settings()


class TelegramService:
    """Telegram integration service using Telethon"""

    def __init__(self):
        self._clients: Dict[str, Any] = {}  # In-memory client cache

    async def add_account(
        self,
        db: AsyncSession,
        phone_number: str,
        session_data: bytes,
        api_id: int,
        api_hash: str,
        proxy_id: Optional[UUID] = None,
        daily_limit: int = 20
    ) -> TelegramAccount:
        """
        Add a new Telegram account with encrypted session
        """
        # Encrypt session before storing
        encrypted_session = encryption_service.encrypt(session_data)

        account = TelegramAccount(
            phone_number=phone_number,
            session_encrypted=encrypted_session,
            api_id=api_id,
            api_hash=api_hash,
            proxy_id=proxy_id,
            status=AccountStatus.PENDING,
            daily_limit=daily_limit,
        )

        db.add(account)
        await db.commit()
        await db.refresh(account)

        return account

    async def connect_account(
        self,
        db: AsyncSession,
        account_id: UUID
    ) -> Dict[str, Any]:
        """
        Connect to Telegram and verify account
        """
        # Get account from database
        result = await db.execute(
            select(TelegramAccount).where(TelegramAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise NotFoundException("Account not found")

        # Get proxy if assigned
        proxy_config = None
        if account.proxy_id:
            proxy_result = await db.execute(
                select(Proxy).where(Proxy.id == account.proxy_id)
            )
            proxy = proxy_result.scalar_one_or_none()
            if proxy:
                proxy_config = self._build_proxy_config(proxy)

        try:
            # Decrypt session
            session_bytes = encryption_service.decrypt(account.session_encrypted)

            # Create Telethon client
            from telethon import TelegramClient
            from telethon.connection import ConnectionMode

            client = TelegramClient(
                session=session_bytes,
                api_id=account.api_id,
                api_hash=account.api_hash,
                proxy=proxy_config,
                device_model="iPhone 15 Pro",
                system_version="17.0",
                app_version="8.4.2",
                lang_code="en",
                system_lang_code="en-US",
            )

            # Connect and get self
            await client.connect()

            if not await client.is_user_authorized():
                account.status = AccountStatus.AUTH_REQUIRED
                await db.commit()
                await client.disconnect()
                return {"status": "auth_required", "message": "Authorization required"}

            me = await client.get_me()

            # Update account info
            account.username = me.username or None
            account.first_name = me.first_name
            account.last_name = me.last_name or None
            account.status = AccountStatus.ACTIVE
            account.last_active = datetime.utcnow()
            await db.commit()

            # Cache client
            self._clients[str(account_id)] = client

            return {
                "status": "connected",
                "username": me.username,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "is_premium": getattr(me, 'premium', False),
            }

        except Exception as e:
            account.status = AccountStatus.CONNECTION_ERROR
            await db.commit()
            raise TelegramException(f"Failed to connect: {str(e)}")

    async def disconnect_account(
        self,
        db: AsyncSession,
        account_id: UUID
    ) -> bool:
        """
        Disconnect Telegram account
        """
        # Remove from cache
        if str(account_id) in self._clients:
            client = self._clients[str(account_id)]
            await client.disconnect()
            del self._clients[str(account_id)]

        # Update status
        result = await db.execute(
            select(TelegramAccount).where(TelegramAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if account:
            account.status = AccountStatus.INACTIVE
            await db.commit()

        return True

    async def check_account_status(
        self,
        db: AsyncSession,
        account_id: UUID
    ) -> Dict[str, Any]:
        """
        Check account status and health
        """
        result = await db.execute(
            select(TelegramAccount).where(TelegramAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise NotFoundException("Account not found")

        # If connected, verify connection
        if account.status == AccountStatus.ACTIVE:
            client = self._clients.get(str(account_id))
            if client:
                try:
                    await client.get_me()
                    return {
                        "status": account.status.value,
                        "username": account.username,
                        "first_name": account.first_name,
                        "last_name": account.last_name,
                        "last_active": account.last_active,
                    }
                except Exception:
                    # Connection lost
                    account.status = AccountStatus.CONNECTION_ERROR
                    await db.commit()

        return {
            "status": account.status.value,
            "username": account.username,
            "first_name": account.first_name,
            "last_name": account.last_name,
            "last_active": account.last_active,
        }

    async def send_message(
        self,
        account_id: UUID,
        peer_id: int,
        message: str
    ) -> bool:
        """
        Send message using account
        """
        client = self._clients.get(str(account_id))
        if not client:
            raise TelegramException("Account not connected")

        try:
            await client.send_message(peer_id, message)
            return True
        except Exception as e:
            raise TelegramException(f"Failed to send message: {str(e)}")

    async def update_profile(
        self,
        account_id: UUID,
        **kwargs
    ) -> bool:
        """
        Update account profile
        """
        client = self._clients.get(str(account_id))
        if not client:
            raise TelegramException("Account not connected")

        try:
            await client(
                lambda: client.functions.account.UpdateProfileRequest(**kwargs)
            )
            return True
        except Exception as e:
            raise TelegramException(f"Failed to update profile: {str(e)}")

    async def upload_profile_photo(
        self,
        account_id: UUID,
        file_path: str
    ) -> bool:
        """
        Upload profile photo
        """
        client = self._clients.get(str(account_id))
        if not client:
            raise TelegramException("Account not connected")

        try:
            await client.upload_profile_photo(file=file_path)
            return True
        except Exception as e:
            raise TelegramException(f"Failed to upload photo: {str(e)}")

    async def send_media(
        self,
        account_id: UUID,
        peer_id: int,
        file_path: str,
        caption: Optional[str] = None
    ) -> bool:
        """
        Send media file
        """
        client = self._clients.get(str(account_id))
        if not client:
            raise TelegramException("Account not connected")

        try:
            await client.send_file(
                peer_id,
                file_path,
                caption=caption
            )
            return True
        except Exception as e:
            raise TelegramException(f"Failed to send media: {str(e)}")

    def _build_proxy_config(self, proxy: Proxy) -> tuple:
        """Build proxy configuration for Telethon"""
        if proxy.protocol == ProxyProtocol.SOCKS5:
            return (proxy.ip, proxy.port, proxy.username, proxy.password)
        elif proxy.protocol == ProxyProtocol.HTTP:
            return (proxy.ip, proxy.port, proxy.username, proxy.password, True)
        else:
            return None


# Singleton instance
telegram_service = TelegramService()
