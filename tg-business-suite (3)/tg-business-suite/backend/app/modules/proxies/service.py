"""
Proxy service
"""

import asyncio
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundException
from app.core.constants import ProxyStatus, ProxyProtocol
from app.modules.proxies.models import Proxy


class ProxyService:
    """Proxy management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_proxies(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Proxy]:
        """Get all proxies for organization"""
        result = await self.db.execute(
            select(Proxy)
            .where(Proxy.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_proxy(
        self,
        proxy_id: UUID,
        organization_id: UUID
    ) -> Proxy:
        """Get proxy by ID"""
        result = await self.db.execute(
            select(Proxy).where(
                Proxy.id == proxy_id,
                Proxy.organization_id == organization_id
            )
        )
        proxy = result.scalar_one_or_none()

        if not proxy:
            raise NotFoundException("Proxy not found")

        return proxy

    async def create_proxy(
        self,
        organization_id: UUID,
        ip: str,
        port: int,
        username: Optional[str],
        password: Optional[str],
        protocol: ProxyProtocol
    ) -> Proxy:
        """Create a new proxy"""
        proxy = Proxy(
            organization_id=organization_id,
            ip=ip,
            port=port,
            username=username,
            password=password,
            protocol=protocol,
            status=ProxyStatus.INACTIVE,
        )

        self.db.add(proxy)
        await self.db.commit()
        await self.db.refresh(proxy)

        return proxy

    async def update_proxy(
        self,
        proxy_id: UUID,
        organization_id: UUID,
        data: dict
    ) -> Proxy:
        """Update proxy"""
        proxy = await self.get_proxy(proxy_id, organization_id)

        for key, value in data.items():
            if hasattr(proxy, key):
                setattr(proxy, key, value)

        await self.db.commit()
        await self.db.refresh(proxy)

        return proxy

    async def delete_proxy(
        self,
        proxy_id: UUID,
        organization_id: UUID
    ) -> None:
        """Delete proxy"""
        proxy = await self.get_proxy(proxy_id, organization_id)
        await self.db.delete(proxy)
        await self.db.commit()

    async def test_proxy(
        self,
        proxy_id: UUID,
        organization_id: UUID
    ) -> Dict:
        """Test proxy connectivity"""
        import aiohttp

        proxy = await self.get_proxy(proxy_id, organization_id)

        # Build proxy URL
        if proxy.username and proxy.password:
            proxy_url = f"{proxy.protocol.value}://{proxy.username}:{proxy.password}@{proxy.ip}:{proxy.port}"
        else:
            proxy_url = f"{proxy.protocol.value}://{proxy.ip}:{proxy.port}"

        try:
            start_time = datetime.now()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://httpbin.org/ip",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    latency = int((datetime.now() - start_time).total_seconds() * 1000)

                    if response.status == 200:
                        # Update proxy status
                        proxy.status = ProxyStatus.ACTIVE
                        proxy.latency = latency
                        proxy.last_tested = datetime.utcnow()
                        await self.db.commit()

                        return {
                            "success": True,
                            "latency": latency,
                        }

        except Exception as e:
            # Update proxy status
            proxy.status = ProxyStatus.DEAD
            proxy.last_tested = datetime.utcnow()
            await self.db.commit()

            return {
                "success": False,
                "error": str(e)
            }
