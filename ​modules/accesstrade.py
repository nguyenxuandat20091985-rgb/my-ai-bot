"""
AccessTrade Adapter
============================================
REQUIRES OFFICIAL ACCESSTRADE API DOCUMENTATION

This module is intentionally a SAFE INTERFACE.
It does NOT invent endpoints.
It does NOT scrape illegally.
It does NOT bypass authentication.

When you have official docs + credentials:
1. Fill ACCESSTRADE_API_KEY / TOKEN / PUBLISHER_ID in secrets
2. Implement the real methods below
3. Set ENABLE_ACCESSTRADE = True via config

Until then: all methods return empty / None / graceful fallback.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from .config import (
    ACCESSTRADE_API_KEY,
    ACCESSTRADE_API_TOKEN,
    ACCESSTRADE_PUBLISHER_ID,
    ACCESSTRADE_BASE_URL,
    ENABLE_ACCESSTRADE,
)

logger = logging.getLogger(__name__)


class AccessTradeClient:
    """
    Official-API-only client skeleton.
    """

    def __init__(self):
        self.api_key = ACCESSTRADE_API_KEY
        self.token = ACCESSTRADE_API_TOKEN
        self.publisher_id = ACCESSTRADE_PUBLISHER_ID
        self.base_url = ACCESSTRADE_BASE_URL
        self.enabled = ENABLE_ACCESSTRADE

    def is_ready(self) -> bool:
        return bool(self.enabled and self.api_key and self.token and self.publisher_id)

    def get_product_feed(self, category: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        TODO: Implement with official Product Feed endpoint.
        REQUIRES OFFICIAL ACCESSTRADE API DOCUMENTATION
        """
        if not self.is_ready():
            logger.info("AccessTrade not configured → returning empty feed")
            return []
        # Placeholder – do not invent endpoint
        logger.warning("AccessTrade get_product_feed not implemented yet (need official docs)")
        return []

    def create_deep_link(self, product_url: str, campaign_id: str = None) -> Optional[str]:
        """
        TODO: Official deep-link / tracking link API.
        Until implemented → return None (caller keeps original URL).
        """
        if not self.is_ready():
            return None
        logger.warning("AccessTrade create_deep_link not implemented yet (need official docs)")
        return None

    def get_campaigns(self) -> List[Dict[str, Any]]:
        if not self.is_ready():
            return []
        logger.warning("AccessTrade get_campaigns not implemented yet")
        return []


# Convenience singleton
client = AccessTradeClient()


def get_affiliate_link(product_url: str) -> str:
    """
    Safe helper.
    Returns deep link if available, otherwise original product_url.
    Never fabricates tracking parameters.
    """
    deep = client.create_deep_link(product_url)
    return deep or product_url