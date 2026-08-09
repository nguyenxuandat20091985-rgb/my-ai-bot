import os
import sys
import logging
import json
from litellm import completion

# Cấu hình Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Định nghĩa công cụ (Tool) cho AI
tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Truy cập một đường link website để đọc nội dung văn bản.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Đường link đầy đủ cần truy cập (vd: https://vnexpress.net)"}
                },
                "required": ["url"]
            }
        }
    }
]

def scrape_website(url: str) -> str:
    """Tool cào web tối ưu cho Groq"""
    import requests
    from bs4 import BeautifulSoup
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Loại bỏ thẻ thừa
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Cắt bớt nội dung còn 4000 ký tự để tránh tràn bộ nhớ của Groq
        return text[:4000]
    except Exception as e:
        return f"Lỗi cào web: {str(e)}"

def run_agent():
    # SỬ DỤNG GROQ - Model Llama 3.3 70B Versatile
    model = "groq/llama-3.3-70b-versatile"
    logger.info(f"🚀 Đang khởi động Agent với Groq model: {model}")

    messages = [
        {"role": "system", "content": "Bạn là AI Agent có khả năng tự dùng tool cào web. Luôn tư duy logic và trả lời bằng tiếng Việt."},
        {"role": "user", "content": "Hãy dùng tool scrape_website truy cập https://vnexpress.net/ và tóm tắt 3 tin công nghệ nổi bật nhất bằng tiếng Việt."}
    ]

    # Vòng lặp Agent (ReAct)
    while True:
        response = completion(model=model, messages=messages, tools=tools, tool_choice="auto")
        msg = response.choices[0].message
        
        # Thêm phản hồi của AI vào messages
        messages.append(msg)

        # Kiểm tra xem AI có gọi tool không
        if not msg.tool_calls:
            logger.info("💡 AI đã trả lời xong (không cần gọi thêm tool).")
            return msg.content

        # Xử lý các tool AI gọi
        for tool_call in msg.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "scrape_website":
                logger.info(f"⚙️ Đang cào web: {function_args['url']}")
                result = scrape_website(function_args['url'])
                
                # Nhét kết quả vào bộ nhớ của AI
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result
                })
                logger.info(f"✅ Đã lấy được dữ liệu web (độ dài: {len(result)} ký tự).")

if __name__ == "__main__":
    try:
        final_text = run_agent()
        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(final_text)
        logger.info("🎉 Hoàn thành! Đã lưu kết quả vào result.txt")
    except Exception as e:
        logger.error(f"❌ Lỗi hệ thống: {e}")
        sys.exit(1)