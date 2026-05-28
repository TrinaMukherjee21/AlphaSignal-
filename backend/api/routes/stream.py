"""
SSE (Server-Sent Events) streaming endpoint.
Clients can subscribe to /api/stream/{ticker} for a persistent HTTP stream
instead of (or in addition to) WebSocket.
"""
import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from db.redis_client import redis_client

router = APIRouter(prefix="/api")

@router.get("/stream/{ticker}")
async def stream_ticker(ticker: str):
    """
    SSE endpoint. Forwards any new data from Redis pub/sub to the client.
    The Kafka consumer publishes updates to Redis channel `updates:{ticker}`.
    """
    ticker = ticker.upper()
    
    async def event_generator():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"updates:{ticker}")
        try:
            # Send the cached last signal immediately so client has instant context
            cached = await redis_client.get(f"last_signal:{ticker}")
            if cached:
                yield f"data: {cached}\n\n"

            # Stream new events as they arrive
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                await asyncio.sleep(0)
        finally:
            await pubsub.unsubscribe(f"updates:{ticker}")
            await pubsub.aclose()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
