===== FILE: docs/CURRENT_SYSTEM_AUDIT.md =====

```markdown
# CURRENT SYSTEM AUDIT – my-ai-bot

**Date**: 2026-08-12  
**Repository**: https://github.com/nguyenxuandat20091985-rgb/my-ai-bot  
**Commits observed**: 59

## Structure (real)

```
ROOT
├── .github/workflows/main.yml
├── docs/               ← GitHub Pages source
├── tools/web_scraper.py
├── bot.py              ← CORE daily publisher
├── app.py              ← CORE Streamlit assistant
├── products.json       ← 3 products
├── requirements.txt
├── index.html + bai-*.html  ← currently written to ROOT
└── result.txt
```

## Core Files Classification

| File | Role | Status |
|------|------|--------|
| bot.py | Daily AI review + HTML + social | CORE – keep intact |
| app.py | Streamlit + scrape tool | CORE – keep intact |
| products.json | Product source | CORE – extend only |
| .github/workflows/main.yml | Cron 00:00 UTC + commit | CORE – keep |
| docs/ | GitHub Pages | CORE – must sync |

## Critical Issues Found

1. **Output path mismatch**: bot.py writes to ROOT, GitHub Pages is set to `/docs`.
2. Only 3 products → rapid rotation.
3. No fact-checking, scoring, anti-duplicate, SEO full tags, memory.
4. No AccessTrade integration.
5. Social content is generic.
6. App.py has only one tool.

## Data Flow (actual)

```
products.json → bot.py (toordinal % len) → litellm/Groq → HTML (root) + result.txt
→ Actions commit → Pages serves /docs (old files)
```

## AI Stack

- Provider: Groq via litellm
- Model: groq/llama-3.3-70b-versatile
- Temperature: 0.8
- No retry / no structured output

## Recommendation

Implement V1.0 as **CORE + EXTENSIONS** only.  
Never rewrite bot.py / app.py from scratch.
```

===== END FILE =====
