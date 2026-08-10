import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from litellm import completion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

MODEL = "groq/llama-3.3-70b-versatile"
BLOG_URL = "https://nguyenxuandat20091985-rgb.github.io/my-ai-bot"
TZ = timezone(timedelta(hours=7))

# ========== CSS HIỆN ĐẠI ==========
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --primary: #4f46e5;
  --primary-dark: #4338ca;
  --accent: #ec4899;
  --bg: #f8fafc;
  --card: #ffffff;
  --text: #0f172a;
  --muted: #64748b;
  --border: #e2e8f0;
  --radius: 16px;
  --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.05);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}

.header {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
  color: white;
  padding: 28px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 50%, rgba(255,255,255,0.12), transparent 50%);
}

.header-inner { position: relative; z-index: 1; }

.header h1 {
  font-size: 1.55rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 4px;
}

.header p {
  font-size: 0.9rem;
  opacity: 0.9;
  font-weight: 500;
}

.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 16px 60px;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  overflow: hidden;
}

.article {
  padding: 32px 28px;
}

.article h1 {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.3;
  margin-bottom: 12px;
  color: var(--text);
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.article p {
  margin-bottom: 1.25rem;
  font-size: 1.05rem;
  color: #334155;
}

.article p:last-of-type { margin-bottom: 0; }

.cta {
  display: block;
  margin: 36px 0 24px;
  background: linear-gradient(135deg, #e11d48, #be123c);
  color: white !important;
  text-align: center;
  padding: 16px 24px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1.05rem;
  text-decoration: none;
  box-shadow: 0 4px 14px rgba(225, 29, 72, 0.35);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.cta:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(225, 29, 72, 0.45);
}

.footer-note {
  text-align: center;
  color: var(--muted);
  font-size: 0.8rem;
  margin-top: 8px;
}

/* Index page */
.list-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 24px;
  text-align: center;
}

.post-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-item a {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  text-decoration: none;
  color: var(--text);
  font-weight: 600;
  box-shadow: var(--shadow);
  transition: all 0.15s ease;
}

.post-item a:hover {
  border-color: #c7d2fe;
  box-shadow: var(--shadow-lg);
  transform: translateY(-1px);
}

.post-item .icon {
  font-size: 1.4rem;
  flex-shrink: 0;
}

.post-item .date {
  color: var(--muted);
  font-size: 0.85rem;
  font-weight: 500;
  margin-left: auto;
}

@media (max-width: 640px) {
  .article { padding: 24px 20px; }
  .article h1 { font-size: 1.45rem; }
  .header h1 { font-size: 1.35rem; }
}
"""

def ai(prompt: str) -> str:
    resp = completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75,
        max_tokens=2048
    )
    return resp.choices[0].message.content.strip()

def load_products() -> list:
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)["products"]

def page_shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{title} – Review thật lòng từ Góc Bếp Thông Minh">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="Review đồ gia dụng & deal thật lòng mỗi ngày">
  <meta property="og:type" content="article">
  <title>{title}</title>
  <style>{CSS}</style>
</head>
<body>
  <header class="header">
    <div class="header-inner">
      <h1>Góc Bếp Thông Minh</h1>
      <p>Săn deal · Review thật lòng mỗi ngày</p>
    </div>
  </header>
  <main class="container">
    {body}
  </main>
</body>
</html>"""

def main():
    today = datetime.now(TZ)
    date_str = today.strftime("%d/%m/%Y")
    slug = today.strftime("%Y-%m-%d")

    products = load_products()
    product = products[today.toordinal() % len(products)]
    logger.info(f"Sản phẩm hôm nay: {product['name']}")

    # ===== Sinh bài review =====
    raw = ai(
        f"""Bạn là cây viết review đồ gia dụng nổi tiếng Việt Nam.
Văn phong: thật thà, gần gũi, hài hước nhẹ, dễ đọc.

Viết bài review khoảng 450-550 từ về: {product['name']}.
Điểm mạnh: {product['highlights']}
Đối tượng: {product['audience']}

YÊU CẦU BẮT BUỘC:
- Dòng ĐẦU TIÊN chỉ là tiêu đề giật gân (không có #, *, dấu ngoặc).
- Các dòng sau là nội dung, mỗi đoạn cách nhau 1 dòng trống.
- Không dùng markdown.
- Cuối bài nhắc người đọc bấm link ưu đãi.
- Chỉ dùng thông tin được cung cấp, không bịa thêm link khác."""
    )

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    title = lines[0].lstrip("#*•- ").strip()
    paragraphs = lines[1:]

    body_html = "".join(f"<p>{p}</p>" for p in paragraphs)

    article = f"""
    <article class="card article">
      <h1>{title}</h1>
      <div class="meta">
        <span>📅 {date_str}</span>
        <span>·</span>
        <span>Review tự động</span>
      </div>
      {body_html}
      <a class="cta" href="{product['link']}" target="_blank" rel="noopener">
        👉 Xem giá ưu đãi hôm nay
      </a>
      <p class="footer-note">Bài viết do trợ lý AI biên soạn tự động.</p>
    </article>
    """

    os.makedirs("docs", exist_ok=True)
    with open(f"docs/bai-{slug}.html", "w", encoding="utf-8") as f:
        f.write(page_shell(title, article))
    logger.info(f"Đã xuất bản: docs/bai-{slug}.html")

    # ===== Cập nhật mục lục =====
    posts = sorted(
        [p for p in os.listdir("docs") if p.startswith("bai-") and p.endswith(".html")],
        reverse=True
    )

    items = ""
    for p in posts:
        date_part = p.replace("bai-", "").replace(".html", "")
        items += f"""
        <li class="post-item">
          <a href="{p}">
            <span class="icon">📰</span>
            <span>Bài ngày {date_part}</span>
            <span class="date">{date_part}</span>
          </a>
        </li>"""

    index_body = f"""
    <div class="card" style="padding: 28px 24px;">
      <h2 class="list-title">Mục lục săn deal</h2>
      <ul class="post-list">{items}</ul>
    </div>
    """

    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(page_shell("Góc Bếp Thông Minh – Săn Deal", index_body))
    logger.info("Đã cập nhật docs/index.html")

    # ===== 3 bài social =====
    social = ai(
        f"""Dựa trên sản phẩm: {product['name']}
Điểm mạnh: {product['highlights']}

Viết đúng 3 bài đăng mạng xã hội tiếng Việt.
Mỗi bài dưới 8 câu, có emoji vui, kết thúc bằng link: {product['link']}

Phân cách các bài bằng đúng một dòng chứa ---
Không thêm tiêu đề hay số thứ tự."""
    )

    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(f"📰 BÀI MỚI:\n{BLOG_URL}/bai-{slug}.html\n\n")
        f.write("👇 3 BÀI NGẮN COPY ĐI GIEO LINK:\n\n")
        f.write(social)

    logger.info("Đã lưu result.txt")

if __name__ == "__main__":
    try:
        main()
        logger.info("Hoàn thành!")
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        sys.exit(1)