"""
Analytics đơn giản – ghi nhận mỗi lần publish.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List

from .config import DATA_DIR

logger = logging.getLogger(__name__)
ANALYTICS_FILE = DATA_DIR / "analytics.json"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=7))).isoformat()


def _load() -> List[Dict[str, Any]]:
    if not ANALYTICS_FILE.exists():
        return []
    try:
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(data: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data[-365:], f, ensure_ascii=False, indent=2)  # giữ 1 năm


def record_publish(
    product_id: str,
    product_name: str,
    slug: str,
    title: str,
    mode: str = "extended",
) -> None:
    data = _load()
    data.append({
        "timestamp": _now(),
        "product_id": product_id,
        "product_name": product_name,
        "slug": slug,
        "title": title,
        "mode": mode,
    })
    _save(data)
    logger.info(f"Analytics recorded: {product_name} ({slug})")


def summary() -> Dict[str, Any]:
    data = _load()
    by_product: Dict[str, int] = {}
    for item in data:
        name = item.get("product_name") or "unknown"
        by_product[name] = by_product.get(name, 0) + 1
    return {
        "total_posts": len(data),
        "by_product": by_product,
        "last_post": data[-1] if data else None,
    }