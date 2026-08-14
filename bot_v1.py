"""
MY AI AFFILIATE AGENT V1.0 - Orchestrator
"""

from __future__ import annotations

import os
import sys
import json
import logging
import time  # ✅ A. Đã thêm import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from modules.config import (
    SAFE_MODE, AUTO_PUBLISH, BLOG_URL, DOCS_DIR, MODEL, DATA_DIR
)
from modules.product_manager import (
    load_products, select_product_for_today, score_product
)
from modules.content_engine import (
    generate_long_review, generate_social_posts, generate_seo_meta
)
from modules.anti_duplicate import is_duplicate, record_content
from modules.quality_control import run_quality_gate
from modules.safety_guard import safety_check
from modules.seo_engine import render_html_page, update_index
from modules.accesstrade import get_affiliate_link
from modules.analytics import record_publish, summary

from litellm import completion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DOCS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ✅ B. Đã thay toàn bộ hàm original_ai
def original_ai(prompt: str, max_retries: int = 3) -> str:
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = completion(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if "ratelimit" in err_str or "rate_limit" in err_str or "tokens per minute" in err_str:
                wait = 25 * attempt
                logger.warning(f"Core rate limit – đợi {wait}s ({attempt}/{max_retries})")
                time.sleep(wait)
                continue
            raise
    raise last_err


def write_social_outputs(
    product: dict,
    title: str,
    slug: str,
    social_raw: str,
    mode: str = "v1",
) -> None:
    """Ghi result.txt (dễ copy Fanpage) + social.json (cho Make.com)."""
    aff = product.get("affiliate_url") or product.get("link") or ""
    blog_link = f"{BLOG_URL}/bai-{slug}.html"
    date_str = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y")

    # Tách 3 bài social
    parts = [p.strip() for p in social_raw.split("---") if p.strip()]

    # ----- result.txt -----
    lines = [
        f"📰 BÀI MỚI ({mode.upper()}) – {date_str}",
        f"Sản phẩm: {product.get('name')}",
        f"Link website: {blog_link}",
        f"Link affiliate: {aff}",
        "",
        "👇 3 BÀI NGẮN – COPY ĐĂNG FANPAGE:",
        "",
    ]
    for i, part in enumerate(parts[:3], 1):
        lines.append(f"===== BÀI {i} =====")
        lines.append(part)
        lines.append("")
    lines.append("===== HASHTAG GỢI Ý =====")
    lines.append("#GocBepThongMinh #SanDeal #DoGiaDung #ReviewThatLong #Shopee")
    lines.append("")

    with open("result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ----- social.json (Make.com / Zapier dễ đọc) -----
    social_data = {
        "date": date_str,
        "product_name": product.get("name"),
        "product_id": product.get("id"),
        "blog_url": blog_link,
        "affiliate_url": aff,
        "title": title,
        "posts": parts[:3],
        "hashtags": ["#GocBepThongMinh", "#SanDeal", "#DoGiaDung", "#ReviewThatLong", "#Shopee"],
    }
    with open(DATA_DIR / "social.json", "w", encoding="utf-8") as f:
        json.dump(social_data, f, ensure_ascii=False, indent=2)
    # copy ra docs để GitHub Pages cũng có (nếu cần)
    with open(DOCS_DIR / "social.json", "w", encoding="utf-8") as f:
        json.dump(social_data, f, ensure_ascii=False, indent=2)

    logger.info("Social outputs saved → result.txt + data/social.json")


def run_original_core_flow(product: dict, today, date_str: str, slug: str) -> None:
    logger.info(">>> Running ORIGINAL CORE flow (fallback)")

    raw = original_ai(
        "Bạn là cây viết review đồ gia dụng nổi tiếng Việt Nam, văn phong thật thà, gần gũi.\n"
        f"Hãy viết bài review khoảng 500 từ về: {product['name']}.\n"
        f"Điểm mạnh: {product.get('highlights', '')}\n"
        f"Người đọc: {product.get('audience', '')}\n"
        "Yêu cầu: dòng ĐẦU TIÊN là tiêu đề giật gân (không kèm # hay *), "
        "các dòng sau là nội dung, mỗi đoạn cách nhau một dòng trống. "
        "Cuối bài nhắc người đọc bấm link ưu đãi."
    )
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    title = lines[0].lstrip("#* ")
    body = "".join(f"<p>{l}</p>" for l in lines[1:])

    aff = product.get("affiliate_url") or product.get("link") or "#"
    meta = {"seo_title": title, "meta_description": f"Review {product['name']}", "keywords": product["name"]}
    html = render_html_page(title, body, product, meta, date_str, slug)

    for target in [DOCS_DIR / f"bai-{slug}.html", Path(f"bai-{slug}.html")]:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(html)

    posts = sorted([p.name for p in DOCS_DIR.glob("bai-*.html")], reverse=True)
    update_index(posts, DOCS_DIR / "index.html")
    update_index(posts, Path("index.html"))

    social = original_ai(
        f"Dựa trên sản phẩm {product['name']} (điểm mạnh: {product.get('highlights', '')}), "
        f"viết 3 bài đăng mạng xã hội tiếng Việt ngắn dưới 8 câu, có emoji, "
        f"mỗi bài kèm link {aff}. Phân cách bằng đúng một dòng ---"
    )
    write_social_outputs(product, title, slug, social, mode="core")
    record_publish(product.get("id", ""), product["name"], slug, title, mode="core")
    logger.info("Core published")


def run_extended_pipeline(product: dict, today, date_str: str, slug: str) -> bool:
    logger.info(">>> Running EXTENDED V1.0 pipeline")

    product["affiliate_url"] = get_affiliate_link(
        product.get("product_url") or product.get("link") or ""
    )

    review = generate_long_review(product)
    title = review["title"]
    body = review["body"]

    if is_duplicate(product["id"], title, body, angle="daily_review"):
        logger.warning("Duplicate detected → block extended publish")
        return False

    meta = generate_seo_meta(product, title)
    gate = run_quality_gate(body, title, product, meta, is_duplicate=False)
    safety = safety_check(body, product)

    logger.info(
        f"Quality: fact={gate['fact'].get('score')} quality={gate['quality']['score']} seo={gate['seo']['score']}"
    )
    logger.info(f"Safety: passed={safety['passed']} score={safety.get('score')}")

    if SAFE_MODE and (not gate["passed"] or not safety["passed"]):
        logger.warning("SAFE_MODE: content failed quality/safety → fallback Core")
        return False

    body_html = "".join(f"<p>{p}</p>" for p in body.split("\n\n") if p.strip())
    html = render_html_page(title, body_html, product, meta, date_str, slug)

    for target in [DOCS_DIR / f"bai-{slug}.html", Path(f"bai-{slug}.html")]:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(html)

    posts = sorted([p.name for p in DOCS_DIR.glob("bai-*.html")], reverse=True)
    update_index(posts, DOCS_DIR / "index.html")
    update_index(posts, Path("index.html"))

    social = generate_social_posts(product)
    write_social_outputs(product, title, slug, social, mode="v1")

    record_content(
        product_id=product["id"],
        title=title,
        body=body,
        angle="daily_review",
        content_type="long_review",
        extra={"slug": slug, "score": score_product(product)},
    )
    record_publish(product["id"], product["name"], slug, title, mode="extended")

    logger.info("✅ Extended pipeline published successfully")
    return True


def main():
    today = datetime.now(timezone(timedelta(hours=7)))
    date_str = today.strftime("%d/%m/%Y")
    slug = today.strftime("%Y-%m-%d")

    products = load_products()
    if not products:
        logger.error("No products found in products.json")
        sys.exit(1)

    product = select_product_for_today(products)
    logger.info(f"Today product: {product['name']} | score={score_product(product)}")

    success = False
    try:
        success = run_extended_pipeline(product, today, date_str, slug)
    except Exception as e:
        logger.error(f"Extended pipeline error: {e}")
        success = False

    if not success:
        run_original_core_flow(product, today, date_str, slug)

    # In tóm tắt analytics
    s = summary()
    logger.info(f"Analytics: total_posts={s['total_posts']} | by_product={s['by_product']}")
    logger.info("🎉 Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)