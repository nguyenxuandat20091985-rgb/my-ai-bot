"""
Gia Tộc Họ Nguyễn — Tờ báo độc lập về đất nước & con người Việt Nam.
Chạy hoàn toàn riêng, KHÔNG đụng news_bot.py / Tờ Báo AI / Chợ Deal.
Mỗi lần chạy xuất 1 bài; workflow chạy 3 lần/ngày → 3 bài/ngày.
Mỗi bài luôn có một link sản phẩm lấy từ products.json ở một khối riêng, không chi phối nội dung bài.
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from litellm import completion

from modules.config import BLOG_URL, DATA_DIR, DOCS_DIR, MAX_TOKENS, MODEL, TEMPERATURE

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FAMILY_DIR = DOCS_DIR / "gia-toc"
FINGERPRINT_FILE = DATA_DIR / "family_news_fingerprints.json"
ARTICLES_FILE = DATA_DIR / "family_articles.json"
FAMILY_BLOG = f"{BLOG_URL}/gia-toc"

# Chủ đề cố định — xoay vòng, chống lệch chủ đề
TOPICS = [
    {
        "id": "lang-nghe",
        "title_hint": "Làng nghề truyền thống Việt Nam",
        "prompt": "Viết về một làng nghề truyền thống nổi tiếng của Việt Nam (gốm Bát Tràng, lụa Vạn Phúc, tranh Đông Hồ, nón lá Huế, đúc đồng, mây tre đan…). Nêu lịch sử, kỹ thuật, giá trị văn hóa và ý nghĩa với đời sống người Việt.",
        "image_keywords": "vietnam traditional craft village pottery",
        "images": [
            "https://images.unsplash.com/photo-1528183429752-a97d0bf99b5a?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=1200&h=630&fit=crop",
        ],
    },
    {
        "id": "phong-tuc",
        "title_hint": "Phong tục tập quán các vùng miền",
        "prompt": "Viết về một phong tục tập quán đẹp của người Việt (Tết Nguyên Đán, giỗ tổ Hùng Vương, lễ hội đền Trần, tục thờ cúng tổ tiên, cưới hỏi truyền thống, ngày giỗ…). Giải thích ý nghĩa nhân văn và sự gắn kết gia đình.",
        "image_keywords": "vietnam tet festival traditional",
        "images": [
            "https://images.unsplash.com/photo-1548013146-72479768bada?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1509030450996-dd1a26dda6bc?w=1200&h=630&fit=crop",
        ],
    },
    {
        "id": "nhan-vat",
        "title_hint": "Nhân vật lịch sử / anh hùng dân tộc",
        "prompt": "Viết về một nhân vật lịch sử hoặc anh hùng dân tộc Việt Nam (Hùng Vương, Hai Bà Trưng, Lý Thái Tổ, Trần Hưng Đạo, Nguyễn Trãi, Quang Trung, Hồ Chí Minh…). Tập trung vào cống hiến, tấm gương đạo đức và bài học cho thế hệ sau. Không tranh luận chính trị nhạy cảm.",
        "image_keywords": "vietnam history monument temple",
        "images": [
            "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1528183429752-a97d0bf99b5a?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=1200&h=630&fit=crop",
        ],
    },
    {
        "id": "ho-nguyen",
        "title_hint": "Câu chuyện họ Nguyễn trong lịch sử",
        "prompt": "Viết về họ Nguyễn — họ lớn nhất Việt Nam: nguồn gốc, sự hiện diện trong lịch sử, các nhân vật họ Nguyễn tiêu biểu (Nguyễn Trãi, Nguyễn Du, Nguyễn Huệ…), giá trị gia tộc, tinh thần đoàn kết và tự hào dòng họ.",
        "image_keywords": "vietnam family ancestral altar traditional",
        "images": [
            "https://images.unsplash.com/photo-1548013146-72479768bada?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1509030450996-dd1a26dda6bc?w=1200&h=630&fit=crop",
        ],
    },
    {
        "id": "am-thuc",
        "title_hint": "Ẩm thực – lễ hội – văn hóa",
        "prompt": "Viết về một món ăn hoặc lễ hội ẩm thực Việt Nam (phở, bánh chưng, bún bò Huế, cao lầu, nem, mâm cỗ Tết…). Kể nguồn gốc, ý nghĩa văn hóa và cách món ăn gắn kết con người Việt.",
        "image_keywords": "vietnam food pho traditional cuisine",
        "images": [
            "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1528183429752-a97d0bf99b5a?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1548013146-72479768bada?w=1200&h=630&fit=crop",
        ],
    },
    {
        "id": "canh-dep",
        "title_hint": "Cảnh đẹp thiên nhiên – di sản",
        "prompt": "Viết về một danh thắng hoặc di sản Việt Nam (Vịnh Hạ Long, Phong Nha, Hội An, Mỹ Sơn, ruộng bậc thang Sapa, đồng bằng sông Cửu Long…). Mô tả vẻ đẹp, giá trị di sản và tinh thần giữ gìn quê hương.",
        "image_keywords": "vietnam landscape ha long bay nature",
        "images": [
            "https://images.unsplash.com/photo-1528183429752-a97d0bf99b5a?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=1200&h=630&fit=crop",
        ],
    },
    {
        "id": "gia-dinh",
        "title_hint": "Giá trị gia đình – tôn sư trọng đạo",
        "prompt": "Viết về giá trị gia đình Việt Nam: chữ hiếu, tình nghĩa vợ chồng, anh em, tôn sư trọng đạo, mái ấm gia đình. Lấy ví dụ đời thường và ý nghĩa với thế hệ trẻ.",
        "image_keywords": "vietnam family home traditional values",
        "images": [
            "https://images.unsplash.com/photo-1509030450996-dd1a26dda6bc?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1548013146-72479768bada?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=1200&h=630&fit=crop",
        ],
    },
    {
        "id": "con-nguoi",
        "title_hint": "Con người Việt Nam đương đại",
        "prompt": "Viết câu chuyện tích cực về con người Việt Nam hôm nay: sự chăm chỉ, hiếu học, đoàn kết, sáng tạo, giữ gìn bản sắc trong thời hiện đại. Không chính trị nhạy cảm, không chia rẽ.",
        "image_keywords": "vietnam people street life culture",
        "images": [
            "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1528183429752-a97d0bf99b5a?w=1200&h=630&fit=crop",
            "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=1200&h=630&fit=crop",
        ],
    },
]


def _now():
    return datetime.now(timezone(timedelta(hours=7)))


def _fingerprint(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", " ", (text or "").lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]


def load_fingerprints() -> list:
    try:
        data = json.loads(FINGERPRINT_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_fingerprints(items: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FINGERPRINT_FILE.write_text(json.dumps(items[-800:], ensure_ascii=False, indent=2), encoding="utf-8")


def load_articles() -> list:
    try:
        data = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_articles(items: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_FILE.write_text(json.dumps(items[-60:], ensure_ascii=False, indent=2), encoding="utf-8")


def pick_topic(used_ids: set) -> dict:
    available = [t for t in TOPICS if t["id"] not in used_ids]
    if not available:
        available = TOPICS
    # Xoay theo ngày + giờ để đa dạng trong ngày
    now = _now()
    idx = (now.toordinal() * 3 + now.hour) % len(available)
    return available[idx]


def pick_image(topic: dict, seed: str) -> str:
    # Ảnh minh họa lấy trực tiếp từ Internet; ưu tiên bộ ảnh theo chủ đề, có fallback.
    images = topic.get("images") or []
    if images:
        digest = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16)
        return images[digest % len(images)]
    return f"https://picsum.photos/seed/{hashlib.md5(seed.encode()).hexdigest()[:10]}/1200/630"


def required_product(sequence: int) -> dict:
    """Mỗi bài bắt buộc có một sản phẩm hợp lệ từ products.json, không phụ thuộc nội dung bài."""
    from modules.product_manager import load_products

    products = load_products()
    valid = [
        p for p in products
        if p.get("name") and (p.get("affiliate_url") or p.get("link") or p.get("product_url"))
    ]
    if not valid:
        raise RuntimeError("products.json không có sản phẩm nào có tên và link hợp lệ.")
    valid.sort(key=lambda p: str(p.get("id") or p.get("name") or ""))
    return valid[sequence % len(valid)]


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def ai_write(topic: dict) -> str:
    prompt = f"""Bạn là biên tập viên của tờ báo "Gia Tộc Họ Nguyễn" — tờ báo chuyên về đất nước và con người Việt Nam.

