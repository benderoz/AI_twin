from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Разрешаем CORS для фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

# Заготовка для WebSocket-прокси HeyGen (будет доработано)
@app.websocket("/ws/heygen")
async def heygen_ws_proxy(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Здесь будет логика проксирования к HeyGen
            await websocket.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        pass