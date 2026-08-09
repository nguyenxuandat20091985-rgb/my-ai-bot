import os
import sys
import logging
import json
from litellm import completion

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    import requests
    from bs4 import BeautifulSoup
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        return text[:4000]
    except Exception as e:
        return f"Lỗi cào web: {str(e)}"

def run_agent():
    model = "groq/llama-3.3-70b-versatile"
    logger.info(f"Khởi động Agent với Groq model: {model}")

    messages = [
        {"role": "system", "content": "Bạn là AI Agent có khả năng tự dùng tool cào web. Luôn tư duy logic và trả lời bằng tiếng Việt."},
        {"role": "user", "content": "Hãy dùng tool scrape_website truy cập https://vnexpress.net/ và tóm tắt 3 tin công nghệ nổi bật nhất bằng tiếng Việt."}
    ]

    while True:
        response = completion(model=model, messages=messages, tools=tools, tool_choice="auto")
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            logger.info("AI đã trả lời xong.")
            return msg.content

        for tool_call in msg.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            if function_name == "scrape_website":
                logger.info(f"Đang cào web: {function_args['url']}")
                result = scrape_website(function_args['url'])
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": result})

if __name__ == "__main__":
    try:
        final_text = run_agent()
        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(final_text)
        logger.info("Hoàn thành! Đã lưu kết quả vào result.txt")
    except Exception as e:
        logger.error(f"Lỗi hệ thống: {e}")
        sys.exit(1)