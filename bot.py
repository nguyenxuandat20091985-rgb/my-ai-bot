import os
import google.generativeai as genai
import sys

# 1. Cấu hình API Key
api_key = os.getenv("MY_API_KEY")

if not api_key:
    print("Lỗi: Không tìm thấy biến môi trường MY_API_KEY. Hãy kiểm tra lại Secrets trong GitHub.")
    sys.exit(1) # Dừng chương trình nếu không có API Key

genai.configure(api_key=api_key)

try:
    # Sử dụng model gemini-1.5-flash (nhanh và ổn định hơn gemini-pro cũ)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 2. Gọi AI
    print("Đang kết nối với AI...")
    response = model.generate_content("Xin chao, ban la ai?")
    
    # 3. Hiển thị kết quả ra Log (Để anh xem ngay trên màn hình GitHub)
    print("--- KẾT QUẢ AI TRẢ LỜI ---")
    print(response.text)
    print("--------------------------")
    
    # 4. Ghi kết quả vào file
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Đã lưu kết quả vào file result.txt thành công.")

except Exception as e:
    # 5. Xử lý lỗi
    error_msg = f"LOI ROI: {str(e)}"
    print(error_msg)
    
    # Ghi lỗi vào file để anh kiểm tra
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(error_msg)
    
    sys.exit(1) # Dừng chương trình và báo lỗi cho GitHub Actions
