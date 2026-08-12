"""
Unit tests – no real API calls.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.product_manager import (
    normalize_product, validate_product, score_product, _generate_id
)


def test_normalize_old_schema():
    raw = {
        "name": "Nồi chiên không dầu",
        "link": "https://shorten.asia/epmrd8Bx",
        "highlights": "chiên nướng không cần dầu, bớt 80% mỡ",
        "audience": "các mẹ nội trợ"
    }
    p = normalize_product(raw)
    assert p["name"] == "Nồi chiên không dầu"
    assert p["link"] == "https://shorten.asia/epmrd8Bx"
    assert p["affiliate_url"] == "https://shorten.asia/epmrd8Bx"
    assert p["id"]
    assert "pros" in p
    assert validate_product(p) == []


def test_score_range():
    p = normalize_product({
        "name": "Test",
        "link": "https://example.com",
        "highlights": "a, b, c",
        "audience": "mẹ bỉm sữa",
        "discount": 40,
        "rating": 4.5,
        "review_count": 200,
        "commission": 8
    })
    s = score_product(p)
    assert 0 <= s <= 100


def test_id_stable():
    id1 = _generate_id("Nồi A", "https://x.com/1")
    id2 = _generate_id("Nồi A", "https://x.com/1")
    assert id1 == id2


if __name__ == "__main__":
    test_normalize_old_schema()
    test_score_range()
    test_id_stable()
    print("All product_manager tests passed")