import os
import google.generativeai as genai
import sys

# 1. Cấu hình API Key
api_key = os.getenv("MY_API_KEY")

if not api_key:
    print("Lỗi: Không tìm thấy biến môi trường MY_API_KEY.")
    sys.exit(1)

# Debug: Chỉ in ra độ dài để kiểm tra key có bị rỗng hay quá ngắn không
print(f"Độ dài API Key nhận được: {len(api_key)} ký tự.")

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Đang gọi AI...")
    response = model.generate_content("Xin chao, ban la ai?")
    
    print("AI đã trả lời thành công!")
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(response.text)

except Exception as e:
    print(f"Lỗi API: {str(e)}")
    sys.exit(1)
