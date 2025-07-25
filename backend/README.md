# Backend для Telegram HeyGen WebApp

## Запуск

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Переменные окружения
- HEYGEN_API_KEY — ваш API-ключ HeyGen (см. .env)