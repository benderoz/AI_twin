require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));

// Telegram Bot Configuration
const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// HeyGen API Configuration
const HEYGEN_API_KEY = process.env.HEYGEN_API_KEY;
const HEYGEN_API_URL = process.env.HEYGEN_API_URL;

// Store active sessions
const activeSessions = new Map();

// HeyGen API Functions
async function createHeyGenToken() {
  try {
    const response = await axios.post(`${HEYGEN_API_URL}/v1/streaming.create_token`, {}, {
      headers: {
        'X-Api-Key': HEYGEN_API_KEY,
        'Content-Type': 'application/json'
      }
    });
    return response.data.data.token;
  } catch (error) {
    console.error('Error creating HeyGen token:', error.response?.data || error.message);
    throw error;
  }
}

async function createStreamingSession(token, userId) {
  try {
    const response = await axios.post(`${HEYGEN_API_URL}/v1/streaming.new`, {
      quality: 'high',
      avatar_name: 'Wayne_20240711', // Default avatar
      voice: {
        voice_id: 'ec68fe1ddb6f4d5ba2d6a6b165f54a74',
        rate: 1.0,
        emotion: 'FRIENDLY'
      },
      version: 'v2',
      video_encoding: 'H264',
      language: 'ru',
      knowledge_base: 'Ты дружелюбный русскоговорящий ассистент. Отвечай коротко и по существу. Ты можешь помочь с любыми вопросами.'
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const sessionData = response.data.data;
    activeSessions.set(userId, {
      ...sessionData,
      token: token,
      startTime: new Date()
    });
    
    return sessionData;
  } catch (error) {
    console.error('Error creating streaming session:', error.response?.data || error.message);
    throw error;
  }
}

async function startStreamingSession(sessionId, token) {
  try {
    const response = await axios.post(`${HEYGEN_API_URL}/v1/streaming.start`, {
      session_id: sessionId
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error starting streaming session:', error.response?.data || error.message);
    throw error;
  }
}

async function stopStreamingSession(sessionId, token) {
  try {
    const response = await axios.post(`${HEYGEN_API_URL}/v1/streaming.stop`, {
      session_id: sessionId
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error stopping streaming session:', error.response?.data || error.message);
    throw error;
  }
}

// Telegram Bot Handlers
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  const webAppUrl = `${process.env.NODE_ENV === 'production' ? 'https' : 'http'}://localhost:${PORT}/webapp`;
  
  const opts = {
    reply_markup: {
      inline_keyboard: [
        [
          {
            text: '📹 Открыть видеозвонок с аватаром',
            web_app: { url: webAppUrl }
          }
        ]
      ]
    }
  };
  
  bot.sendMessage(chatId, 
    '🤖 Добро пожаловать в HeyGen Avatar Bot!\n\n' +
    'Нажмите кнопку ниже, чтобы начать видеозвонок с интерактивным аватаром. ' +
    'Вы сможете общаться голосом или текстом!', 
    opts
  );
});

bot.on('message', (msg) => {
  if (!msg.text || msg.text.startsWith('/')) return;
  
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 
    'Для начала общения с аватаром используйте команду /start и откройте веб-приложение!'
  );
});

// API Routes
app.post('/api/create-session', async (req, res) => {
  try {
    const { userId } = req.body;
    
    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }
    
    // Create token
    const token = await createHeyGenToken();
    
    // Create session
    const sessionData = await createStreamingSession(token, userId);
    
    // Start session
    await startStreamingSession(sessionData.session_id, token);
    
    res.json({
      success: true,
      sessionId: sessionData.session_id,
      token: token,
      url: sessionData.url,
      accessToken: sessionData.access_token
    });
  } catch (error) {
    console.error('API Error:', error);
    res.status(500).json({ 
      error: 'Failed to create session',
      message: error.message 
    });
  }
});

app.post('/api/send-message', async (req, res) => {
  try {
    const { sessionId, token, text, taskType = 'talk' } = req.body;
    
    if (!sessionId || !token || !text) {
      return res.status(400).json({ error: 'Missing required parameters' });
    }
    
    const response = await axios.post(`${HEYGEN_API_URL}/v1/streaming.task`, {
      session_id: sessionId,
      text: text,
      task_type: taskType
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    res.json({ success: true, data: response.data });
  } catch (error) {
    console.error('Send message error:', error);
    res.status(500).json({ 
      error: 'Failed to send message',
      message: error.message 
    });
  }
});

app.post('/api/close-session', async (req, res) => {
  try {
    const { sessionId, token, userId } = req.body;
    
    if (sessionId && token) {
      await stopStreamingSession(sessionId, token);
    }
    
    if (userId) {
      activeSessions.delete(userId);
    }
    
    res.json({ success: true });
  } catch (error) {
    console.error('Close session error:', error);
    res.status(500).json({ 
      error: 'Failed to close session',
      message: error.message 
    });
  }
});

// Serve Web App
app.get('/webapp', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'webapp.html'));
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    activeSessions: activeSessions.size
  });
});

// Cleanup inactive sessions every 10 minutes
setInterval(() => {
  const now = new Date();
  for (const [userId, session] of activeSessions) {
    const timeDiff = now - session.startTime;
    if (timeDiff > 30 * 60 * 1000) { // 30 minutes
      console.log(`Cleaning up inactive session for user ${userId}`);
      stopStreamingSession(session.session_id, session.token)
        .catch(err => console.error('Error cleaning up session:', err));
      activeSessions.delete(userId);
    }
  }
}, 10 * 60 * 1000);

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📱 Bot token: ${process.env.TELEGRAM_BOT_TOKEN ? 'Set' : 'Not set'}`);
  console.log(`🎭 HeyGen API key: ${HEYGEN_API_KEY ? 'Set' : 'Not set'}`);
});

module.exports = app;