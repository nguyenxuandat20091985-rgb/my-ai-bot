import os
import sys
import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from litellm import completion

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODEL = "groq/llama-3.3-70b-versatile"
BLOG_URL = "https://nguyenxuandat20091985-rgb.github.io/my-ai-bot"
WEBHOOK_URL = "https://hook.eu1.make.com/93lazxg8m91zwbwyvzpx32kgifl3g75c"

CSS = """
body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f7f7fb;color:#222}
header{background:linear-gradient(90deg,#4f46e5,#ec4899);color:#fff;padding:16px;text-align:center}
.wrap{max-width:720px;margin:12px auto;padding:16px;background:#fff;border-radius:12px;line-height:1.7}
h1{font-size:1.5rem;line-height:1.3}
a.buy{display:block;text-align:center;background:#e11d48;color:#fff;padding:12px;border-radius:10px;text-decoration:none;font-weight:bold;margin:20px 0}
.small{color:#888;font-size:0.85rem}
li{margin:6px 0}
"""

def ai(prompt):
    resp = completion(model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.8)
    return resp.choices[0].message.content

def load_products():
    with open("products.json", "r", encoding="utf-8") as f:
        return json.load(f)["products"]

def page_shell(title, inner):
    return f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title><style>{CSS}</style></head>
<body>
<header><b>GÓC BẾP THÔNG MINH – SĂN DEAL</b><br><span class="small">Review thật lòng mỗi ngày</span></header>
<div class="wrap">{inner}</div>
</body></html>"""

def send_to_make_webhook(title, social_content, affiliate_link, blog_post_url):
    payload = {
        "title": title,
        "content": social_content,
        "affiliate_link": affiliate_link,
        "blog_url": blog_post_url
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Đã tự động bắn dữ liệu sang Make.com thành công!")
        else:
            logger.warning(f"⚠️ Gửi webhook thất bại, mã lỗi: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Lỗi kết nối đến Make.com: {e}")

def main():
    today = datetime.now(timezone(timedelta(hours=7)))
    date_str = today.strftime("%d/%m/%Y")
    slug = today.strftime("%Y-%m-%d")

    products = load_products()
    product = products[today.toordinal() % len(products)]
    logger.info(f"Hôm nay AI chọn sản phẩm: {product['name']}")

    raw = ai(
        "Bạn là cây viết review đồ gia dụng nổi tiếng Việt Nam, văn phong thật thà, gần gũi, hài hước nhẹ.\n"
        f"Hãy viết bài review khoảng 500 từ về: {product['name']}.\n"
        f"Điểm mạnh: {product['highlights']}\n"
        f"Người đọc: {product['audience']}\n"
        "Yêu cầu: dòng ĐẦU TIÊN là tiêu đề giật gân (không kèm ký tự # hay *), các dòng sau là nội dung, "
        "mỗi đoạn cách nhau một dòng trống. Cuối bài nhắc người đọc bấm link ưu đãi."
    )
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    title = lines[0].lstrip('#* ')
    body = "".join(f"<p>{l}</p>" for l in lines[1:])

    inner = f"<h1>{title}</h1><p class='small'>📅 {date_str}</p>{body}"
    inner += f"<a class='buy' href='{product['link']}' target='_blank'>👉 BẤM XEM GIÁ ƯU ĐÃI HÔM NAY</a>"
    inner += "<p class='small'>Bài viết do trợ lý AI biên soạn tự động.</p>"

    with open(f"bai-{slug}.html", "w", encoding="utf-8") as f:
        f.write(page_shell(title, inner))
    logger.info(f"Đã xuất bản: bai-{slug}.html")

    posts = sorted([p for p in os.listdir(".") if p.startswith("bai-")], reverse=True)
    items = "".join(f"<li><a href='{p}'>📰 Bài ngày {p.replace('bai-','').replace('.html','')}</a></li>" for p in posts)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page_shell("Góc Bếp Thông Minh – Săn Deal", f"<h1>Mục lục báo deal</h1><ul>{items}</ul>"))

    social = ai(
        f"Dựa trên sản phẩm {product['name']} (điểm mạnh: {product['highlights']}), "
        f"viết 1 bài đăng mạng xã hội tiếng Việt ngắn dưới 8 câu, có emoji vui, cuối bài kèm link {product['link']}."
    )
    
    blog_post_url = f"{BLOG_URL}/bai-{slug}.html"

    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(f"📰 BÀI MỚI TRÊN BÁO CỦA ANH:\n{blog_post_url}\n\n")
        f.write("👇 BÀI NGẮN COPY ĐI GIEO LINK:\n\n")
        f.write(social)
    logger.info("Đã lưu bài ngắn vào result.txt")

    # Tự động bắn dữ liệu qua Webhook của Make.com
    send_to_make_webhook(title, social, product['link'], blog_post_url)

if __name__ == "__main__":
    try:
        main()
        logger.info("🎉 Hoàn thành! Tờ báo đã tự xuất bản và kích hoạt phân phối tự động.")
    except Exception as e:
        logger.error(f"Lỗi hệ thống: {e}")
        sys.exit(1)
