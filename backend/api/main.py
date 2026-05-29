import asyncio
import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import sentiment, prices, stream
from api.websocket import ws_routes
from api.websocket.ws_manager import manager
from kafka.consumer import KafkaConsumer
from db.database import engine
from db.models import Base
from db.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trade Sentiment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sentiment.router)
app.include_router(prices.router)
app.include_router(stream.router)
app.include_router(ws_routes.router)

@app.on_event("startup")
async def startup():
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start Kafka broadcast task
    asyncio.create_task(kafka_broadcast_task())

async def kafka_broadcast_task():
    # Listen to processed sentiment and price ticks
    consumer = KafkaConsumer(["sentiment-scores", "price-ticks"])
    logger.info("API Kafka Broadcast Task started.")
    
    async for message in consumer.listen():
        ticker = message.get("ticker")
        if ticker:
            # 1. Broadcast to all WS clients subscribed to this ticker
            await manager.broadcast(ticker, message)
            
            # 2. Publish to Redis pub/sub for SSE clients
            payload = json.dumps(message)
            await redis_client.publish(f"updates:{ticker}", payload)
            
            # 3. Cache last signal for instant hydration on new connections
            if "signal" in message:
                await redis_client.set(f"last_signal:{ticker}", payload, ex=3600)
