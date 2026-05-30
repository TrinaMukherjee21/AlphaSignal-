import asyncio
import logging
import os
from kafka.consumer import KafkaConsumer
from kafka.producer import KafkaProducer
from db.database import AsyncSessionLocal
from db.models import SentimentScore
from nlp.sentiment_model import SentimentModel
from nlp.signal_engine import SignalEngine
from datetime import datetime
from db.redis_client import redis_client
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPWorker:
    def __init__(self):
        self.consumer = KafkaConsumer(["raw-news", "raw-social"])
        self.producer = KafkaProducer()
        self.model = SentimentModel()
        self.signal_engine = SignalEngine()
        self.batch_size = 1

    async def start(self):
        await self.producer.start()
        await self.consumer.start()
        logger.info("NLP Worker started. Batch processing news and social streams...")
        
        batch_messages = []
        
        async for message in self.consumer.listen():
            batch_messages.append(message)
            
            if len(batch_messages) >= self.batch_size:
                await self.process_batch(batch_messages)
                batch_messages = []

    async def process_batch(self, messages: list[dict]):
        # Extract texts for scoring
        texts = []
        for msg in messages:
            # Combine text
            text = f"{msg.get('title', '')} {msg.get('description', '') or msg.get('selftext', '')}"
            texts.append(text)

        # Run sentiment scoring in a thread to avoid blocking the event loop
        scores = await asyncio.to_thread(self.model.score_batch, texts)

        # Process each message with its score
        for msg, score in zip(messages, scores):
            ticker = msg.get("ticker")
            
            # Use provided source, default to news if it's yahoo finance, else reddit if truly reddit
            original_source = msg.get("source", "news")
            # For backward compatibility, check if it's explicitly from a subreddit
            if "r/" in original_source or original_source == "reddit":
                source = "reddit"
            elif "description" in msg or "yahoo" in original_source.lower() or original_source != "reddit":
                source = original_source
            else:
                source = "reddit"
                
            weight = 0.6 if source == "reddit" else 1.0
            
            # Update signal engine
            self.signal_engine.add_score(ticker, score, weight)
            current_signal = self.signal_engine.get_signal(ticker)
            
            logger.info(f"SignalEngine updated for {ticker}: Score={score:.3f}, Weight={weight}, Current Signal={current_signal}")
            
            # Save to DB
            async with AsyncSessionLocal() as session:
                sentiment_record = SentimentScore(
                    ticker=ticker,
                    score=score,
                    signal=current_signal,
                    source=source,
                    headline=msg.get("title", "No Title")
                )
                session.add(sentiment_record)
                await session.commit()
            
            # Publish processed result for UI
            processed_msg = {
                "ticker": ticker,
                "score": score,
                "signal": current_signal,
                "source": source,
                "headline": msg.get("title"),
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.producer.publish("sentiment-scores", processed_msg)
            
            # Cache in Redis
            cache_key = f"sentiment:{ticker}"
            await redis_client.lpush(cache_key, json.dumps(processed_msg))
            await redis_client.ltrim(cache_key, 0, 49)
            
        logger.info(f"Processed batch of {len(messages)} messages.")

if __name__ == "__main__":
    worker = NLPWorker()
    asyncio.run(worker.start())
