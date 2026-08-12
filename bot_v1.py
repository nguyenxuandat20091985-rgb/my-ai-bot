"""
MY AI AFFILIATE AGENT V1.0 - Orchestrator
=========================================
This file is an EXTENSION of the original bot.py.

PRINCIPLE:
- Keep original Core flow 100% intact as fallback.
- New pipeline runs only when modules are available and SAFE_MODE rules pass.
- Never delete or break the original daily review logic.

Usage:
  python bot_v1.py          # runs extended pipeline
  (or replace bot.py later after testing)
"""

from __future__ import annotations

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from modules.config import (
    SAFE_MODE, AUTO_PUBLISH, BLOG_URL, DOCS_DIR, MODEL
)
from modules.product_manager import (
    load_products, select_product_for_today, score_product, normalize_product
)
from modules.content_engine import (
    generate_long_review, generate_social_posts, generate_seo_meta
)
from modules.fact_checker import fact_check_content
from modules.anti_duplicate import is_duplicate, record_content
from modules.quality_control import run_quality_gate
from modules.safety_guard import safety_check
from modules.seo_engine import render_html_page, update_index
from modules.accesstrade import get_affiliate_link

# Original CSS + helpers kept for fallback
from litellm import completion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def original_ai(prompt: str) -> str:
    """Exact same AI call as original Core bot.py"""
    resp = completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return resp.choices[0].message.content


def run_original_core_flow(product: dict, today, date_str: str, slug: str) -> None:
    """
    100% original logic from bot.py (kept intact).
    Used as fallback or when SAFE_MODE blocks new pipeline.
    """
    logger.info(">>> Running ORIGINAL CORE flow (fallback / safe)")

    raw = original_ai(
        "Bạn là cây viết review đồ gia dụng nổi tiếng Việt Nam, văn phong thật thà, gần gũi, hài hước nhẹ.\n"
        f"Hãy viết bài review khoảng 500 từ về: {product['name']}.\n"
        f"Điểm mạnh: {product.get('highlights', '')}\n"
        f"Người đọc: {product.get('audience', '')}\n"
        "Yêu cầu: dòng ĐẦU TIÊN là tiêu đề giật gân (không kèm ký tự # hay *), các dòng sau là nội dung, "
        "mỗi đoạn cách nhau một dòng trống. Cuối bài nhắc người đọc bấm link ưu đãi."
    )
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    title = lines[0].lstrip("#* ")
    body = "".join(f"<p>{l}</p>" for l in lines[1:])

    CSS = """
body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f7f7fb;color:#222}
header{background:linear-gradient(90deg,#4f46e5,#ec4899);color:#fff;padding:16px;text-align:center}
.wrap{max-width:720px;margin:12px auto;padding:16px;background:#fff;border-radius:12px;line-height:1.7}
h1{font-size:1.5rem;line-height:1.3}
a.buy{display:block;text-align:center;background:#e11d48;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:bold;margin:20px 0}
.small{color:#888;font-size:0.85rem}
li{margin:6px 0}
"""
    inner = f"<h1>{title}</h1><p class='small'>📅 {date_str}</p>{body}"
    inner += f"<a class='buy' href='{product.get('link') or product.get('affiliate_url')}' target='_blank'>👉 BẤM XEM GIÁ ƯU ĐÃI HÔM NAY</a>"
    inner += "<p class='small'>Bài viết do trợ lý AI biên soạn tự động.</p>"

    html = f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title><style>{CSS}</style></head>
