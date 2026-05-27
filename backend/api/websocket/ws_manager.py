from fastapi import WebSocket
from typing import List, Dict
import json

class ConnectionManager:
    def __init__(self):
        # ticker -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, ticker: str, websocket: WebSocket):
        await websocket.accept()
        ticker = ticker.upper()
        if ticker not in self.active_connections:
            self.active_connections[ticker] = []
        self.active_connections[ticker].append(websocket)

    def disconnect(self, ticker: str, websocket: WebSocket):
        ticker = ticker.upper()
        if ticker in self.active_connections:
            self.active_connections[ticker].remove(websocket)
            if not self.active_connections[ticker]:
                del self.active_connections[ticker]

    async def broadcast(self, ticker: str, data: dict):
        ticker = ticker.upper()
        if ticker in self.active_connections:
            for connection in self.active_connections[ticker]:
                try:
                    await connection.send_json(data)
                except Exception:
                    pass

manager = ConnectionManager()