Yêu cầu:
- Chủ đề gợi ý: {topic["title_hint"]}
- Nhiệm vụ: {topic["prompt"]}
- Viết 700–1000 từ tiếng Việt, giọng trang trọng, gần gũi, tự hào dân tộc.
- Không chính trị nhạy cảm, không chia rẽ, không bôi nhọ.
- Không dùng markdown # hoặc **.
- Không chèn link.
- Không bịa sự kiện lịch sử không có cơ sở phổ thông.
- Cấu trúc:
  1) Dòng đầu tiên = tiêu đề hấp dẫn (không đánh số)
  2) Mở bài dẫn cảm xúc
  3) Nội dung chính (2–4 đoạn)
  4) Kết luận truyền cảm hứng giữ gìn bản sắc / giá trị gia đình

Chỉ trả về bài viết hoàn chỉnh."""
    for attempt in range(2):
        extra = "" if attempt == 0 else "\nBản trước chưa đạt độ dài. Hãy viết lại, bảo đảm phần thân bài có 700–1000 từ tiếng Việt."
        r = completion(
            model=MODEL,
            messages=[{"role": "user", "content": prompt + extra}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        text = (r.choices[0].message.content or "").strip()
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        body = "\n\n".join(lines[1:]) if len(lines) > 1 else text
        count = word_count(body)
        logger.info(f"Độ dài bài lần {attempt + 1}: {count} từ")
        if 700 <= count <= 1000:
            return text
    raise RuntimeError("AI không tạo được bài trong khoảng 700–1000 từ sau 2 lần thử.")


def render_article_html(title: str, body: str, image: str, date: str, slug: str, product: dict | None) -> str:
    paras = "".join(
        f"<p>{html.escape(x.strip())}</p>" for x in re.split(r"\n\s*\n", body) if x.strip()
    )
    img = (
        f'<img class="hero" src="{html.escape(image, quote=True)}" alt="{html.escape(title)}" loading="eager">'
        if image
        else ""
    )
    product_box = ""
    if product and (product.get("name")):
        purl = product.get("affiliate_url") or product.get("link") or product.get("product_url") or "#"
        product_box = f"""
        <aside class="product">
          <div class="product-label">Liên kết sản phẩm</div>
          <div class="product-name">{html.escape(product.get("name", ""))}</div>
          <a href="{html.escape(purl, quote=True)}" target="_blank" rel="nofollow sponsored">Xem sản phẩm →</a>
        </aside>"""

    css = """
