"""
SEO Engine – Magazine UI + hỗ trợ ảnh sản phẩm
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from pathlib import Path

from .config import BLOG_URL, SITE_NAME, SITE_DESCRIPTION, DOCS_DIR

MAGAZINE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: #f8fafc; color: #1e293b; line-height: 1.6;
  -webkit-font-smoothing: antialiased; padding: 16px 16px 32px;
  min-height: 100vh; display: flex; flex-direction: column; align-items: center;
}
.container { max-width: 820px; width: 100%; margin: 0 auto; }
.magazine-header {
  background: linear-gradient(145deg, #4f46e5 0%, #7c3aed 45%, #ec4899 100%);
  border-radius: 28px; padding: 40px 28px 32px; margin-bottom: 32px;
  box-shadow: 0 16px 40px -8px rgba(79, 70, 229, 0.30);
  text-align: center; color: #ffffff; position: relative; overflow: hidden;
}
.magazine-header h1 { font-size: 2.1rem; font-weight: 700; margin-bottom: 8px; }
.magazine-header .slogan {
  font-size: 0.95rem; opacity: 0.92; background: rgba(255,255,255,0.12);
  display: inline-block; padding: 4px 18px; border-radius: 40px;
}
.article-card {
  background: #ffffff; border-radius: 24px; padding: 24px 24px 28px;
  margin-bottom: 28px; box-shadow: 0 8px 28px rgba(0,0,0,0.04);
  border-left: 6px solid transparent;
  border-image: linear-gradient(180deg, #4f46e5, #ec4899) 1;
}
.featured-badge {
  display: inline-block; background: #fce7f3; color: #be185d;
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.8px; padding: 4px 14px; border-radius: 40px; margin-bottom: 16px;
}
.article-card h1 { font-size: 1.7rem; font-weight: 700; line-height: 1.3; margin-bottom: 12px; }
.article-meta { font-size: 0.9rem; color: #64748b; margin-bottom: 20px; }
.article-body { font-size: 1.05rem; line-height: 1.75; color: #334155; }
.article-body p { margin-bottom: 16px; }
.product-img {
  width: 100%; max-height: 320px; object-fit: contain; border-radius: 16px;
  margin: 8px 0 20px; background: #f1f5f9;
}
.btn-buy {
  display: block; text-align: center;
  background: linear-gradient(135deg, #e11d48, #be185d);
  color: #fff; padding: 14px 24px; border-radius: 14px;
  text-decoration: none; font-weight: 700; font-size: 1.05rem;
  margin: 28px 0 16px; box-shadow: 0 6px 20px rgba(225, 29, 72, 0.25);
}
.disclosure {
  font-size: 0.8rem; color: #64748b; margin-top: 24px;
  padding-top: 16px; border-top: 1px solid #e2e8f0;
}
.section-label {
  display: flex; align-items: center; gap: 12px;
  font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 1.6px; color: #94a3b8; margin-bottom: 18px;
}
.section-label::before, .section-label::after {
  content: ""; flex: 1; height: 1px; background: #e2e8f0;
}
.archive-list { display: flex; flex-direction: column; gap: 12px; }
.archive-item {
  background: #ffffff; border-radius: 18px; padding: 16px 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02); border: 1px solid #f1f5f9;
  display: flex; justify-content: space-between; align-items: center;
  text-decoration: none; color: inherit;
}
.archive-item .info h3 { font-size: 1.05rem; font-weight: 600; color: #1e293b; }
.archive-item .info .date { font-size: 0.8rem; color: #94a3b8; }
.archive-item .arrow { color: #4f46e5; font-size: 1.25rem; }
.footer {
  text-align: center; padding: 32px 0 8px; margin-top: 40px;
  border-top: 1px solid #e9eef3; color: #94a3b8; font-size: 0.8rem;
}
.footer span { color: #4f46e5; font-weight: 500; }
@media (max-width: 600px) {
  .magazine-header h1 { font-size: 1.6rem; }
  .article-card h1 { font-size: 1.35rem; }
}
"""


