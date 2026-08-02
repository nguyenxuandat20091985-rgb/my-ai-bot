import os
import sys
from google import genai

api_key = os.getenv("MY_API_KEY")

if not api_key:
    print("Lỗi: Không tìm thấy biến môi trường MY_API_KEY.")
    sys.exit(1)

print(f"Độ dài API Key nhận được: {len(api_key)} ký tự.")

client = genai.Client(api_key=api_key)

try:
    print("Đang gọi AI...")
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Xin chào, bạn là ai? Hãy giới thiệu ngắn gọn bằng tiếng Việt."
    )
    
    print("AI đã trả lời thành công!")
    
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print("Đã lưu kết quả vào result.txt")

except Exception as e:
    print(f"Lỗi API: {str(e)}")
    sys.exit(1)