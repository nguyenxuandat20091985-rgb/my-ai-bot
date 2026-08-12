"""
Safety Guard
Block: fake review, fake discount, misleading claim, spam, invalid affiliate.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Any, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

FORBIDDEN_PHRASES = [
    r"tôi đã dùng",
    r"tôi đã trải nghiệm",
    r"sau khi dùng",
    r"review thật 100%",
    r"cam kết hoàn tiền",
    r"chỉ còn \d+ suất",
    r"sắp hết hàng",
    r"giá sốc nhất",
    r"rẻ nhất thị trường",
    r"độc quyền",
]


def check_forbidden_phrases(content: str) -> List[str]:
    found = []
    for pat in FORBIDDEN_PHRASES:
        if re.search(pat, content, re.IGNORECASE):
            found.append(pat)
    return found


def validate_affiliate_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        return True
    except Exception:
        return False


def safety_check(content: str, product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
    {
        "passed": bool,
        "score": 0-100,
        "issues": [...],
        "blocked_reasons": [...]
    }
    """
    issues = []
    blocked = []

    # 1. Forbidden phrases
    forbidden = check_forbidden_phrases(content)
    if forbidden:
        issues.append(f"forbidden_phrases: {forbidden}")
        blocked.append("possible_fake_personal_experience_or_scarcity")

    # 2. Affiliate link
    aff = product.get("affiliate_url") or product.get("link") or ""
    if not validate_affiliate_url(aff):
        issues.append("invalid_or_missing_affiliate_url")
        blocked.append("invalid_affiliate_link")

    # 3. Empty or too short
    if len(content.strip()) < 150:
        issues.append("content_too_short")
        blocked.append("low_quality")

    score = 100 - len(issues) * 25
    score = max(0, score)

    passed = len(blocked) == 0 and score >= 70

    return {
        "passed": passed,
        "score": score,
        "issues": issues,
        "blocked_reasons": blocked,
    }