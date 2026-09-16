"""
MY AI AFFILIATE AGENT V1.0 - Orchestrator
"""

from __future__ import annotations

import os
import sys
import json
import logging
import time
import re
import html as html_lib
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

WEEKDAYS_VI = [
    "THỨ HAI", "THỨ BA", "THỨ TƯ", "THỨ NĂM", "THỨ SÁU", "THỨ BẢY", "CHỦ NHẬT"
]
MONTHS_VI = [
    "", "THÁNG 1", "THÁNG 2", "THÁNG 3", "THÁNG 4", "THÁNG 5", "THÁNG 6",
    "THÁNG 7", "THÁNG 8", "THÁNG 9", "THÁNG 10", "THÁNG 11", "THÁNG 12",
]


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
    """Ghi result.txt + social.json (luôn đồng bộ)."""
    aff = product.get("affiliate_url") or product.get("link") or ""
    blog_link = f"{BLOG_URL}/bai-{slug}.html"
    date_str = datetime.now(timezone(timedelta(hours=7))).strftime("%d/%m/%Y")

    parts = [p.strip() for p in social_raw.split("---") if p.strip()]
    if len(parts) <= 1 and "=====" in social_raw:
        parts = [
            p.strip()
            for p in re.split(r"===== BÀI \d+ =====", social_raw)
            if p.strip() and "HASHTAG" not in p
        ]

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

    social_data = {
        "date": date_str,
        "product_name": product.get("name"),
        "product_id": product.get("id"),
        "blog_url": blog_link,
        "affiliate_url": aff,
        "title": title,
        "posts": parts[:3],
        "hashtags": [
            "#GocBepThongMinh",
            "#SanDeal",
            "#DoGiaDung",
            "#ReviewThatLong",
            "#Shopee",
        ],
    }
    with open(DATA_DIR / "social.json", "w", encoding="utf-8") as f:
        json.dump(social_data, f, ensure_ascii=False, indent=2)
    with open(DOCS_DIR / "social.json", "w", encoding="utf-8") as f:
        json.dump(social_data, f, ensure_ascii=False, indent=2)

    logger.info("Social outputs saved → result.txt + data/social.json + docs/social.json")


def render_newspaper_home(
    product: dict,
    title: str,
    body: str,
    date_str: str,
    slug: str,
    today: datetime,
) -> None:
    """Cập nhật trang chủ Tờ Báo AI với bài review hôm nay."""
    name = html_lib.escape(product.get("name") or "Sản phẩm")
    aff = html_lib.escape(
        product.get("affiliate_url") or product.get("link") or "#", quote=True
    )
    img = html_lib.escape(product.get("image_url") or "", quote=True)
    highlights = html_lib.escape(product.get("highlights") or "")
    audience = html_lib.escape(product.get("audience") or "gia đình")
    title_e = html_lib.escape(title)
    price = product.get("price") or product.get("price_text") or ""
    price_e = html_lib.escape(str(price)) if price else "Xem giá ưu đãi"

    weekday = WEEKDAYS_VI[today.weekday()]
    top_date = f"{weekday}, {today.day} {MONTHS_VI[today.month]}, {today.year}"
    meta_date = f"{date_str} · 09:00 · Bài phân tích độc lập"

    # Tách đoạn body (plain text hoặc đã có <p>)
    if "<p>" in body:
        paras = re.findall(r"<p>(.*?)</p>", body, flags=re.S)
        paras = [re.sub(r"<[^>]+>", "", p).strip() for p in paras if p.strip()]
    else:
        paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

    story_parts = []
    for i, p in enumerate(paras[:8]):
        safe = html_lib.escape(p)
        if i == 0:
            story_parts.append(f'<p class="dropcap">{safe}</p>')
        elif i == 3 and len(paras) > 4:
            story_parts.append("<h2>Điểm đáng chú ý</h2>")
            story_parts.append(f"<p>{safe}</p>")
        else:
            story_parts.append(f"<p>{safe}</p>")
    story_html = "\n".join(story_parts)

    dek = html_lib.escape(
        (paras[0][:160] + "…") if paras and len(paras[0]) > 160 else (paras[0] if paras else highlights)
    )

    hero = ""
    if img:
        hero = (
            f'<a href="{aff}" target="_blank" rel="nofollow sponsored">'
            f'<img class="hero" src="{img}" alt="{name}"></a>'
        )

    page = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Góc Bếp Thông Minh | Tờ Báo AI</title>
