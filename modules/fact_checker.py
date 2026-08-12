"""
Fact Checker
Classify every claim: FACT | OPINION | INFERENCE | UNKNOWN
AI must not invent price, rating, discount, warranty, etc.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# Patterns that look like hard facts
FACT_PATTERNS = [
    r"\d+%",                          # percentage
    r"\d+[\.,]\d+\s*(đ|vnđ|vnd|k|tr)", # price
    r"giảm\s+\d+",
    r"giá\s+\d+",
    r"đánh giá\s+\d",
    r"sao\s+\d",
    r"bảo hành\s+\d+",
    r"miễn phí",
    r"freeship",
    r"voucher",
    r"mã giảm",
]

OPINION_MARKERS = [
    "tôi nghĩ", "theo tôi", "có lẽ", "dường như", "có vẻ",
    "nên mua", "đáng mua", "tuyệt vời", "rất tốt", "yêu thích",
]


def classify_sentence(text: str, known_facts: Dict[str, Any]) -> str:
    """
    Very lightweight heuristic classifier.
    Returns: FACT | OPINION | INFERENCE | UNKNOWN
    """
    t = text.lower().strip()
    if not t:
        return "UNKNOWN"

    # Check against known product data
    for key, val in known_facts.items():
        if val is None:
            continue
        val_str = str(val).lower()
        if val_str and val_str in t:
            return "FACT"

    # Opinion markers
    for m in OPINION_MARKERS:
        if m in t:
            return "OPINION"

    # Hard number claims without support → UNKNOWN
    for pat in FACT_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            # If we reach here, the number is not in known_facts
            return "UNKNOWN"

    # Default soft inference
    return "INFERENCE"


def extract_claims(content: str) -> List[str]:
    """Split content into sentences for checking."""
    # Simple Vietnamese sentence splitter
    parts = re.split(r"(?<=[\.\!\?\n])\s+", content)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def fact_check_content(content: str, product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry.
    Returns:
    {
        "score": 0-100,
        "claims": [{"text":..., "label":..., "ok": bool}],
        "unsupported": [...],
        "passed": bool
    }
    """
    known = {
        "name": product.get("name"),
        "price": product.get("price"),
        "old_price": product.get("old_price"),
        "discount": product.get("discount"),
        "rating": product.get("rating"),
        "review_count": product.get("review_count"),
        "highlights": product.get("highlights"),
        "pros": " ".join(product.get("pros") or []),
        "audience": product.get("audience"),
    }

    claims = extract_claims(content)
    results = []
    unsupported = []

    for c in claims:
        label = classify_sentence(c, known)
        ok = label in ("FACT", "OPINION", "INFERENCE")
        if label == "UNKNOWN":
            unsupported.append(c)
            ok = False
        results.append({"text": c[:120], "label": label, "ok": ok})

    total = len(results) or 1
    ok_count = sum(1 for r in results if r["ok"])
    score = round(ok_count / total * 100, 1)

    passed = score >= 70 and len(unsupported) <= 2

    return {
        "score": score,
        "claims": results,
        "unsupported": unsupported,
        "passed": passed,
        "total_claims": total,
        "ok_claims": ok_count,
    }


def sanitize_content(content: str, product: Dict[str, Any]) -> str:
    """
    Soft sanitize: remove obvious unsupported numeric claims.
    Prefer keeping content intact; only strip clearly dangerous parts.
    """
    # For V1 we only warn, do not aggressively rewrite.
    # Full rewrite can be added later with AI.
    return content