import os
import sys
import logging
import json
from litellm import completion

# Cấu hình Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Định nghĩa công cụ cào web cho AI
tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Truy cập một đường link website để đọc nội dung văn bản.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Đường link đầy đủ cần truy cập"}
                },
                "required": ["url"]
            }
        }
    }
]

def scrape_website(url: str) -> str:
    """Tool cào web tích hợp sẵn"""
    import requests
    from bs4 import BeautifulSoup
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        return soup.get_text(separator=' ', strip=True)[:6000]
    except Exception as e:
        return f"Lỗi cào web: {str(e)}"

def run_agent():
    # Sử dụng Gemini 2.0 Flash qua LiteLLM
    model = "gemini/gemini-2.0-flash"
    logger.info(f"Đang khởi động Agent với model: {model}")

    messages = [
        {"role": "system", "content": "Bạn là AI Agent có khả năng tự dùng tool cào web. Luôn tư duy logic."},
        {"role": "user", "content": "Hãy dùng tool scrape_website truy cập https://vnexpress.net/ và tóm tắt 3 tin công nghệ nổi bật nhất bằng tiếng Việt."}
    ]

    # Vòng lặp Agent (ReAct)
    while True:
        response = completion(model=model, messages=messages, tools=tools, tool_choice="auto")
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content # AI đã trả lời xong

        for tool_call in msg.tool_calls:
            if tool_call.function.name == "scrape_website":
                args = json.loads(tool_call.function.arguments)
                logger.info(f"Đang cào web: {args['url']}")
                result = scrape_website(args['url'])
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "content": result})

if __name__ == "__main__":
    try:
        final_text = run_agent()
        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(final_text)
        logger.info("Hoàn thành! Đã lưu vào result.txt")
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        sys.exit(1)