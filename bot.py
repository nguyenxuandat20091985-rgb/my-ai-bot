import os
import sys
import logging
import json
from litellm import completion
from tools.web_scraper import scrape_website

# Cấu hình Logging chuẩn cho GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Định nghĩa công cụ theo chuẩn OpenAI (được litellm tự động dịch sang Gemini/Claude)
tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Truy cập một đường link website để đọc nội dung văn bản của bài báo hoặc trang web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Đường link đầy đủ cần truy cập (ví dụ: https://vnexpress.net)"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

def route_and_execute(task_description: str):
    # --- MULTI-MODEL ROUTER ---
    # Anh có thể đổi model tùy ý. Litellm hỗ trợ:
    # - gemini/gemini-2.0-flash (Nhanh, rẻ, đọc web cực tốt)
    # - claude-3-5-sonnet-20241022 (Suy luận sâu, logic cực đỉnh)
    # - gpt-4o (Đa dụng, sáng tạo)
    
    # Ta chọn Gemini 2.0 Flash cho tác vụ đọc báo vì tốc độ nhanh và context lớn.
    model = "gemini/gemini-2.0-flash" 
    logger.info(f"🧠 Router đã chọn model: {model}")

    messages = [
        {"role": "system", "content": "Bạn là một trợ lý AI siêu việt có khả năng tự động sử dụng công cụ (tool calling) để lấy thông tin từ internet. Hãy luôn tư duy logic trước khi hành động."},
        {"role": "user", "content": task_description}
    ]

    # --- BƯỚC 1: AI SUY NGHĨ VÀ QUYẾT ĐỊNH GỌI TOOL ---
    logger.info("🔄 Đang gửi yêu cầu tới AI...")
    response = completion(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto" # Cho phép AI tự quyết định có gọi tool hay không
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # Nếu AI thấy không cần lên mạng (ví dụ hỏi kiến thức chung), nó sẽ trả lời luôn
    if not tool_calls:
        logger.info("💡 AI trả lời trực tiếp không cần công cụ.")
        return response_message.content

    # --- BƯỚC 2: AGENT LOOP (THỰC THI CÔNG CỤ) ---
    # Thêm phản hồi của AI vào messages để duy trì ngữ cảnh
    messages.append(response_message)

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        logger.info(f"⚙️ AI đang gọi công cụ: {function_name} với tham số: {function_args}")

        if function_name == "scrape_website":
            url = function_args.get("url")
            tool_response = scrape_website(url)
            logger.info(f"📄 Đã cào web thành công. Độ dài nội dung: {len(tool_response)} ký tự.")

            # Nhét kết quả cào web vào bộ nhớ của AI
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": tool_response
            })

    # --- BƯỚC 3: AI TÓM TẮT KẾT QUẢ ---
    logger.info("🔄 Đang gửi kết quả cào web lại cho AI để phân tích và tóm tắt...")
    final_response = completion(
        model=model,
        messages=messages
    )

    return final_response.choices[0].message.content

if __name__ == "__main__":
    # --- TÁC VỤ MẪU CHO AGENTIC AI ---
    # Anh có thể thay đổi TASK này để bot làm các việc khác nhau mỗi ngày
    TASK = """
    Hãy đóng vai một chuyên gia phân tích công nghệ.
    Bạn hãy sử dụng công cụ scrape_website để truy cập trang https://vnexpress.net/
    Sau đó, tìm kiếm trong nội dung trang nhất và tóm tắt cho tôi 3 bài viết nổi bật nhất liên quan đến "Trí tuệ nhân tạo" (AI) hoặc "Công nghệ".
    Trình bày rõ ràng, mạch lạc, có gạch đầu dòng bằng tiếng Việt.
    """

    try:
        final_text = route_and_execute(TASK)
        with open("result.txt", "w", encoding="utf-8") as f:
            f.write(final_text)
        logger.info("✅ Hoàn thành! Đã lưu kết quả vào result.txt")
    except Exception as e:
        logger.error(f"❌ Lỗi hệ thống: {str(e)}")
        sys.exit(1)