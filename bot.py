import os
import google.generativeai as genai

# 1. Lấy API Key từ GitHub Secrets
api_key = os.getenv("MY_API_KEY")
genai.configure(api_key=api_key)

# 2. Khởi tạo mô hình AI
model = genai.GenerativeModel('gemini-pro')

# 3. Gửi yêu cầu cho AI
try:
    print("Dang ket noi voi Gemini...")
    response = model.generate_content("Hãy viết một câu danh ngôn hay về sự kiên trì.")
    
    # 4. Ghi kết quả vào file result.txt
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print("AI da tra loi xong! Ket qua da duoc luu vao result.txt")
except Exception as e:
    print(f"Co loi xay ra: {e}")
