"""
Proxies module
"""

from app.modules.proxies.router import router
from app.modules.proxies.service import ProxyService
from app.modules.proxies.schemas import (
    ProxyCreate,
    ProxyResponse,
    ProxyUpdate,
    ProxyTestResult,
)

__all__ = [
    "router",
    "ProxyService",
    "ProxyCreate",
    "ProxyResponse",
    "ProxyUpdate",
    "ProxyTestResult",
]
