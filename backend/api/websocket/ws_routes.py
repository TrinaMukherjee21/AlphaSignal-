from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websocket.ws_manager import manager
from db.redis_client import redis_client
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{ticker}")
async def websocket_endpoint(websocket: WebSocket, ticker: str):
    ticker = ticker.upper()
    await manager.connect(ticker, websocket)
    
    try:
        # 1. Send last 10 cached events from Redis
        cache_key = f"sentiment:{ticker}"
        cached_events = await redis_client.lrange(cache_key, 0, 9)
        if cached_events:
            for event_json in reversed(cached_events):
                await websocket.send_json(json.loads(event_json))
        
        # 2. Keep connection alive and listen for any client messages
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(ticker, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {ticker}: {e}")
        manager.disconnect(ticker, websocket)
