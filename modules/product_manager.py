"""
Product Manager - Normalize, validate, score, cache.
Backward-compatible with old products.json schema.
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from copy import deepcopy

from .config import PRODUCTS_JSON, PRODUCT_CACHE, SCORING_WEIGHTS, DATA_DIR

logger = logging.getLogger(__name__)

# New canonical schema
CANONICAL_FIELDS = [
    "id", "name", "brand", "category", "price", "old_price", "discount",
    "rating", "review_count", "image_url", "product_url", "affiliate_url",
    "merchant", "commission", "availability", "keywords", "pros", "cons",
    "source", "last_updated", "highlights", "audience", "link"  # keep old fields
]


def _now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=7))).isoformat()


def _generate_id(name: str, link: str = "") -> str:
    raw = f"{name}|{link}".strip().lower()
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def normalize_product(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert any product dict (old or new) → canonical schema.
    NEVER drops old fields. Always backward-compatible.
    """
    p = deepcopy(raw)

    # --- map old fields ---
    name = p.get("name") or p.get("title") or "Unknown Product"
    link = p.get("link") or p.get("product_url") or p.get("url") or ""
    highlights = p.get("highlights") or ""
    audience = p.get("audience") or ""

    # build id if missing
    pid = p.get("id") or _generate_id(name, link)

    # normalize price fields
    price = p.get("price")
    old_price = p.get("old_price")
    discount = p.get("discount")
    if price is not None and old_price is not None and old_price > 0 and discount is None:
        try:
            discount = round((1 - float(price) / float(old_price)) * 100, 1)
        except Exception:
            discount = None

    # keywords from highlights + name
    keywords = p.get("keywords") or []
    if not keywords and highlights:
        keywords = [k.strip() for k in highlights.replace(",", " ").split() if len(k.strip()) > 2][:8]

    # pros/cons
    pros = p.get("pros") or []
    if not pros and highlights:
        pros = [h.strip() for h in highlights.split(",") if h.strip()]

    cons = p.get("cons") or []

    canonical = {
        "id": pid,
        "name": name,
        "brand": p.get("brand") or "",
        "category": p.get("category") or "gia-dung",
        "price": price,
        "old_price": old_price,
        "discount": discount,
        "rating": p.get("rating"),
        "review_count": p.get("review_count"),
        "image_url": p.get("image_url") or p.get("image") or "",
        "product_url": link,
        "affiliate_url": p.get("affiliate_url") or link,  # fallback to product link
        "merchant": p.get("merchant") or "unknown",
        "commission": p.get("commission"),
        "availability": p.get("availability") or "unknown",
        "keywords": keywords,
        "pros": pros,
        "cons": cons,
        "source": p.get("source") or "products.json",
        "last_updated": p.get("last_updated") or _now_iso(),
        # keep original for backward compatibility
        "highlights": highlights,
        "audience": audience,
        "link": link,
    }
    return canonical


def validate_product(p: Dict[str, Any]) -> List[str]:
    """Return list of validation errors. Empty = valid."""
    errors = []
    if not p.get("name"):
        errors.append("missing name")
    if not p.get("link") and not p.get("product_url") and not p.get("affiliate_url"):
        errors.append("missing any URL")
    return errors


