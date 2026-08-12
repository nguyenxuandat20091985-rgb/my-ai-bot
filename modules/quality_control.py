"""
Quality Control
Scores: FACT, QUALITY, SEO, DUPLICATE, SAFETY
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from .config import MIN_FACT_SCORE, MIN_QUALITY_SCORE, MIN_SEO_SCORE, MIN_SAFETY_SCORE
from .fact_checker import fact_check_content

logger = logging.getLogger(__name__)


def quality_score(content: str, product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heuristic quality score 0-100.
    """
    score = 50.0
    length = len(content)

    if 400 <= length <= 1200:
        score += 20
    elif 200 <= length < 400 or 1200 < length <= 1800:
        score += 10

    # Structure signals
    if "nên mua" in content.lower() or "phù hợp" in content.lower():
        score += 8
    if "lưu ý" in content.lower() or "nhược điểm" in content.lower() or "không nên" in content.lower():
        score += 10
    if "affiliate" in content.lower() or "hoa hồng" in content.lower():
        score += 7
    if product.get("name", "").lower() in content.lower():
        score += 5

    return {
        "score": round(min(score, 100), 1),
        "length": length,
    }


def seo_score(title: str, meta: Dict[str, str], content: str) -> Dict[str, Any]:
    score = 40.0
    if title and 20 <= len(title) <= 70:
        score += 20
    desc = meta.get("meta_description", "")
    if 50 <= len(desc) <= 160:
        score += 20
    if meta.get("keywords"):
        score += 10
    if content.count("\n\n") >= 3:  # has paragraphs
        score += 10
    return {"score": round(min(score, 100), 1)}


def run_quality_gate(
    content: str,
    title: str,
    product: Dict[str, Any],
    meta: Dict[str, str] = None,
    is_duplicate: bool = False,
) -> Dict[str, Any]:
    """
    Full gate.
    Returns detailed report + passed flag.
    """
    meta = meta or {}

    fact = fact_check_content(content, product)
    qual = quality_score(content, product)
    seo = seo_score(title, meta, content)

    safety_score = 100.0
    if is_duplicate:
        safety_score -= 40
    # more safety checks can be added in safety_guard

    report = {
        "fact": fact,
        "quality": qual,
        "seo": seo,
        "duplicate": is_duplicate,
        "safety_score": safety_score,
        "passed": (
            fact["passed"]
            and qual["score"] >= MIN_QUALITY_SCORE
            and seo["score"] >= MIN_SEO_SCORE
            and safety_score >= MIN_SAFETY_SCORE
            and not is_duplicate
        ),
    }
    return report