<meta name="description" content="{title_e}">
<meta property="og:title" content="{title_e}">
<meta property="og:description" content="{dek}">
<meta property="og:type" content="website">
<meta property="og:image" content="{img}">
<style>
:root{{--ink:#171717;--paper:#fffdf8;--cream:#f3efe6;--red:#b42318;--line:#d7d1c5;--muted:#756f65;--gold:#a16207}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:#e9e5dc;color:var(--ink);font-family:Georgia,"Times New Roman",serif}}.paper{{max-width:1180px;margin:18px auto;background:var(--paper);min-height:100vh;box-shadow:0 8px 35px #0002}}.top{{padding:8px 28px;border-bottom:1px solid var(--line);font:12px Arial,sans-serif;color:var(--muted);display:flex;justify-content:space-between}}.mast{{padding:18px 28px 12px;text-align:center;border-bottom:4px double var(--ink)}}.mast .eyebrow{{font:700 11px Arial,sans-serif;letter-spacing:3px;text-transform:uppercase;color:var(--red)}}.mast h1{{font-size:clamp(38px,8vw,76px);line-height:.9;margin:7px 0 10px;letter-spacing:-3px}}.mast .motto{{font:italic 15px Georgia;color:var(--muted)}}.nav{{display:flex;justify-content:center;gap:26px;flex-wrap:wrap;padding:10px 20px;border-bottom:1px solid var(--line);font:700 12px Arial,sans-serif;text-transform:uppercase;letter-spacing:.7px}}.nav a{{color:var(--ink);text-decoration:none}}.nav a:hover{{color:var(--red)}}.breaking{{margin:0 28px;padding:9px 0;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:center;font:700 12px Arial,sans-serif}}.breaking b{{background:var(--red);color:#fff;padding:5px 9px}}.layout{{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(260px,1fr);gap:0;margin:0 28px}}.main{{padding:25px 28px 35px 0;border-right:1px solid var(--line)}}.side{{padding:25px 0 35px 24px}}.label{{font:700 11px Arial,sans-serif;letter-spacing:1.4px;text-transform:uppercase;color:var(--red)}}.headline{{font-size:clamp(34px,5vw,58px);line-height:1.02;margin:9px 0 12px;letter-spacing:-1.8px}}.dek{{font-size:19px;line-height:1.45;color:#49433b;margin-bottom:14px}}.meta{{font:12px Arial,sans-serif;color:var(--muted);padding:9px 0 15px;border-bottom:1px solid var(--line)}}.hero{{display:block;width:100%;height:min(480px,52vw);min-height:260px;object-fit:cover;margin:18px 0 7px;background:#ddd}}.caption{{font:11px Arial,sans-serif;color:var(--muted);font-style:italic}}.story{{font-size:18px;line-height:1.72}}.story p{{margin:17px 0}}.story h2{{font-size:25px;line-height:1.15;margin:28px 0 8px}}.dropcap:first-letter{{float:left;font-size:65px;line-height:.75;padding:9px 8px 0 0;color:var(--red);font-weight:bold}}.box{{border-top:3px solid var(--ink);border-bottom:1px solid var(--line);padding:12px 0;margin:24px 0}}.box h3{{margin:0 0 10px;font-size:18px}}.product{{display:grid;grid-template-columns:90px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}}.product:last-child{{border-bottom:0}}.product img{{width:90px;height:82px;object-fit:contain;background:#f5f2eb}}.product h4{{margin:0 0 4px;font-size:15px;line-height:1.25}}.price{{font:bold 14px Arial;color:var(--red)}}.buy{{display:inline-block;margin-top:6px;color:var(--red);font:700 11px Arial;text-decoration:none;border-bottom:1px solid var(--red)}}.side-title{{font-size:22px;border-bottom:3px solid var(--ink);padding-bottom:8px;margin:0 0 4px}}.brief{{padding:13px 0;border-bottom:1px solid var(--line)}}.brief strong{{font-size:16px;line-height:1.3;display:block}}.brief span{{font:10px Arial;color:var(--red);text-transform:uppercase}}.chat{{margin-top:25px;border:1px solid var(--ink);background:#faf8f2}}.chathead{{background:var(--ink);color:#fff;padding:12px 14px;display:flex;justify-content:space-between;font:700 12px Arial}}.chatbody{{height:180px;overflow:auto;padding:10px;font:13px Arial}}.msg{{max-width:88%;padding:8px 10px;margin:6px 0;border-radius:3px;background:#eee8dc}}.user{{margin-left:auto;background:#ead6d2}}.quick{{display:flex;gap:5px;flex-wrap:wrap;padding:8px;border-top:1px solid var(--line)}}.quick button{{font:11px Arial;border:1px solid var(--line);background:#fff;padding:6px 8px;cursor:pointer}}.form{{display:flex;border-top:1px solid var(--line)}}.form input{{flex:1;border:0;background:#fff;padding:11px;font:13px Arial;outline:0}}.form button{{border:0;background:var(--red);color:#fff;padding:0 14px;font:bold 12px Arial}}.disclosure{{font:11px Arial;color:var(--muted);border-top:1px solid var(--line);padding-top:13px;margin-top:25px;line-height:1.5}}.footer{{border-top:4px double var(--ink);padding:22px 28px;text-align:center;font:11px Arial;color:var(--muted)}}@media(max-width:760px){{.paper{{margin:0;box-shadow:none}}.top{{padding:7px 12px}}.mast{{padding:18px 12px 13px}}.mast h1{{letter-spacing:-2px}}.nav{{gap:14px;padding:9px 10px}}.breaking{{margin:0 12px}}.layout{{display:block;margin:0 12px}}.main{{padding:20px 0 28px;border-right:0;border-bottom:1px solid var(--line)}}.side{{padding:22px 0}}.headline{{font-size:36px}}.dek{{font-size:17px}}.hero{{height:70vw;min-height:220px}}.story{{font-size:17px}}.top span:last-child{{display:none}}}}
</style>
</head>
<body>
<div class="paper">
<div class="top"><span>{top_date}</span><span>ẤN BẢN ĐIỆN TỬ • TÒA SOẠN AI</span></div>
<header class="mast"><div class="eyebrow">Góc Bếp Thông Minh</div><h1>TỜ BÁO AI</h1><div class="motto">Tin đáng đọc · lựa chọn đáng tiền · thông tin có trách nhiệm</div></header>
<nav class="nav"><a href="./">Trang nhất</a><a href="#tieu-dung">Tiêu dùng</a><a href="#san-pham">Sản phẩm</a><a href="./bai-{slug}.html">Đọc đầy đủ</a><a href="./market.html">🛒 Chợ Deal</a><a href="#chatboss">ChatBoss</a></nav>
<div class="breaking"><b>TIN MỚI</b><span>Review hôm nay: {name} — dành cho {audience}</span></div>
<div class="layout">
<main class="main">
<div class="label">Tiêu dùng thông minh</div>
<h2 class="headline">{title_e}</h2>
<p class="dek">{dek}</p>
<div class="meta">{meta_date}</div>
{hero}
<div class="caption">Ảnh minh họa sản phẩm. Giá và tình trạng bán hàng có thể thay đổi theo thời điểm.</div>
<div class="story" id="tieu-dung">
{story_html}
<p><a href="./bai-{slug}.html" style="color:var(--red);font-weight:bold">→ Đọc bản đầy đủ</a> · <a href="{aff}" target="_blank" rel="nofollow sponsored" style="color:var(--red);font-weight:bold">Xem ưu đãi ngay</a></p>
</div>
<div class="disclosure">Minh bạch thương mại: một số liên kết trên trang là liên kết tiếp thị liên kết (affiliate). Tờ báo có thể nhận hoa hồng nếu phát sinh giao dịch hợp lệ. Điều này không làm thay đổi nguyên tắc đánh giá độc lập.</div>
</main>
<aside class="side" id="san-pham">
<h3 class="side-title">Đáng chú ý</h3>
<div class="brief"><span>01 · Sản phẩm hôm nay</span><strong>{name}</strong></div>
<div class="brief"><span>02 · Điểm mạnh</span><strong>{highlights or "Xem chi tiết trong bài"}</strong></div>
<div class="brief"><span>03 · Phù hợp</span><strong>{audience}</strong></div>
<div class="box"><h3>SẢN PHẨM TRONG BÀI</h3>
<div class="product">{"" if not img else f'<img src="{img}" alt="{name}">'}"<div><h4>{name}</h4><div class="price">{price_e}</div><a class="buy" href="{aff}" target="_blank" rel="nofollow sponsored">XEM ƯU ĐÃI →</a></div></div>
</div>
<section class="chat" id="chatboss"><div class="chathead"><span>🤖 CHATBOSS</span><span>TƯ VẤN</span></div><div class="chatbody" id="chatbody"><div class="msg">Xin chào. Tôi có thể tóm tắt bài review {name} hoặc gợi ý theo nhu cầu của bạn.</div></div><div class="quick"><button data-q="Tóm tắt bài">Tóm tắt</button><button data-q="Điểm mạnh sản phẩm">Điểm mạnh</button><button data-q="Tư vấn mua">Tư vấn mua</button></div><form class="form" id="form"><input id="input" placeholder="Hỏi ChatBoss..."><button>GỬI</button></form></section>
</aside>
</div>
<footer class="footer">© 2026 GÓC BẾP THÔNG MINH · TỜ BÁO AI · Nội dung được biên tập với mục tiêu cung cấp thông tin hữu ích và an toàn.</footer>
</div>
<script>
const body=document.getElementById("chatbody"),input=document.getElementById("input");
const productName="{name.replace(chr(34), chr(92)+chr(34))}";
const affLink="{aff}";
function ask(q){{if(!q.trim())return;let a="Tôi có thể giúp bạn hiểu bài review và cân nhắc trước khi mua.";if(/mua|tư vấn|giá|ưu đãi/i.test(q))a="Sản phẩm hôm nay: "+productName+". Bạn có thể xem ưu đãi tại: "+affLink;if(/tóm tắt|điểm mạnh|mạnh/i.test(q))a="{html_lib.escape(highlights or 'Xem chi tiết trong bài.')}";body.insertAdjacentHTML("beforeend","<div class='msg' style='background:#ead6d2;margin-left:auto'>"+q.replace(/</g,"<")+"</div><div class='msg'>"+a+"</div>");body.scrollTop=body.scrollHeight}}
document.querySelectorAll("[data-q]").forEach(b=>b.onclick=()=>ask(b.dataset.q));document.getElementById("form").onsubmit=e=>{{e.preventDefault();ask(input.value);input.value=""}};
</script>
</body>
</html>"""

    # Fix accidental quote from f-string product block
    page = page.replace('}"<div>', '}<div>')

    Path("index.html").write_text(page, encoding="utf-8")
    logger.info("Updated newspaper homepage index.html with today's review")


def _publish_html(html: str, slug: str) -> list[str]:
    """Ghi bài ra docs/ và root (GitHub Pages deploy từ root)."""
    targets = [
        DOCS_DIR / f"bai-{slug}.html",
        Path(f"bai-{slug}.html"),
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Wrote {target}")
    posts = sorted(
        [p.name for p in DOCS_DIR.glob("bai-*.html")] +
        [p.name for p in Path(".").glob("bai-*.html")],
        reverse=True,
    )
    update_index(list(dict.fromkeys(posts)), DOCS_DIR / "index.html")
    return posts


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
    body_text = "\n\n".join(lines[1:])
    body = "".join(f"<p>{l}</p>" for l in lines[1:])

    aff = product.get("affiliate_url") or product.get("link") or "#"
    meta = {
        "seo_title": title,
        "meta_description": f"Review {product['name']}",
        "keywords": product["name"],
    }
    html = render_html_page(title, body, product, meta, date_str, slug)
    _publish_html(html, slug)
    render_newspaper_home(product, title, body_text, date_str, slug, today)

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

    pid = product.get("id") or product.get("name", "unknown")
    if is_duplicate(pid, title, body, angle="daily_review"):
        logger.warning("Duplicate detected → block extended publish")
        return False

    meta = generate_seo_meta(product, title)
    gate = run_quality_gate(body, title, product, meta, is_duplicate=False)
    safety = safety_check(body, product)

    logger.info(
        f"Quality: fact={gate['fact'].get('score')} "
        f"quality={gate['quality']['score']} seo={gate['seo']['score']}"
    )
    logger.info(f"Safety: passed={safety['passed']} score={safety.get('score')}")

    if SAFE_MODE and (not gate["passed"] or not safety["passed"]):
        logger.warning("SAFE_MODE: content failed quality/safety → fallback Core")
        return False

    body_html = "".join(f"<p>{p}</p>" for p in body.split("\n\n") if p.strip())
    html = render_html_page(title, body_html, product, meta, date_str, slug)
    _publish_html(html, slug)
    render_newspaper_home(product, title, body, date_str, slug, today)

    social = generate_social_posts(product)
    write_social_outputs(product, title, slug, social, mode="v1")

    record_content(
        product_id=pid,
        title=title,
        body=body,
        angle="daily_review",
        content_type="long_review",
        extra={"slug": slug, "score": score_product(product)},
    )
    record_publish(pid, product["name"], slug, title, mode="extended")

    logger.info("✅ Extended pipeline published successfully")
    return True


def main():
    today = datetime.now(timezone(timedelta(hours=7)))
    date_str = today.strftime("%d/%m/%Y")
    slug = today.strftime("%Y-%m-%d")

    try:
        from modules.product_fetcher import run_fetch_and_merge, ENABLE_PRODUCT_FETCH
        if ENABLE_PRODUCT_FETCH:
            run_fetch_and_merge()
    except Exception as e:
        logger.warning(f"Product fetch skip: {e}")

    products = load_products()
    if not products:
        logger.error("No products found in products.json")
        sys.exit(1)

    product = select_product_for_today(products)
    if not product:
        logger.error("select_product_for_today returned None")
        sys.exit(1)

    logger.info(f"Today product: {product.get('name')} | score={score_product(product)}")

    success = False
    try:
        success = run_extended_pipeline(product, today, date_str, slug)
    except Exception as e:
        logger.error(f"Extended pipeline error: {e}")
        success = False

    if not success:
        try:
            run_original_core_flow(product, today, date_str, slug)
        except Exception as e:
            logger.error(f"Core flow also failed: {e}")
            raise

    try:
        s = summary()
        logger.info(f"Analytics: total_posts={s['total_posts']} | by_product={s['by_product']}")
    except Exception as e:
        logger.warning(f"Analytics summary failed: {e}")

    logger.info("🎉 Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)