def build_json_ld(product: Dict[str, Any], title: str, url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": f"Review {product.get('name')}",
        "datePublished": datetime.now(timezone(timedelta(hours=7))).date().isoformat(),
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
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
    aff_url = product.get("affiliate_url") or product.get("link") or "#"
    seo_title = meta.get("seo_title") or title
    meta_desc = meta.get("meta_description") or f"Review {product.get('name')} – Góc Bếp Thông Minh"
    keywords = meta.get("keywords") or ""
    page_url = f"{BLOG_URL}/bai-{slug}.html"
    json_ld = build_json_ld(product, title, page_url)

    img_html = ""
    if product.get("image_url"):
        img_html = f'<img class="product-img" src="{product["image_url"]}" alt="{product.get("name", "")}" loading="lazy">'

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
  <style>{MAGAZINE_CSS}</style>
</head>
<body>
  <div class="container">
    <header class="magazine-header">
      <h1>Góc Bếp Thông Minh</h1>
      <span class="slogan">Review thật lòng &amp; săn deal chính hãng mỗi ngày</span>
    </header>
    <article class="article-card">
      <span class="featured-badge">🔥 Review hôm nay</span>
      <h1>{title}</h1>
      <p class="article-meta">📅 {date_str}</p>
      {img_html}
      <div class="article-body">{body_html}</div>
      <a class="btn-buy" href="{aff_url}" target="_blank" rel="nofollow sponsored">
        👉 BẤM XEM GIÁ ƯU ĐÃI HÔM NAY
      </a>
      <p class="disclosure">
        Bài viết có chứa link affiliate. Người viết có thể nhận hoa hồng nếu bạn mua qua link này.
        Giá và tình trạng sản phẩm có thể thay đổi, vui lòng kiểm tra trên trang bán hàng.
      </p>
    </article>
    <footer class="footer">
      <p>© 2026 <span>Góc Bếp Thông Minh</span> – All rights reserved.</p>
    </footer>
  </div>
</body>
</html>"""
    return html


def update_index(posts: List[str], output_path: Path) -> None:
    if not posts:
        posts = []

    featured_html = ""
    archive_html = ""

    if posts:
        newest = posts[0]
        date_str = newest.replace("bai-", "").replace(".html", "")
        try:
            y, m, d = date_str.split("-")
            nice_date = f"{d}/{m}/{y}"
        except Exception:
            nice_date = date_str

        featured_html = f"""
    <article class="article-card">
      <span class="featured-badge">🔥 Mới nhất</span>
      <h2 style="font-size:1.5rem;font-weight:700;margin-bottom:12px;">
        <a href="{newest}" style="color:#1e293b;text-decoration:none;">Review săn deal ngày {nice_date}</a>
      </h2>
      <p style="color:#475569;font-size:0.98rem;margin-bottom:20px;line-height:1.6;">
        Đánh giá chi tiết, phân tích ưu nhược điểm và chia sẻ kinh nghiệm săn deal giá hời cho thiết bị nhà bếp đáng mua nhất hôm nay.
      </p>
      <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid #f1f5f9;padding-top:18px;font-size:0.85rem;color:#64748b;flex-wrap:wrap;gap:12px;">
        <span>📅 {nice_date}</span>
        <a href="{newest}" style="background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;padding:10px 22px;border-radius:40px;text-decoration:none;font-weight:600;font-size:0.85rem;">
          Đọc bài viết →
        </a>
      </div>
    </article>
"""
        for p in posts[1:]:
            ds = p.replace("bai-", "").replace(".html", "")
            try:
                y, m, d = ds.split("-")
                nice = f"{d}/{m}/{y}"
            except Exception:
                nice = ds
            archive_html += f"""
      <a href="{p}" class="archive-item">
        <div class="info">
          <h3>Review thiết bị gia dụng ngày {nice}</h3>
          <span class="date">📅 {nice}</span>
        </div>
        <span class="arrow">→</span>
      </a>
"""

    archive_section = ""
    if archive_html:
        archive_section = f"""
    <div class="section-label">Các số báo trước</div>
    <div class="archive-list">{archive_html}</div>
"""

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{SITE_NAME}</title>
  <meta name="description" content="{SITE_DESCRIPTION}">
  <style>{MAGAZINE_CSS}</style>
</head>
<body>
  <div class="container">
    <header class="magazine-header">
      <h1>Góc Bếp Thông Minh</h1>
      <span class="slogan">Review thật lòng &amp; săn deal chính hãng mỗi ngày</span>
    </header>
    {featured_html}
    {archive_section}
    <footer class="footer">
      <p>© 2026 <span>Góc Bếp Thông Minh</span> – All rights reserved.</p>
    </footer>
  </div>
</body>
</html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)