def load_products(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load products.json and normalize every item.
    Compatible with both old and new schema.
    """
    path = path or PRODUCTS_JSON
    if not path.exists():
        logger.warning(f"products.json not found at {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_list = data.get("products", data) if isinstance(data, dict) else data
    if not isinstance(raw_list, list):
        logger.error("products.json format invalid")
        return []

    products = []
    for raw in raw_list:
        try:
            p = normalize_product(raw)
            errs = validate_product(p)
            if errs:
                logger.warning(f"Product '{p.get('name')}' validation: {errs}")
            products.append(p)
        except Exception as e:
            logger.error(f"Failed to normalize product: {e}")
    return products


def save_products(products: List[Dict[str, Any]], path: Optional[Path] = None) -> None:
    """Save in old-compatible format + keep new fields."""
    path = path or PRODUCTS_JSON
    # Keep simple structure that old bot.py still understands
    simple = []
    for p in products:
        simple.append({
            "name": p["name"],
            "link": p.get("link") or p.get("affiliate_url") or p.get("product_url"),
            "highlights": p.get("highlights") or ", ".join(p.get("pros", [])),
            "audience": p.get("audience") or "",
            # extra fields (new)
            "id": p.get("id"),
            "price": p.get("price"),
            "old_price": p.get("old_price"),
            "discount": p.get("discount"),
            "rating": p.get("rating"),
            "image_url": p.get("image_url"),
            "affiliate_url": p.get("affiliate_url"),
            "keywords": p.get("keywords"),
            "pros": p.get("pros"),
            "cons": p.get("cons"),
            "category": p.get("category"),
            "last_updated": p.get("last_updated"),
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"products": simple}, f, ensure_ascii=False, indent=2)


def score_product(p: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> float:
    """
    Configurable scoring.
    Returns 0-100.
    """
    w = weights or SCORING_WEIGHTS
    score = 0.0

    # deal (discount)
    discount = p.get("discount") or 0
    try:
        discount = float(discount)
    except Exception:
        discount = 0
    deal_score = min(discount / 50.0, 1.0) * 100  # 50% discount = full
    score += deal_score * w.get("deal", 0.3)

    # rating
    rating = p.get("rating") or 0
    try:
        rating = float(rating)
    except Exception:
        rating = 0
    rating_score = (rating / 5.0) * 100
    score += rating_score * w.get("rating", 0.2)

    # review_count (log scale)
    rc = p.get("review_count") or 0
    try:
        rc = int(rc)
    except Exception:
        rc = 0
    review_score = min(rc / 500.0, 1.0) * 100
    score += review_score * w.get("review_count", 0.15)

    # commission
    comm = p.get("commission") or 0
    try:
        comm = float(comm)
    except Exception:
        comm = 0
    comm_score = min(comm / 15.0, 1.0) * 100  # 15% = full
    score += comm_score * w.get("commission", 0.15)

    # audience_fit (simple heuristic)
    audience = (p.get("audience") or "").lower()
    fit = 50.0
    if any(k in audience for k in ["mẹ", "nội trợ", "bỉm", "gia đình"]):
        fit = 85.0
    score += fit * w.get("audience_fit", 0.1)

    # content_potential
    pros = p.get("pros") or []
    potential = 40.0 + min(len(pros) * 10, 40) + (20 if p.get("image_url") else 0)
    score += min(potential, 100) * w.get("content_potential", 0.1)

    return round(min(score, 100.0), 1)


def select_product_for_today(products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Chọn sản phẩm thông minh:
    1. Ưu tiên sản phẩm chưa đăng trong 3 ngày gần đây
    2. Trong các sản phẩm còn lại → chọn điểm cao nhất
    3. Nếu tất cả đã đăng gần đây → xoay theo ngày (fallback)
    """
    if not products:
        return None

    today = datetime.now(timezone(timedelta(hours=7)))
    recent_ids = set()

    # Đọc lịch sử nếu có
    history_path = DATA_DIR / "content_history.json"
    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            cutoff = (today - timedelta(days=3)).date()
            for item in history if isinstance(history, list) else history.get("items", []):
                try:
                    d = item.get("date") or item.get("created_at") or ""
                    # hỗ trợ cả ISO và YYYY-MM-DD
                    if "T" in str(d):
                        d = d[:10]
                    item_date = datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
                    if item_date >= cutoff:
                        pid = item.get("product_id") or item.get("id")
                        if pid:
                            recent_ids.add(pid)
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Không đọc được content_history: {e}")

    # Ưu tiên sản phẩm chưa đăng gần đây
    candidates = [p for p in products if p.get("id") not in recent_ids]
    if not candidates:
        candidates = products  # fallback: dùng tất cả

    # Chọn điểm cao nhất trong candidates
    scored = [(score_product(p), p) for p in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Nếu nhiều sản phẩm cùng điểm cao → xoay nhẹ theo ngày để đa dạng
    top_score = scored[0][0]
    top_group = [p for s, p in scored if s >= top_score - 5]
    idx = today.toordinal() % len(top_group)
    chosen = top_group[idx]

    logger.info(
        f"Selected: {chosen['name']} | score={score_product(chosen)} | "
        f"avoided_recent={len(recent_ids)} | candidates={len(candidates)}"
    )
    return chosen


def get_top_products(products: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    scored = [(score_product(p), p) for p in products]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:n]]


# Quick self-test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prods = load_products()
    print(f"Loaded {len(prods)} products")
    for p in prods:
        print(f"  - {p['name']} | score={score_product(p)} | id={p['id']}")