<body>
<header><b>GÓC BẾP THÔNG MINH – SĂN DEAL</b><br><span class="small">Review thật lòng mỗi ngày</span></header>
<div class="wrap">{inner}</div>
</body></html>"""

    # Write both root (legacy) and docs/ (correct Pages path)
    for target in [Path(f"bai-{slug}.html"), DOCS_DIR / f"bai-{slug}.html"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(html)
    logger.info(f"Original Core published: bai-{slug}.html")

    # Social
    social = original_ai(
        f"Dựa trên sản phẩm {product['name']} (điểm mạnh: {product.get('highlights', '')}), "
        f"viết 3 bài đăng mạng xã hội tiếng Việt ngắn dưới 8 câu, có emoji vui, "
        f"và mỗi bài kèm link {product.get('link') or product.get('affiliate_url')} . "
        "Phân cách các bài bằng đúng một dòng chứa ---"
    )
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(f"📰 BÀI MỚI TRÊN BÁO CỦA ANH:\n{BLOG_URL}/bai-{slug}.html\n\n")
        f.write("👇 3 BÀI NGẮN COPY ĐI GIEO LINK:\n\n")
        f.write(social)
    logger.info("Original Core social saved to result.txt")


def run_extended_pipeline(product: dict, today, date_str: str, slug: str) -> bool:
    """
    New V1.0 pipeline.
    Returns True if published successfully, False if blocked → caller falls back to Core.
    """
    logger.info(">>> Running EXTENDED V1.0 pipeline")

    # 1. Affiliate link (safe)
    product["affiliate_url"] = get_affiliate_link(
        product.get("product_url") or product.get("link") or ""
    )

    # 2. Generate content
    review = generate_long_review(product)
    title = review["title"]
    body = review["body"]

    # 3. Anti-duplicate
    if is_duplicate(product["id"], title, body, angle="daily_review"):
        logger.warning("Duplicate detected → block publish")
        return False

    # 4. SEO meta
    meta = generate_seo_meta(product, title)

    # 5. Quality + Fact + Safety gate
    gate = run_quality_gate(body, title, product, meta, is_duplicate=False)
    safety = safety_check(body, product)

    logger.info(f"Quality gate: fact={gate['fact']['score']} quality={gate['quality']['score']} seo={gate['seo']['score']}")
    logger.info(f"Safety: passed={safety['passed']} score={safety['score']}")

    if SAFE_MODE:
        if not gate["passed"] or not safety["passed"]:
            logger.warning("SAFE_MODE: content did not pass gates → fallback to Core")
            return False

    if not AUTO_PUBLISH and SAFE_MODE:
        # In strict safe mode we still require explicit auto flag
        logger.info("AUTO_PUBLISH=false → skip extended publish, use Core")
        return False

    # 6. Render HTML
    body_html = "".join(f"<p>{p}</p>" for p in body.split("\n\n") if p.strip())
    html = render_html_page(title, body_html, product, meta, date_str, slug)

    # 7. Write to both locations (compatibility)
    for target in [Path(f"bai-{slug}.html"), DOCS_DIR / f"bai-{slug}.html"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(html)

    # 8. Update index in docs/
    posts = sorted(
        [p.name for p in DOCS_DIR.glob("bai-*.html")],
        reverse=True
    )
    update_index(posts, DOCS_DIR / "index.html")
    # also legacy root index
    update_index(posts, Path("index.html"))

    # 9. Social
    social = generate_social_posts(product)
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(f"📰 BÀI MỚI (V1.0):\n{BLOG_URL}/bai-{slug}.html\n\n")
        f.write("👇 3 BÀI NGẮN:\n\n")
        f.write(social)

    # 10. Record history
    record_content(
        product_id=product["id"],
        title=title,
        body=body,
        angle="daily_review",
        content_type="long_review",
        extra={"slug": slug, "score": score_product(product)},
    )

    logger.info("Extended pipeline published successfully")
    return True


def main():
    today = datetime.now(timezone(timedelta(hours=7)))
    date_str = today.strftime("%d/%m/%Y")
    slug = today.strftime("%Y-%m-%d")

    products = load_products()
    if not products:
        logger.error("No products found")
        sys.exit(1)

    product = select_product_for_today(products)
    logger.info(f"Today product: {product['name']} | score={score_product(product)}")

    # Try extended first
    success = False
    try:
        success = run_extended_pipeline(product, today, date_str, slug)
    except Exception as e:
        logger.error(f"Extended pipeline error: {e}")
        success = False

    if not success:
        # Always fall back to original Core – never break daily publish
        run_original_core_flow(product, today, date_str, slug)

    logger.info("🎉 Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)