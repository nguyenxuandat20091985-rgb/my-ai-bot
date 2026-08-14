"""
Content Engine – Prompt tối ưu + retry khi rate limit Groq
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any
from litellm import completion

from .config import MODEL, TEMPERATURE, MAX_TOKENS

logger = logging.getLogger(__name__)


def _ai(prompt: str, temperature: float = None, max_retries: int = 3) -> str:
    """Gọi AI, tự đợi & thử lại nếu bị rate limit."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = completion(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature if temperature is not None else TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if "ratelimit" in err_str or "rate_limit" in err_str or "tokens per minute" in err_str:
                wait = 25 * attempt  # 25s, 50s, 75s
                logger.warning(f"Rate limit – đợi {wait}s rồi thử lại ({attempt}/{max_retries})")
                time.sleep(wait)
                continue
            logger.error(f"AI call failed: {e}")
            raise
    logger.error(f"AI call failed after {max_retries} retries: {last_err}")
    raise last_err


def build_base_context(product: Dict[str, Any]) -> str:
    pros = product.get("pros") or []
    cons = product.get("cons") or []
    highlights = product.get("highlights") or ", ".join(pros)

    lines = [
        f"Tên sản phẩm: {product.get('name')}",
        f"Điểm mạnh (từ dữ liệu): {highlights}",
        f"Đối tượng phù hợp: {product.get('audience') or 'người dùng phổ thông'}",
    ]
    if product.get("price"):
        lines.append(f"Giá hiện tại (nếu có): {product.get('price')}")
    if product.get("discount"):
        lines.append(f"Mức giảm (nếu có): {product.get('discount')}%")
    if product.get("rating"):
        lines.append(f"Đánh giá: {product.get('rating')}/5")
    if cons:
        lines.append(f"Điểm cần lưu ý: {', '.join(cons)}")
    lines.append(f"Link: {product.get('affiliate_url') or product.get('link')}")
    return "\n".join(lines)


def generate_long_review(product: Dict[str, Any]) -> Dict[str, str]:
    ctx = build_base_context(product)
    prompt = f"""Bạn là biên tập viên review đồ gia dụng tiếng Việt, văn phong thật thà, gần gũi, hữu ích.
KHÔNG giả vờ đã dùng sản phẩm.
KHÔNG bịa giá, rating, voucher, bảo hành, thời gian giao hàng.
Chỉ dùng thông tin được cung cấp dưới đây.

THÔNG TIN SẢN PHẨM:
{ctx}

YÊU CẦU:
- Dòng ĐẦU TIÊN: tiêu đề giật gân, tự nhiên (không dùng # *).
- Sau đó viết bài khoảng 500-650 từ.
- Cấu trúc bắt buộc:
  1. Hook mở đầu (gợi nhu cầu thật)
  2. Nhu cầu / vấn đề người dùng thường gặp
  3. Giới thiệu sản phẩm (dựa trên dữ liệu)
  4. Các điểm mạnh thực tế
  5. Điểm cần lưu ý (nếu có, nếu không thì bỏ qua)
  6. Ai nên mua / ai chưa nên mua
  7. CTA rõ ràng + nhắc tự kiểm tra giá hiện tại
  8. Cuối bài ghi đúng câu: "Bài viết có chứa link affiliate. Người viết có thể nhận hoa hồng nếu bạn mua qua link."
- Mỗi đoạn cách nhau một dòng trống.
- Không dùng markdown heading (#).
- Không dùng từ "tôi đã dùng", "tôi review thật".
"""
    raw = _ai(prompt, temperature=0.75)
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    title = lines[0].lstrip("#* ").strip() if lines else product.get("name", "Review")
    body = "\n\n".join(lines[1:]) if len(lines) > 1 else raw
    return {"title": title, "body": body, "type": "long_review"}


def generate_social_posts(product: Dict[str, Any], n: int = 3) -> str:
    ctx = build_base_context(product)
    link = product.get("affiliate_url") or product.get("link") or ""
    prompt = f"""Dựa trên thông tin sản phẩm sau, viết {n} bài đăng Facebook tiếng Việt ngắn (dưới 8 câu mỗi bài).
Mỗi bài: có emoji vui, có CTA rõ, luôn kèm link ở cuối.

THÔNG TIN:
{ctx}

YÊU CẦU:
- Phân cách các bài bằng đúng một dòng chỉ có ---
- Không bịa thông tin.
- Không dùng "tôi đã dùng", "tôi review thật".
- Tập trung lợi ích + CTA.
- Mỗi bài kết thúc bằng link: {link}
"""
    return _ai(prompt, temperature=0.8, max_retries=3)


def generate_seo_meta(product: Dict[str, Any], title: str) -> Dict[str, str]:
    name = product.get("name", "")
    prompt = f"""Viết meta SEO tiếng Việt cho bài review sản phẩm "{name}".
Tiêu đề bài: {title}

Trả về đúng 3 dòng:
1. SEO title (≤60 ký tự)
2. Meta description (≤155 ký tự)
3. Keywords (5-8 từ, cách nhau dấu phẩy)
"""
    raw = _ai(prompt, temperature=0.5, max_retries=3)
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    return {
        "seo_title": lines[0] if lines else title[:60],
        "meta_description": lines[1] if len(lines) > 1 else f"Review {name} chi tiết, ưu nhược điểm và deal hiện tại.",
        "keywords": lines[2] if len(lines) > 2 else name,
    }