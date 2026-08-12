# CORE PROTECTION RULES

## Absolute Rules

1. **Never delete** bot.py, app.py, products.json, .github/workflows/main.yml
2. **Never force-push** or rewrite git history
3. **Never change** the original daily selection logic (toordinal % len) unless explicitly requested
4. **Always keep** a working fallback path that produces HTML + result.txt every day
5. **New modules** live under `modules/` only
6. **bot_v1.py** is the new orchestrator – original bot.py stays as pure Core until you decide to swap
7. GitHub Actions continues to call `python bot.py` until you change the workflow yourself
8. Secrets never committed

## How to activate V1.0 safely

Option A (recommended first):
```bash
# Test locally
python bot_v1.py