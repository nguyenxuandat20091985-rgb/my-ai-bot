"""
Central configuration for MY AI AFFILIATE AGENT V1.0
SAFE MODE = ON by default.
"""

import os
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"          # GitHub Pages target
PRODUCTS_JSON = BASE_DIR / "products.json"
CONTENT_HISTORY = DATA_DIR / "content_history.json"
PRODUCT_CACHE = DATA_DIR / "product_cache.json"
MEMORY_DB = DATA_DIR / "memory.db"

# Ensure data dir exists
DATA_DIR.mkdir(exist_ok=True)

# ============================================================
# AI
# ============================================================
MODEL = os.getenv("AI_MODEL", "groq/llama-3.3-70b-versatile")
TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "4096"))

# ============================================================
# SAFE MODE (default ON)
# ============================================================
SAFE_MODE = os.getenv("SAFE_MODE", "true").lower() in ("1", "true", "yes", "on")
AUTO_PUBLISH = os.getenv("AUTO_PUBLISH", "false").lower() in ("1", "true", "yes", "on")

# Quality thresholds (0-100)
MIN_FACT_SCORE = int(os.getenv("MIN_FACT_SCORE", "70"))
MIN_QUALITY_SCORE = int(os.getenv("MIN_QUALITY_SCORE", "65"))
MIN_SEO_SCORE = int(os.getenv("MIN_SEO_SCORE", "60"))
MIN_SAFETY_SCORE = int(os.getenv("MIN_SAFETY_SCORE", "80"))

# ============================================================
# ACCESSTRADE
# ============================================================
ACCESSTRADE_API_TOKEN = os.getenv("ACCESSTRADE_API_TOKEN", "")
ACCESSTRADE_CAMPAIGN_ID = os.getenv("ACCESSTRADE_CAMPAIGN_ID", "")
ACCESSTRADE_BASE_URL = os.getenv("ACCESSTRADE_BASE_URL", "https://api.accesstrade.vn")
# ============================================================
# SCORING WEIGHTS (configurable)
# ============================================================
SCORING_WEIGHTS = {
    "deal": 0.30,          # discount %
    "rating": 0.20,
    "review_count": 0.15,
    "commission": 0.15,
    "audience_fit": 0.10,
    "content_potential": 0.10,
}

# ============================================================
# BLOG / SEO
# ============================================================
BLOG_URL = os.getenv("BLOG_URL", "https://nguyenxuandat20091985-rgb.github.io/my-ai-bot")
SITE_NAME = "Góc Bếp Thông Minh – Săn Deal"
SITE_DESCRIPTION = "Review đồ gia dụng & deal thật lòng mỗi ngày"

# ============================================================
# FEATURE FLAGS
# ============================================================
ENABLE_ACCESSTRADE = bool(ACCESSTRADE_API_KEY and ACCESSTRADE_API_TOKEN)
ENABLE_IMAGE_GEN = os.getenv("ENABLE_IMAGE_GEN", "false").lower() in ("1", "true", "yes")
ENABLE_SOCIAL_PUBLISH = os.getenv("ENABLE_SOCIAL_PUBLISH", "false").lower() in ("1", "true", "yes")

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")