import requests
from bs4 import BeautifulSoup

def scrape_website(url: str) -> str:
    """
    Truy cập một đường link website để đọc nội dung văn bản của bài báo hoặc trang web.
    Args:
        url: Đường link đầy đủ cần truy cập (ví dụ: https://vnexpress.net)
    """
    try:
        # Giả lập trình duyệt thật để tránh bị các trang báo chặn (Block bot)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Loại bỏ các thẻ thừa (script, style, menu...)
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        
        # Cắt bớt nội dung (6000 ký tự) để tránh làm tràn bộ nhớ AI (Context Window)
        return text[:6000]
    except Exception as e:
        return f"Lỗi khi cào web (có thể do trang web chặn truy cập): {str(e)}"