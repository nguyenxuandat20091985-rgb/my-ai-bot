import os
import google.generativeai as genai

# Lấy API Key từ Secrets của GitHub
api_key = os.getenv("MY_API_KEY")
genai.configure(api_key=api_key)

# Khởi tạo AI
model = genai.GenerativeModel('gemini-pro')

try:
    # Gửi yêu cầu cho AI
    response = model.generate_content("Hãy viết một câu danh ngôn hay về sự kiên trì.")
    
    # Lưu kết quả vào file
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("AI đã trả lời thành công!")
except Exception as e:
    # Nếu lỗi, ghi lỗi ra file để mình biết
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(f"Loi xay ra: {e}")
