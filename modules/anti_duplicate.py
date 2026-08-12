"""
Anti-duplicate system.
Stores content history to avoid repeating same angle/title/hash.
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from .config import CONTENT_HISTORY, DATA_DIR

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=7))).isoformat()


def _load_history() -> List[Dict[str, Any]]:
    if not CONTENT_HISTORY.exists():
        return []
    try:
        with open(CONTENT_HISTORY, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Cannot load content history: {e}")
        return []


def _save_history(history: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    # Keep last 500 entries
    history = history[-500:]
    with open(CONTENT_HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def is_duplicate(
    product_id: str,
    title: str,
    body: str,
    angle: str = "default",
    threshold_days: int = 14,
) -> bool:
    """
    Check if similar content already exists recently.
    """
    history = _load_history()
    h = content_hash(body)
    title_norm = title.strip().lower()

    cutoff = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=threshold_days)

    for entry in history:
        if entry.get("product_id") != product_id:
            continue
        try:
            ts = datetime.fromisoformat(entry["timestamp"])
            if ts < cutoff:
                continue
        except Exception:
            continue

        if entry.get("content_hash") == h:
            return True
        if entry.get("title", "").strip().lower() == title_norm:
            return True
        if entry.get("angle") == angle and entry.get("product_id") == product_id:
            # same product + same angle within window
            return True
    return False


def record_content(
    product_id: str,
    title: str,
    body: str,
    angle: str = "default",
    content_type: str = "long_review",
    extra: Optional[Dict] = None,
) -> None:
    history = _load_history()
    entry = {
        "product_id": product_id,
        "title": title,
        "content_hash": content_hash(body),
        "angle": angle,
        "content_type": content_type,
        "timestamp": _now(),
        "extra": extra or {},
    }
    history.append(entry)
    _save_history(history)
    logger.info(f"Recorded content: {title[:50]}...")


def get_used_angles(product_id: str) -> List[str]:
    history = _load_history()
    return list({e["angle"] for e in history if e.get("product_id") == product_id})