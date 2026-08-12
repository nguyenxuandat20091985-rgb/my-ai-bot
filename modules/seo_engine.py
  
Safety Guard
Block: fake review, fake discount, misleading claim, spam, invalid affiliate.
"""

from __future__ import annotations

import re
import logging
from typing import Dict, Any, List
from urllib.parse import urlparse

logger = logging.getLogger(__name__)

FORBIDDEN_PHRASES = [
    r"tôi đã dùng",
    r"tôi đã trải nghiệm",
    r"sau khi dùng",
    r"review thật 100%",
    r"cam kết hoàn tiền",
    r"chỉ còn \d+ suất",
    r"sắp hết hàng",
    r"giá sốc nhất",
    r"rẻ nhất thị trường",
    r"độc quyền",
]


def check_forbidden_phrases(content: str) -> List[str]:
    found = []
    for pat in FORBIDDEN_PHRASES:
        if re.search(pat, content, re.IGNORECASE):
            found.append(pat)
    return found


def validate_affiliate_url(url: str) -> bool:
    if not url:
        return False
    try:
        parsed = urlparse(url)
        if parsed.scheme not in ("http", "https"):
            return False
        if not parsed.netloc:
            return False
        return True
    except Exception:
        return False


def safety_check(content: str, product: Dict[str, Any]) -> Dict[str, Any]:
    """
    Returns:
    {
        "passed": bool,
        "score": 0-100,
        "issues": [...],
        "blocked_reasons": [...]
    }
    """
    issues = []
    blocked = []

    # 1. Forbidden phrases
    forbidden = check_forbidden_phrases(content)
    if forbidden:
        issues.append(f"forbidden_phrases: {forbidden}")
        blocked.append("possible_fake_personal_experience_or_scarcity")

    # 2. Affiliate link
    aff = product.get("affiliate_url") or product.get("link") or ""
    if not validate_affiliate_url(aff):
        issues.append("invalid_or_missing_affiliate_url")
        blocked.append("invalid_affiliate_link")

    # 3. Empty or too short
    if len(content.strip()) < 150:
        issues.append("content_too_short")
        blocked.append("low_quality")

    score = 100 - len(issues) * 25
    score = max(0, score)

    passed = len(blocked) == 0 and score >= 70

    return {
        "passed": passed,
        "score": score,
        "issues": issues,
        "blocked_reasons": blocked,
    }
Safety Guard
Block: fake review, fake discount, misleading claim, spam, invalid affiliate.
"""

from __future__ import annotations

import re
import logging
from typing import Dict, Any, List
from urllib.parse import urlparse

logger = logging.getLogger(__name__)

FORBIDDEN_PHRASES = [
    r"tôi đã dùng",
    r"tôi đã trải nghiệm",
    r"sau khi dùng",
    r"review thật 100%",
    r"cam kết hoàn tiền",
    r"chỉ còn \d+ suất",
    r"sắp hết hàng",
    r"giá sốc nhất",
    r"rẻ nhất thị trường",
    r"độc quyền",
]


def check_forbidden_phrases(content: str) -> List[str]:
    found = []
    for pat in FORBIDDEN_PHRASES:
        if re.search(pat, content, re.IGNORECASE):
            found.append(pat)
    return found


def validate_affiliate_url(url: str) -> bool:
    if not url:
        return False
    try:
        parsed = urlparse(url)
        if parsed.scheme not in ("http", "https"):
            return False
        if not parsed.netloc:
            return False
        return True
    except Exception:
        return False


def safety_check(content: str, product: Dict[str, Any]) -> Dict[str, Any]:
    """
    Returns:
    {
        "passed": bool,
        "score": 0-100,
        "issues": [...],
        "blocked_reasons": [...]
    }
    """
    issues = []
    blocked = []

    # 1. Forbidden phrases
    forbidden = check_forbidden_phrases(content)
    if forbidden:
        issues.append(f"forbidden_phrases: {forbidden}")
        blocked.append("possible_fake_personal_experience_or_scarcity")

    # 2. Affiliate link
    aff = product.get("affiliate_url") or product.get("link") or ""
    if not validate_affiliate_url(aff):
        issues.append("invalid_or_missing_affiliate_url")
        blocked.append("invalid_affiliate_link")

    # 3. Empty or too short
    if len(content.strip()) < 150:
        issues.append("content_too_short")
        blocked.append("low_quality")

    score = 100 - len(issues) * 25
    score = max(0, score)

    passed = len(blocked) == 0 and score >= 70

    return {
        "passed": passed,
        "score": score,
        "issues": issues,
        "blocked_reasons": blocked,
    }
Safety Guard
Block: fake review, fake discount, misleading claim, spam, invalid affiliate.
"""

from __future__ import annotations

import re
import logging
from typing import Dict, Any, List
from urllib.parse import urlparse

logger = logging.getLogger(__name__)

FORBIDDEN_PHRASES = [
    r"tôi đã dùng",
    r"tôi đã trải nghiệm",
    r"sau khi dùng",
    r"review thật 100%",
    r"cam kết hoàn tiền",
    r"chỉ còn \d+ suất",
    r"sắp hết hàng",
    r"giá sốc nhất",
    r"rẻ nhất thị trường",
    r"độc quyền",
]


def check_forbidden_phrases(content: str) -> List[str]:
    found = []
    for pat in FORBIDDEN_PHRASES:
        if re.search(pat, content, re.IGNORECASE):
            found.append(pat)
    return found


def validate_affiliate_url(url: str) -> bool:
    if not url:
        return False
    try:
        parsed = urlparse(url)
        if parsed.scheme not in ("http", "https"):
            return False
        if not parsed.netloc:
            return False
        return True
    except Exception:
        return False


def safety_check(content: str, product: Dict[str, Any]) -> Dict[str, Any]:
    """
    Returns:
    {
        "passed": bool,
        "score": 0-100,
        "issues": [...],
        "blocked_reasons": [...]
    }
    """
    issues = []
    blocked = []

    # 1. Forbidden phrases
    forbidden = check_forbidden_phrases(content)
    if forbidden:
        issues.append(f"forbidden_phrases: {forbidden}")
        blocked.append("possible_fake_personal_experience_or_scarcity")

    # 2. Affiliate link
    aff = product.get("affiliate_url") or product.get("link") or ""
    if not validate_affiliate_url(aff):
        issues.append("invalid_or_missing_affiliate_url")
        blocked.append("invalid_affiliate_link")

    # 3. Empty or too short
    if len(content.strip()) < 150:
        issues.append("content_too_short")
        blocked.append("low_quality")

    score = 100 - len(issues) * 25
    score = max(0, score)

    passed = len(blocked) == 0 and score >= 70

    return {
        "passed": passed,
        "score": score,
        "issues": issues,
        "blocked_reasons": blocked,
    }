"""
SEO Engine
Generates meta, JSON-LD, sitemap helpers.
Respects current GitHub Pages /docs setup.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from pathlib import Path

from .config import BLOG_URL, SITE_NAME, SITE_DESCRIPTION, DOCS_DIR


def build_json_ld(product: Dict[str, Any], title: str, url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": f"Review {product.get('name')}",
        "datePublished": datetime.now(timezone(timedelta(hours=7))).date().isoformat(),
        "author": {
            "@type": "Organization",
            "name": SITE_NAME,
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
        },
        "mainEntityOfPage": url,
    }
    if product.get("image_url"):
        data["image"] = product["image_url"]
    return json.dumps(data, ensure_ascii=False)


def render_html_page(
    title: str,
    body_html: str,
    product: Dict[str, Any],
    meta: Dict[str, str],
    date_str: str,
    slug: str,
) -> str:
    """
    Full HTML with SEO tags.
    Compatible with existing visual style of Core.
    """
    aff_url = product.get("affiliate_url") or product.get("link") or "#"
    seo_title = meta.get("seo_title") or title
    meta_desc = meta.get("meta_description") or f"Review {product.get('name')}"
    keywords = meta.get("keywords") or ""
    page_url = f"{BLOG_URL}/bai-{slug}.html"
    json_ld = build_json_ld(product, title, page_url)

    css = """
body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f7f7fb;color:#222}
header{background:linear-gradient(90deg,#4f46e5,#ec4899);color:#fff;padding:16px;text-align:center}
.wrap{max-width:720px;margin:12px auto;padding:16px;background:#fff;border-radius:12px;line-height:1.7}
h1{font-size:1.5rem;line-height:1.3}
a.buy{display:block;text-align:center;background:#e11d48;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:bold;margin:20px 0}
.small{color:#888;font-size:0.85rem}
li{margin:6px 0}
.disclosure{font-size:0.8rem;color:#666;margin-top:24px;padding-top:12px;border-top:1px solid #eee}
"""

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{seo_title}</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{keywords}">
<link rel="canonical" href="{page_url}">
<meta property="og:title" content="{seo_title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{page_url}">
<meta property="og:site_name" content="{SITE_NAME}">
<script type="application/ld+json">{json_ld}</script>
<style>{css}</style>
</head>
<body>
<header><b>GÓC BẾP THÔNG MINH – SĂN DEAL</b><br><span class="small">Review thật lòng mỗi ngày</span></header>
<div class="wrap">
<h1>{title}</h1>
<p class="small">📅 {date_str}</p>
{body_html}
<a class="buy" href="{aff_url}" target="_blank" rel="nofollow sponsored">👉 BẤM XEM GIÁ ƯU ĐÃI HÔM NAY</a>
<p class="disclosure">Bài viết có chứa link affiliate. Người viết có thể nhận hoa hồng nếu bạn mua qua link này. Giá và tình trạng sản phẩm có thể thay đổi, vui lòng kiểm tra trên trang bán hàng.</p>
<p class="small">Bài viết do trợ lý AI biên soạn tự động dựa trên dữ liệu sản phẩm.</p>
</div>
</body>
</html>"""
    return html


def update_index(posts: List[str], output_path: Path) -> None:
    """Simple index updater. posts = list of 'bai-YYYY-MM-DD.html'"""
    items = "".join(
        f'<li><a href="{p}">📰 Bài ngày {p.replace("bai-", "").replace(".html", "")}</a></li>'
        for p in posts
    )
    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{SITE_NAME}</title>
<meta name="description" content="{SITE_DESCRIPTION}">
<style>
body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f7f7fb;color:#222}}
header{{background:linear-gradient(90deg,#4f46e5,#ec4899);color:#fff;padding:16px;text-align:center}}
.wrap{{max-width:720px;margin:12px auto;padding:16px;background:#fff;border-radius:12px;line-height:1.7}}
</style>
</head>
<body>
<header><b>GÓC BẾP THÔNG MINH – SĂN DEAL</b><br><span class="small">Review thật lòng mỗi ngày</span></header>
<div class="wrap">
<h1>Mục lục báo deal</h1>
<ul>{items}</ul>
</div>
</body>
</html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)