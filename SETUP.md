# 🚀 Пошаговая настройка HeyGen Avatar Bot

## 📋 Что нужно подготовить

1. **HeyGen API ключ** - получите на [app.heygen.com](https://app.heygen.com/settings?nav=API)
2. **Telegram Bot Token** - создайте бота через [@BotFather](https://t.me/BotFather)
3. **Сервер с HTTPS** - для работы WebRTC (можно использовать ngrok для тестирования)

## 🎭 1. Настройка HeyGen

1. Зайдите на [app.heygen.com](https://app.heygen.com)
2. Перейдите в Settings → API
3. Скопируйте ваш API ключ
4. Перейдите в [Interactive Avatar](https://labs.heygen.com/interactive-avatar)
5. Выберите или создайте аватар
6. Запомните ID аватара (например: `Wayne_20240711`)

## 🤖 2. Создание Telegram бота

1. Напишите [@BotFather](https://t.me/BotFather)
2. Выполните команды:
   ```
   /newbot
   Введите название: HeyGen Avatar Bot
   Введите username: your_unique_bot_name
   ```
3. Скопируйте полученный токен
4. Настройте Web App:
   ```
   /setmenubutton
   Выберите вашего бота
   Введите URL: https://yourdomain.com/webapp
   Введите описание: Видеозвонок с AI
   ```

## 💻 3. Настройка проекта

1. **Клонируйте и установите:**
   ```bash
   git clone <your-repo>
   cd telegram-heygen-avatar-bot
   npm install
   ```

2. **Настройте переменные окружения:**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Заполните:
   ```env
   HEYGEN_API_KEY=ваш_heygen_api_ключ
   TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
   PORT=3000
   NODE_ENV=production
   ```

3. **Настройте аватар в server.js:**
   ```javascript
   // Найдите в server.js функцию createStreamingSession
   avatar_name: 'ваш_аватар_id',
   voice: {
     voice_id: 'ваш_голос_id',
     rate: 1.0,
     emotion: 'FRIENDLY'
   }
   ```

## 🌐 4. Развертывание

### Локальное тестирование (HTTP)
```bash
npm start
# Откройте http://localhost:3000/test.html для тестирования
```

### С ngrok (для тестирования в Telegram)
```bash
# Установите ngrok
npm install -g ngrok

# Запустите туннель
ngrok http 3000

# Обновите URL в @BotFather на полученный HTTPS адрес
```

### На VPS (production)
```bash
# Установите PM2
npm install -g pm2

# Настройте nginx
sudo nano /etc/nginx/sites-available/avatar-bot

# Конфигурация nginx:
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# Запустите с PM2
pm2 start server.js --name "avatar-bot"
pm2 save
pm2 startup
```

## 🧪 5. Тестирование

1. **Локальное тестирование:**
   - Откройте `http://localhost:3000/test.html`
   - Проверьте создание сессии и подключение к аватару

2. **Тестирование в Telegram:**
   - Напишите боту `/start`
   - Нажмите кнопку "Открыть видеозвонок с аватаром"
   - Протестируйте функции ответа на звонок и общения

## ⚠️ Возможные проблемы

### "Failed to create session"
- Проверьте HeyGen API ключ
- Убедитесь, что у вас достаточно кредитов
- Проверьте лимиты на concurrent sessions (обычно 3)

### WebRTC не работает
- Используйте HTTPS (обязательно для WebRTC)
- Проверьте права на микрофон в браузере
- Убедитесь, что порты не заблокированы

### Бот не отвечает
- Проверьте Telegram Bot Token
- Убедитесь, что URL в WebApp правильный
- Проверьте логи сервера

## 📊 Мониторинг

Проверить статус:
```bash
curl https://yourdomain.com/health
```

Логи PM2:
```bash
pm2 logs avatar-bot
```

## 🎨 Кастомизация

### Изменить приветствие аватара
В `server.js` найдите:
```javascript
knowledge_base: 'Ваш промпт для аватара'
```

### Изменить UI
Отредактируйте `public/styles.css` для изменения внешнего вида.

### Добавить новые функции
Расширьте API в `server.js` и клиентскую логику в `public/app.js`.

## 🔄 Обновления

Для обновления проекта:
```bash
git pull
npm install
pm2 restart avatar-bot
```

---

**🎉 Готово!** Ваш HeyGen Avatar Bot настроен и готов к работе!