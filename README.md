# Telegram HeyGen Avatar Bot

Веб-приложение для Telegram бота с интерактивным аватаром от HeyGen. Имитирует видеозвонок с AI ассистентом, который может общаться голосом и текстом.

## ✨ Возможности

- 🎭 **Интерактивный аватар HeyGen** с реалистичной мимикой и голосом
- 📹 **Имитация видеозвонка** в стиле мессенджеров
- 🎤 **Голосовое общение** с записью и распознаванием речи
- 💬 **Текстовые сообщения** для быстрого общения
- 🌐 **WebRTC потоковое видео** с низкой задержкой
- 📱 **Полная интеграция с Telegram WebApp**
- 🎨 **Современный UI/UX** с плавными анимациями

## 🛠️ Технологии

- **Backend**: Node.js, Express.js
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Video Streaming**: LiveKit WebRTC
- **Avatar Service**: HeyGen Streaming API
- **Bot Framework**: Telegram Bot API
- **UI**: Responsive design с градиентами и анимациями

## 📋 Требования

- Node.js 16+ 
- HeyGen API ключ
- Telegram Bot Token
- HTTPS для продакшена (для WebRTC)

## 🚀 Установка

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd telegram-heygen-avatar-bot
```

2. **Установите зависимости**
```bash
npm install
```

3. **Настройте переменные окружения**
```bash
cp .env.example .env
```

Отредактируйте файл `.env`:
```env
# HeyGen API Configuration
HEYGEN_API_KEY=your_heygen_api_key_here

# Telegram Bot Configuration  
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Server Configuration
PORT=3000
NODE_ENV=development

# HeyGen API URLs
HEYGEN_API_URL=https://api.heygen.com
```

4. **Запустите сервер**
```bash
# Для разработки
npm run dev

# Для продакшена
npm start
```

## ⚙️ Настройка Telegram бота

1. **Создайте бота через @BotFather**
2. **Получите Token** и добавьте в `.env`
3. **Настройте Web App URL** в BotFather:
   ```
   /setmenubutton
   -> Выберите вашего бота
   -> Введите URL: https://yourdomain.com/webapp
   ```

## 🎭 Настройка HeyGen

1. **Получите API ключ** в панели HeyGen
2. **Выберите аватар** из доступных или создайте собственный
3. **Настройте голос** в `server.js`:
```javascript
avatar_name: 'Wayne_20240711', // ID вашего аватара
voice: {
  voice_id: 'your_voice_id',
  rate: 1.0,
  emotion: 'FRIENDLY'
}
```

## 📱 Использование

1. **Запустите бота** командой `/start`
2. **Нажмите кнопку** "Открыть видеозвонок с аватаром"
3. **Дождитесь загрузки** - появится экран входящего звонка
4. **Ответьте на звонок** - начнется сессия с аватаром
5. **Общайтесь** через текст или голос

## 🏗️ Архитектура

```
├── server.js              # Основной сервер
├── public/
│   ├── webapp.html         # Веб-приложение
│   ├── styles.css          # Стили
│   └── app.js             # Клиентская логика
├── .env                   # Конфигурация
└── package.json           # Зависимости
```

## 🔧 API Endpoints

- `POST /api/create-session` - Создание сессии HeyGen
- `POST /api/send-message` - Отправка сообщения аватару  
- `POST /api/close-session` - Закрытие сессии
- `GET /webapp` - Веб-приложение
- `GET /health` - Проверка здоровья сервиса

## 🎨 Кастомизация

### Изменение аватара
```javascript
// В server.js
avatar_name: 'ваш_аватар_id'
```

### Настройка голоса
```javascript
voice: {
  voice_id: 'ваш_голос_id',
  rate: 1.2,           // Скорость речи
  emotion: 'EXCITED'   // Эмоция
}
```

### Персонализация промпта
```javascript
knowledge_base: 'Ваш промпт для аватара'
```

## 🐛 Отладка

**Проблемы с подключением:**
```bash
# Проверьте статус сервера
curl http://localhost:3000/health

# Проверьте логи
npm run dev
```

**Ошибки HeyGen API:**
- Проверьте API ключ в `.env`
- Убедитесь что у вас есть активная подписка
- Проверьте лимиты на сессии

**Проблемы с WebRTC:**
- Для тестирования используйте HTTPS
- Проверьте права на микрофон в браузере

## 📊 Мониторинг

Сервер предоставляет endpoint для мониторинга:
```bash
GET /health
```

Ответ:
```json
{
  "status": "OK",
  "timestamp": "2024-01-15T10:30:00.000Z", 
  "activeSessions": 2
}
```

## 🚀 Развертывание

### На VPS/Cloud
1. Установите SSL сертификат (Let's Encrypt)
2. Настройте nginx как прокси
3. Используйте PM2 для управления процессом
4. Обновите URL в Telegram WebApp

### Docker
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

## 📄 Лицензия

MIT License

## 🤝 Поддержка

Если у вас есть вопросы или предложения, создайте Issue в репозитории.

## 🔄 Обновления

- **v1.0.0** - Базовая функциональность
- Поддержка голосового общения
- Интеграция с HeyGen Streaming API
- Telegram WebApp интерфейс