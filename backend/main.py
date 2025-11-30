from fastapi import FastAPI, WebSocket
from core.handler.ws_handler import WSHandler
from core.Amadeus import BaseAmadeus
import uvicorn
import logging
import colorlog

app = FastAPI()

# 日志配置，只需在主文件配置一次即可
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s %(levelname)s [%(pathname)s] %(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

ws_handler = WSHandler()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 为每个连接创建一个独立的 Amadeus 实例，确保用户隔离
    Amadeus = BaseAmadeus()
    await ws_handler.handle_ws(websocket, Amadeus)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        ws_ping_interval=300,  # 设置心跳间隔为 300 秒
        ws_ping_timeout=300    # 设置心跳超时为 300 秒
    )
    # uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4