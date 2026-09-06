# GPU Flip Finder

AI-assisted GPU flipping deal discovery with Scrapling.

## Run
```bash
cp .env.example .env
pip install -U ".[main]"
scrapling install
uvicorn app:app --reload
```

## Endpoints
- GET /health
- GET /deals

## Telegram
Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USER_IDS` in `.env`, then run bot entrypoint separately.
