## Telegram Finance Buddy (MVP)

Групповой бот для учёта трат на категории (alcohol, smokes, fun, restaurants) с остроумными ответами от Gemini и (позже) простыми картинками.

### Быстрый старт (локально, polling)
1) Установите Python 3.11+
2) Скопируйте `.env.example` в `.env` и заполните значения
3) Установите зависимости:
```bash
pip install -r requirements.txt
```
4) Запуск:
```bash
python -m app.main
```

### Переменные окружения
- TELEGRAM_BOT_TOKEN — токен от BotFather
- GEMINI_API_KEY — ключ Gemini (Google AI Studio)
- DATABASE_URL — строка подключения Postgres (Supabase/любая)
- APP_TZ — часовой пояс для отчётов, по умолчанию Europe/Moscow
- RUN_MODE — `polling` или `webhook`
- PUBLIC_URL — публичный URL приложения (только для `webhook`)

### Что дальше
- Добавить БД и CRUD
- Разбор сообщений и команды (/week, /month, /all, /stats, /undo)
- Подключить Gemini для шуток
- Генерация простых картинок-коллажей