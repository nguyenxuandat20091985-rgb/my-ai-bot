import os
import google.generativeai as genai

# Cấu hình API
try:
    api_key = os.getenv("MY_API_KEY")
    if not api_key:
        raise ValueError("Chua tim thay API Key! Kiem tra lai Secrets.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Thử gọi AI
    response = model.generate_content("Xin chao, ban la ai?")
    
    # Ghi kết quả thành công
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write("AI tra loi: " + response.text)

except Exception as e:
    # Nếu lỗi, ghi thẳng lỗi vào result.txt để anh đọc
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(f"LOI ROI: {str(e)}")
