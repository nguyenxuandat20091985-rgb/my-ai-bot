import os
from google import genai # Thư viện mới

# Cấu hình
client = genai.Client(api_key=os.environ.get("MY_API_KEY"))

try:
    # Gọi AI bằng thư viện mới
    response = client.models.generate_content(
        model="gemini-2.0-flash", # Nên dùng model mới nhất/nhanh nhất
        contents="Xin chao, ban la ai?",
    )
    
    # Ghi log kết quả
    print(f"AI trả lời: {response.text}")
    
except Exception as e:
    print(f"Có lỗi xảy ra: {str(e)}")
