// Global variables
let tg = window.Telegram?.WebApp;
let currentSession = null;
let room = null;
let mediaStream = null;
let webSocket = null;
let callStartTime = null;
let callTimer = null;
let isRecording = false;
let mediaRecorder = null;
let recordedChunks = [];

// Initialize Telegram Web App
if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#000000');
    tg.setBackgroundColor('#000000');
}

// Screen management
const screens = {
    loading: document.getElementById('loading-screen'),
    call: document.getElementById('call-screen'),
    video: document.getElementById('video-screen'),
    error: document.getElementById('error-screen')
};

// UI Elements
const elements = {
    progressFill: document.getElementById('progress-fill'),
    loadingStatus: document.getElementById('loading-status'),
    answerBtn: document.getElementById('answer-btn'),
    declineBtn: document.getElementById('decline-btn'),
    avatarVideo: document.getElementById('avatar-video'),
    connectionStatus: document.getElementById('connection-status'),
    callDuration: document.getElementById('call-duration'),
    messageInput: document.getElementById('message-input'),
    sendBtn: document.getElementById('send-btn'),
    micBtn: document.getElementById('mic-btn'),
    endCallBtn: document.getElementById('end-call-btn'),
    errorMessage: document.getElementById('error-message'),
    retryBtn: document.getElementById('retry-btn'),
    ringtone: document.getElementById('ringtone')
};

// Utility functions
function showScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[screenName].classList.add('active');
}

function updateLoadingStatus(status, progress = null) {
    elements.loadingStatus.textContent = status;
    if (progress !== null) {
        elements.progressFill.style.width = `${progress}%`;
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function startCallTimer() {
    callStartTime = Date.now();
    callTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
        elements.callDuration.textContent = formatTime(elapsed);
    }, 1000);
}

function stopCallTimer() {
    if (callTimer) {
        clearInterval(callTimer);
        callTimer = null;
    }
}

function updateConnectionStatus(status) {
    elements.connectionStatus.style.color = status === 'connected' ? '#27ae60' : '#e74c3c';
}

// API functions
async function createSession() {
    try {
        const userId = tg?.initDataUnsafe?.user?.id || Math.random().toString(36).substr(2, 9);
        
        const response = await fetch('/api/create-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ userId })
        });

        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to create session');
        }

        currentSession = {
            sessionId: data.sessionId,
            token: data.token,
            url: data.url,
            accessToken: data.accessToken,
            userId: userId
        };

        return currentSession;
    } catch (error) {
        console.error('Error creating session:', error);
        throw error;
    }
}

async function sendMessage(text, taskType = 'talk') {
    if (!currentSession) {
        throw new Error('No active session');
    }

    try {
        const response = await fetch('/api/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sessionId: currentSession.sessionId,
                token: currentSession.token,
                text: text,
                taskType: taskType
            })
        });

        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to send message');
        }

        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
}

async function closeSession() {
    if (!currentSession) return;

    try {
        await fetch('/api/close-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sessionId: currentSession.sessionId,
                token: currentSession.token,
                userId: currentSession.userId
            })
        });
    } catch (error) {
        console.error('Error closing session:', error);
    }

    // Close WebSocket
    if (webSocket) {
        webSocket.close();
        webSocket = null;
    }

    // Disconnect from LiveKit room
    if (room) {
        room.disconnect();
        room = null;
    }

    // Clean up media
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }

    elements.avatarVideo.srcObject = null;
    currentSession = null;
    stopCallTimer();
    updateConnectionStatus('disconnected');
}

// WebRTC and LiveKit functions
async function setupLiveKitConnection() {
    if (!currentSession) {
        throw new Error('No session available');
    }

    try {
        // Create LiveKit Room
        room = new LiveKitClient.Room({
            adaptiveStream: true,
            dynacast: true,
            videoCaptureDefaults: {
                resolution: LiveKitClient.VideoPresets.h720.resolution,
            },
        });

        // Handle room events
        room.on(LiveKitClient.RoomEvent.DataReceived, (message) => {
            try {
                const data = new TextDecoder().decode(message);
                const eventData = JSON.parse(data);
                console.log('Room message:', eventData);
                handleAvatarEvent(eventData);
            } catch (error) {
                console.error('Error parsing room message:', error);
            }
        });

        // Handle media streams
        mediaStream = new MediaStream();
        
        room.on(LiveKitClient.RoomEvent.TrackSubscribed, (track) => {
            console.log('Track subscribed:', track.kind);
            if (track.kind === 'video' || track.kind === 'audio') {
                mediaStream.addTrack(track.mediaStreamTrack);
                
                // Update video element when we have both audio and video
                if (mediaStream.getVideoTracks().length > 0 && mediaStream.getAudioTracks().length > 0) {
                    elements.avatarVideo.srcObject = mediaStream;
                    updateConnectionStatus('connected');
                    updateLoadingStatus('Подключено!', 100);
                }
            }
        });

        room.on(LiveKitClient.RoomEvent.TrackUnsubscribed, (track) => {
            const mediaTrack = track.mediaStreamTrack;
            if (mediaTrack && mediaStream) {
                mediaStream.removeTrack(mediaTrack);
            }
        });

        room.on(LiveKitClient.RoomEvent.Connected, () => {
            console.log('Connected to LiveKit room');
            updateConnectionStatus('connected');
        });

        room.on(LiveKitClient.RoomEvent.Disconnected, (reason) => {
            console.log('Disconnected from room:', reason);
            updateConnectionStatus('disconnected');
        });

        // Prepare connection
        await room.prepareConnection(currentSession.url, currentSession.accessToken);
        updateLoadingStatus('Подготовка соединения...', 60);
        
        // Connect to room
        await room.connect(currentSession.url, currentSession.accessToken);
        updateLoadingStatus('Подключение к аватару...', 80);
        
        return true;
    } catch (error) {
        console.error('Error setting up LiveKit connection:', error);
        throw error;
    }
}

