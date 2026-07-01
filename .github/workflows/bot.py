import os
import google.generativeai as genai

# Cấu hình API Key lấy từ GitHub Secrets
api_key = os.getenv("MY_API_KEY")
genai.configure(api_key=api_key)

# Khởi tạo mô hình AI
model = genai.GenerativeModel('gemini-pro')

# Gửi yêu cầu cho AI
try:
    response = model.generate_content("Hãy viết một câu danh ngôn hay về sự kiên trì.")
    
    # Ghi kết quả vào file result.txt để GitHub lưu lại
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print("AI da tra loi va luu vao file result.txt")
except Exception as e:
    print(f"Co loi xay ra: {e}")