*{box-sizing:border-box}body{margin:0;background:#faf7f2;color:#1c1917;font-family:Georgia,"Times New Roman",serif}
.wrap{max-width:880px;margin:0 auto;padding:20px}
.mast{background:linear-gradient(135deg,#7f1d1d,#b91c1c,#ca8a04);color:#fff;border-radius:20px;padding:28px 32px;margin-bottom:22px;box-shadow:0 12px 40px #7f1d1d33}
.mast h1{margin:0;font-size:28px;letter-spacing:.02em}
.mast p{margin:8px 0 0;opacity:.92;font-size:15px}
.article{background:#fff;border-radius:18px;padding:28px;box-shadow:0 8px 30px #0000000d;border:1px solid #f5e6d3}
.kicker{color:#b91c1c;font-weight:700;text-transform:uppercase;font-size:12px;letter-spacing:.08em;font-family:system-ui,sans-serif}
.title{font-size:34px;line-height:1.2;margin:12px 0 8px;color:#1c1917}
.meta{color:#78716c;font-size:14px;font-family:system-ui,sans-serif;margin-bottom:8px}
.hero{display:block;width:100%;max-height:460px;object-fit:cover;border-radius:14px;margin:18px 0;border:1px solid #f5e6d3}
.body{font-size:18px;line-height:1.85}.body p{margin:0 0 18px}
.product{margin-top:28px;padding:16px 18px;border-radius:14px;background:#fff7ed;border:1px solid #fed7aa;font-family:system-ui,sans-serif}
.product-label{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#c2410c;font-weight:700}
.product-name{margin:6px 0;font-weight:600;color:#1c1917}
.product a{color:#c2410c;font-weight:700;text-decoration:none}
.footer-note{margin-top:24px;font-size:13px;color:#a8a29e;font-family:system-ui,sans-serif}
.nav{margin-top:20px;font-family:system-ui,sans-serif}.nav a{color:#b91c1c;font-weight:600;text-decoration:none}
@media(max-width:600px){.wrap{padding:12px}.article{padding:18px}.title{font-size:26px}.body{font-size:17px}}
"""
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | Gia Tộc Họ Nguyễn</title>
<meta name="description" content="{html.escape(title)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:image" content="{html.escape(image, quote=True)}">
<meta property="og:url" content="{FAMILY_BLOG}/{html.escape(slug)}.html">
<meta name="twitter:card" content="summary_large_image">
<style>{css}</style>
</head>
<body>
<main class="wrap">
  <header class="mast">
    <h1>Gia Tộc Họ Nguyễn</h1>
    <p>Báo về đất nước &amp; con người Việt Nam · 3 bài mỗi ngày</p>
  </header>
  <article class="article">
    <div class="kicker">Ấn bản gia tộc</div>
    <h2 class="title">{html.escape(title)}</h2>
    <div class="meta">📅 {html.escape(date)}</div>
    {img}
    <div class="body">{paras}</div>
    {product_box}
    <p class="footer-note">Bài do AI biên tập trong khuôn khổ tờ báo Gia Tộc Họ Nguyễn — chủ đề đất nước, con người Việt Nam.</p>
    <p class="nav"><a href="index.html">← Về trang chủ tờ báo</a></p>
  </article>
</main>
</body>
</html>"""


def render_home(articles: list) -> str:
    cards = []
    for a in articles[:12]:
        title = html.escape(a.get("title", "Bài viết"))
        slug = html.escape(a.get("slug", ""))
        date = html.escape(a.get("date", ""))
        image = a.get("image", "")
        excerpt = html.escape((a.get("body", "")[:180] + "…") if a.get("body") else "")
        img = (
            f'<img src="{html.escape(image, quote=True)}" alt="{title}" loading="lazy">'
            if image
            else ""
        )
        cards.append(
            f"""<a class="card" href="{slug}.html">
  {img}
  <div class="card-body">
    <div class="kicker">Ấn bản gia tộc</div>
    <h2>{title}</h2>
    <div class="meta">📅 {date}</div>
    <p>{excerpt}</p>
  </div>
</a>"""
        )

    css = """
*{box-sizing:border-box}body{margin:0;background:#faf7f2;color:#1c1917;font-family:Georgia,"Times New Roman",serif}
.wrap{max-width:1000px;margin:0 auto;padding:20px}
.mast{background:linear-gradient(135deg,#7f1d1d,#b91c1c,#ca8a04);color:#fff;border-radius:22px;padding:32px;margin-bottom:24px;box-shadow:0 12px 40px #7f1d1d33}
.mast h1{margin:0;font-size:32px}.mast p{margin:10px 0 0;opacity:.92}
.grid{display:grid;gap:18px}
.card{display:block;background:#fff;border-radius:16px;overflow:hidden;text-decoration:none;color:inherit;border:1px solid #f5e6d3;box-shadow:0 6px 24px #0000000a;transition:transform .15s ease}
.card:hover{transform:translateY(-2px)}
.card img{width:100%;height:220px;object-fit:cover;display:block}
.card-body{padding:18px 20px}
.kicker{color:#b91c1c;font-weight:700;text-transform:uppercase;font-size:11px;letter-spacing:.08em;font-family:system-ui,sans-serif}
.card h2{font-size:22px;line-height:1.25;margin:8px 0}
.meta{color:#78716c;font-size:13px;font-family:system-ui,sans-serif}
.card p{color:#44403c;font-size:15px;line-height:1.6;margin:10px 0 0}
.empty{padding:40px;text-align:center;color:#78716c}
@media(min-width:720px){.grid{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.wrap{padding:12px}.mast h1{font-size:26px}.card img{height:180px}}
"""
    body_cards = "".join(cards) if cards else '<div class="empty">Chưa có bài. Workflow sẽ xuất bản tự động.</div>'
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gia Tộc Họ Nguyễn — Báo về đất nước & con người Việt Nam</title>
<meta name="description" content="Tờ báo Gia Tộc Họ Nguyễn: 3 bài mỗi ngày về đất nước và con người Việt Nam.">
<style>{css}</style>
</head>
<body>
<main class="wrap">
  <header class="mast">
    <h1>Gia Tộc Họ Nguyễn</h1>
    <p>Ấn phẩm độc lập về đất nước, con người và giá trị gia đình Việt Nam · 3 bài mỗi ngày</p>
  </header>
  <section class="grid">{body_cards}</section>
</main>
</body>
</html>"""


def main() -> None:
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fps = load_fingerprints()
    used_topics = {x.get("topic_id") for x in fps[-24:] if x.get("topic_id")}
    used_titles = {x.get("title_hash") for x in fps if x.get("title_hash")}

    topic = pick_topic(used_topics)
    logger.info(f"Chủ đề hôm nay: {topic['id']} — {topic['title_hint']}")

    raw = ai_write(topic)
    if not raw or len(raw) < 200:
        logger.error("AI trả về nội dung quá ngắn hoặc rỗng.")
        return

    lines = [x.strip() for x in raw.splitlines() if x.strip()]
    title = re.sub(r"^[\"'#*\d\.\)\-\s]+", "", lines[0]).strip()
    body = "\n\n".join(lines[1:]) if len(lines) > 1 else raw

    title_hash = _fingerprint(title)
    if title_hash in used_titles:
        logger.warning("Tiêu đề trùng — bỏ qua lần này để tránh lặp.")
        return

    now = _now()
    date_str = now.strftime("%d/%m/%Y %H:%M")
    slug = f"bai-{now.strftime('%Y-%m-%d')}-{now.strftime('%H%M')}"
    image = pick_image(topic, title)
    articles = load_articles()
    product = required_product(len(articles))

    article_html = render_article_html(title, body, image, date_str, slug, product)
    (FAMILY_DIR / f"{slug}.html").write_text(article_html, encoding="utf-8")
    entry = {
        "title": title,
        "body": body,
        "image": image,
        "date": date_str,
        "slug": slug,
        "topic_id": topic["id"],
        "created_at": now.isoformat(),
        "product_name": product.get("name", ""),
        "product_url": product.get("affiliate_url") or product.get("link") or product.get("product_url"),
    }
    articles.insert(0, entry)
    save_articles(articles)

    home = render_home(articles)
    (FAMILY_DIR / "index.html").write_text(home, encoding="utf-8")

    fps.append(
        {
            "title_hash": title_hash,
            "topic_id": topic["id"],
            "slug": slug,
            "created_at": now.isoformat(),
        }
    )
    save_fingerprints(fps)

    logger.info(f"Đã xuất bản: {FAMILY_DIR}/{slug}.html")
    logger.info(f"Trang chủ: {FAMILY_DIR}/index.html")


if __name__ == "__main__":
    try:
        main()
        logger.info("Hoàn thành tờ báo Gia Tộc Họ Nguyễn.")
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        raise