function handleAvatarEvent(eventData) {
    switch (eventData.type) {
        case 'avatar_start_talking':
            console.log('Avatar started talking');
            break;
        case 'avatar_stop_talking':
            console.log('Avatar stopped talking');
            break;
        case 'stream_ready':
            console.log('Stream ready');
            updateConnectionStatus('connected');
            break;
        default:
            console.log('Unhandled avatar event:', eventData);
    }
}

// Audio recording functions
async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        
        recordedChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
            await processVoiceMessage(audioBlob);
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        isRecording = true;
        elements.micBtn.classList.add('recording');
        
        console.log('Voice recording started');
    } catch (error) {
        console.error('Error starting voice recording:', error);
        showError('Не удалось получить доступ к микрофону');
    }
}

function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        elements.micBtn.classList.remove('recording');
        console.log('Voice recording stopped');
    }
}

async function processVoiceMessage(audioBlob) {
    try {
        // For now, we'll show a message that voice is being processed
        // In a real implementation, you would send this to a speech-to-text service
        console.log('Processing voice message...', audioBlob);
        
        // Placeholder: convert to text and send
        const placeholderText = "Привет! Это сообщение было отправлено голосом.";
        await sendMessage(placeholderText);
        
    } catch (error) {
        console.error('Error processing voice message:', error);
    }
}

// Event handlers
function handleAnswerCall() {
    elements.ringtone.pause();
    elements.ringtone.currentTime = 0;
    
    showScreen('video');
    startCallTimer();
    
    // Send initial greeting
    setTimeout(() => {
        sendMessage('Привет! Как дела?').catch(console.error);
    }, 1000);
}

function handleDeclineCall() {
    elements.ringtone.pause();
    elements.ringtone.currentTime = 0;
    
    closeSession().then(() => {
        if (tg) {
            tg.close();
        } else {
            showScreen('loading');
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    });
}

function handleSendMessage() {
    const text = elements.messageInput.value.trim();
    if (!text) return;
    
    elements.messageInput.value = '';
    elements.sendBtn.classList.add('loading');
    
    sendMessage(text)
        .then(() => {
            elements.sendBtn.classList.remove('loading');
        })
        .catch(error => {
            console.error('Error sending message:', error);
            elements.sendBtn.classList.remove('loading');
            showError('Не удалось отправить сообщение');
        });
}

function handleMicClick() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

function handleEndCall() {
    closeSession().then(() => {
        if (tg) {
            tg.close();
        } else {
            showScreen('loading');
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    });
}

function showError(message) {
    elements.errorMessage.textContent = message;
    showScreen('error');
}

// Initialization
async function initialize() {
    try {
        updateLoadingStatus('Инициализация...', 10);
        
        // Create session
        updateLoadingStatus('Создание сессии...', 30);
        await createSession();
        
        // Setup LiveKit connection
        updateLoadingStatus('Настройка WebRTC...', 50);
        await setupLiveKitConnection();
        
        // Session is ready
        updateLoadingStatus('Готово!', 100);
        
        // Wait a moment then show call screen
        setTimeout(() => {
            showScreen('call');
            
            // Start ringtone
            elements.ringtone.play().catch(error => {
                console.log('Could not play ringtone:', error);
            });
            
        }, 1000);
        
    } catch (error) {
        console.error('Initialization error:', error);
        showError(error.message || 'Ошибка инициализации');
    }
}

// Event listeners
elements.answerBtn.addEventListener('click', handleAnswerCall);
elements.declineBtn.addEventListener('click', handleDeclineCall);
elements.sendBtn.addEventListener('click', handleSendMessage);
elements.micBtn.addEventListener('click', handleMicClick);
elements.endCallBtn.addEventListener('click', handleEndCall);
elements.retryBtn.addEventListener('click', () => {
    showScreen('loading');
    initialize();
});

// Handle Enter key in message input
elements.messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSendMessage();
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden && currentSession) {
        // App hidden - pause operations if needed
        console.log('App hidden');
    } else if (currentSession) {
        // App visible - resume operations
        console.log('App visible');
    }
});

// Handle beforeunload
window.addEventListener('beforeunload', () => {
    closeSession();
});

// Telegram Web App specific handlers
if (tg) {
    tg.onEvent('mainButtonClicked', () => {
        // Handle main button if needed
    });
    
    tg.onEvent('backButtonClicked', () => {
        handleEndCall();
    });
}

// Start the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('App loaded, initializing...');
    initialize();
});

// Auto-resize based on Telegram viewport
function adjustViewport() {
    if (tg) {
        const viewportHeight = tg.viewportHeight || window.innerHeight;
        document.documentElement.style.setProperty('--tg-viewport-height', `${viewportHeight}px`);
    }
}

if (tg) {
    tg.onEvent('viewportChanged', adjustViewport);
    adjustViewport();
}

// Error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    if (!currentSession) {
        showError('Произошла ошибка при загрузке приложения');
    }
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});