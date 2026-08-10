# 🤖 my-ai-bot

Hệ thống tự động sinh bài review săn deal mỗi ngày + AI trợ lý công việc.

## Tính năng

- **bot.py**: Chạy hàng ngày qua GitHub Actions  
  → Chọn sản phẩm từ `products.json`  
  → Gọi Groq Llama 3.3 viết review  
  → Xuất HTML đẹp lên `docs/` (GitHub Pages)  
  → Sinh 3 bài social ngắn vào `result.txt`

- **app.py**: Streamlit AI trợ lý  
  → Có tool tự cào web  
  → Trả lời tiếng Việt

## Blog

https://nguyenxuandat20091985-rgb.github.io/my-ai-bot

## Setup nhanh

### 1. Secret trên GitHub
Vào **Settings → Secrets and variables → Actions**  
Thêm secret: `GROQ_API_KEY`

### 2. GitHub Pages
Settings → Pages → Source: **Deploy from a branch**  
Branch: `main` → folder `/docs`

### 3. Chạy local (bot)

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key
python bot.py