"""
Product Fetcher – Lấy SP từ AccessTrade datafeed (Shopee).
Flag: ENABLE_PRODUCT_FETCH=true mới chạy.
Không xóa products.json cũ – chỉ merge thêm.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List

import requests

from .config import ACCESSTRADE_API_TOKEN
from .product_manager import load_products, save_products, normalize_product, score_product

logger = logging.getLogger(__name__)

ENABLE_PRODUCT_FETCH = os.getenv("ENABLE_PRODUCT_FETCH", "false").lower() in (
    "1", "true", "yes", "on"
)
DATAFEED_URL = "https://api.accesstrade.vn/v1/datafeeds"
DEFAULT_CATS = ["thiet-bi-gia-dung", "nha-cua-doi-song"]
MAX_NEW = int(os.getenv("FETCH_MAX_NEW", "15"))
REQUEST_TIMEOUT = 30


def _headers() -> Dict[str, str]:
    token = (ACCESSTRADE_API_TOKEN or "").strip()
    return {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def fetch_datafeed(
    domain: str = "shopee.vn",
    cat: str = "thiet-bi-gia-dung",
    limit: int = 50,
) -> List[Dict]:
    if not ACCESSTRADE_API_TOKEN:
        logger.warning("Thiếu ACCESSTRADE_API_TOKEN – bỏ qua fetch")
        return []
    try:
        r = requests.get(
            DATAFEED_URL,
            headers=_headers(),
            params={"domain": domain, "cat": cat, "limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            logger.error(f"Datafeed HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("data") or data.get("products") or data.get("items") or []
        else:
            items = []
        if not isinstance(items, list):
            items = []
        logger.info(f"Datafeed {domain}/{cat}: {len(items)} items")
        return items
    except Exception as e:
        logger.error(f"Fetch datafeed lỗi: {e}")
        return []


def _to_product(raw: Dict[str, Any]) -> Dict[str, Any]:
    name = (raw.get("name") or raw.get("product_name") or "Sản phẩm")[:120]
    url = raw.get("url") or raw.get("product_url") or raw.get("link") or ""
    aff = raw.get("aff_link") or raw.get("affiliate_url") or url
    image = raw.get("image") or raw.get("image_url") or ""

    price = raw.get("discount") or raw.get("price")
    old_price = raw.get("price") if raw.get("discount") else None

    pid = raw.get("product_id") or raw.get("sku") or re.sub(r"\W+", "-", name.lower())[:20]

    desc = raw.get("desc") or raw.get("description") or ""
    highlights = str(desc)[:200] if desc else name

    return normalize_product({
        "id": str(pid)[:24],
        "name": name,
        "link": aff or url,
        "product_url": url,
        "affiliate_url": aff or url,
        "price": price,
        "old_price": old_price,
        "image_url": image,
        "highlights": highlights,
        "audience": "người dùng Shopee quan tâm deal gia dụng",
        "category": raw.get("cate") or raw.get("category") or "gia-dung",
        "merchant": "shopee",
        "source": "accesstrade_datafeed",
    })


def merge_new_products(new_items: List[Dict], existing: List[Dict]) -> List[Dict]:
    existing_links = {(p.get("link") or "").rstrip("/").lower() for p in existing}
    existing_names = {(p.get("name") or "").strip().lower() for p in existing}
    merged = list(existing)
    added = 0

    for raw in new_items:
        if not isinstance(raw, dict):
            continue
        try:
            p = _to_product(raw)
        except Exception as e:
            logger.warning(f"Skip raw product: {e}")
            continue

        link = (p.get("link") or "").rstrip("/").lower()
        name = (p.get("name") or "").strip().lower()
        if not link or not name:
            continue
        if link in existing_links or name in existing_names:
            continue

        merged.append(p)
        existing_links.add(link)
        existing_names.add(name)
        added += 1
        if added >= MAX_NEW:
            break

    logger.info(f"Merge: +{added} sản phẩm mới (tổng {len(merged)})")
    return merged


def run_fetch_and_merge() -> int:
    """Trả về số SP sau merge. Chỉ chạy khi ENABLE_PRODUCT_FETCH=true."""
    if not ENABLE_PRODUCT_FETCH:
        logger.info("ENABLE_PRODUCT_FETCH=false – skip fetch")
        return 0

    existing = load_products()
    all_new: List[Dict] = []
    for cat in DEFAULT_CATS:
        all_new.extend(fetch_datafeed(cat=cat, limit=40))

    if not all_new:
        logger.warning("Datafeed không trả về sản phẩm nào")
        return len(existing)

    merged = merge_new_products(all_new, existing)
    save_products(merged)
    return len(merged)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    os.environ["ENABLE_PRODUCT_FETCH"] = "true"
    n = run_fetch_and_merge()
    print(f"Total products: {n}")