"""
AccessTrade Adapter – Official API
Endpoint: POST /v1/product_link/create
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

import requests

from .config import (
    ACCESSTRADE_API_TOKEN,
    ACCESSTRADE_CAMPAIGN_ID,
    ACCESSTRADE_BASE_URL,
    ENABLE_ACCESSTRADE,
)

logger = logging.getLogger(__name__)


class AccessTradeClient:
    def __init__(self):
        self.token = ACCESSTRADE_API_TOKEN
        self.campaign_id = ACCESSTRADE_CAMPAIGN_ID
        self.base_url = ACCESSTRADE_BASE_URL.rstrip("/")
        self.enabled = ENABLE_ACCESSTRADE

    def is_ready(self) -> bool:
        return bool(self.enabled and self.token and self.campaign_id)

    def create_deep_link(
        self,
        product_url: str,
        campaign_id: str = None,
        utm_source: str = "blog",
        utm_medium: str = "affiliate",
        utm_campaign: str = "goc-bep-thong-minh",
    ) -> Optional[str]:
        """
        Tạo affiliate link từ URL sản phẩm (Shopee...).
        Ưu tiên trả về short_link, nếu không có thì aff_link.
        """
        if not self.is_ready():
            logger.info("AccessTrade chưa cấu hình → giữ link gốc")
            return None

        if not product_url or not product_url.startswith("http"):
            logger.warning(f"URL không hợp lệ: {product_url}")
            return None

        cid = campaign_id or self.campaign_id
        api_url = f"{self.base_url}/v1/product_link/create"

        headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "campaign_id": str(cid),
            "urls": [product_url],
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign,
            "url_enc": True,
        }

        try:
            resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
            logger.info(f"AccessTrade status={resp.status_code}")

            if resp.status_code != 200:
                logger.error(f"AccessTrade error: {resp.text[:300]}")
                return None

            data = resp.json()
            if not data.get("success"):
                logger.error(f"AccessTrade success=false: {data}")
                return None

            success_links = data.get("data", {}).get("success_link") or []
            if not success_links:
                logger.warning("AccessTrade không trả về success_link")
                return None

            item = success_links[0]
            # Ưu tiên short_link
            link = item.get("short_link") or item.get("aff_link")
            if link:
                logger.info(f"Affiliate link OK: {link}")
                return link

            return None

        except requests.Timeout:
            logger.error("AccessTrade timeout")
            return None
        except Exception as e:
            logger.error(f"AccessTrade exception: {e}")
            return None

    def get_product_feed(self, category: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        # Chưa dùng – giữ placeholder an toàn
        return []

    def get_campaigns(self) -> List[Dict[str, Any]]:
        return []


# Singleton
client = AccessTradeClient()


def get_affiliate_link(product_url: str) -> str:
    """
    Trả về affiliate link nếu tạo được, không thì giữ link gốc.
    Không bao giờ bịa tracking param.
    """
    if not product_url:
        return product_url or "#"
    deep = client.create_deep_link(product_url)
    return deep or product_url