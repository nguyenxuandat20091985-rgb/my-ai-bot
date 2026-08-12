"""
Content Engine
Generates multiple formats from product data.
Style: natural Vietnamese, useful, no fake personal experience, no fake scarcity.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from litellm import completion

from .config import MODEL, TEMPERATURE, MAX_TOKENS, BLOG_URL

logger = logging.getLogger(__name__)


def _ai(prompt: str, temperature: float = None) -> str:
    """Thin wrapper around litellm. Keeps same provider as Core."""
    try:
        resp = completion(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature if temperature is not None else TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        raise


def build_base_context(product: Dict[str, Any]) -> str:
    """Shared factual context for all generators."""
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
    """
    \~500-700 từ review.
    Structure required:
    HOOK → PROBLEM → PRODUCT → FACTS → PROS → CONS → WHO SHOULD BUY → WHO SHOULD NOT → CTA + DISCLOSURE
    """
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
  1. Hook mở đầu
  2. Nhu cầu / vấn đề người dùng thường gặp
  3. Giới thiệu sản phẩm (dựa trên dữ liệu)
  4. Các điểm mạnh thực tế
  5. Điểm cần lưu ý (nếu có)
  6. Ai nên mua / ai chưa nên mua
  7. CTA rõ ràng + nhắc người đọc tự kiểm tra giá hiện tại
  8. Cuối bài ghi: "Bài viết có chứa link affiliate. Người viết có thể nhận hoa hồng nếu bạn mua qua link."
- Mỗi đoạn cách nhau một dòng trống.
- Không dùng markdown heading (#).
"""
    raw = _ai(prompt, temperature=0.75)
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    title = lines[0].lstrip("#* ").strip() if lines else product.get("name", "Review")
    body = "\n\n".join(lines[1:]) if len(lines) > 1 else raw
    return {"title": title, "body": body, "type": "long_review"}


def generate_social_posts(product: Dict[str, Any], n: int = 3) -> str:
    """3 short posts separated by ---"""
    ctx = build_base_context(product)
    link = product.get("affiliate_url") or product.get("link") or ""
    prompt = f"""Dựa trên thông tin sản phẩm sau, viết {n} bài đăng mạng xã hội tiếng Việt ngắn (dưới 8 câu mỗi bài).
Mỗi bài có emoji vui, có CTA, và luôn kèm link.

THÔNG TIN:
{ctx}

YÊU CẦU:
- Phân cách các bài bằng đúng một dòng chứa ---
- Không bịa thông tin.
- Không dùng từ "tôi đã dùng", "tôi review thật".
- Tập trung lợi ích + CTA.
"""
    return _ai(prompt, temperature=0.8)


def generate_seo_meta(product: Dict[str, Any], title: str) -> Dict[str, str]:
    """Title + meta description + keywords."""
    name = product.get("name", "")
    prompt = f"""Viết meta SEO tiếng Việt cho bài review sản phẩm "{name}".
Tiêu đề bài: {title}

Trả về đúng 3 dòng:
1. SEO title (≤60 ký tự)
2. Meta description (≤155 ký tự)
3. Keywords (5-8 từ, cách nhau dấu phẩy)
"""
    raw = _ai(prompt, temperature=0.5)
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    return {
        "seo_title": lines[0] if lines else title[:60],
        "meta_description": lines[1] if len(lines) > 1 else f"Review {name} chi tiết, ưu nhược điểm và deal hiện tại.",
        "keywords": lines[2] if len(lines) > 2 else name,
    }


def generate_faq(product: Dict[str, Any], n: int = 5) -> str:
    ctx = build_base_context(product)
    prompt = f"""Dựa trên dữ liệu sản phẩm, viết {n} câu hỏi thường gặp (FAQ) và câu trả lời ngắn gọn, trung thực.
Không bịa thông tin.

{ctx}

Định dạng:
Q: ...
A: ...
"""
    return _ai(prompt, temperature=0.6)