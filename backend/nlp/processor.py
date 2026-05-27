import asyncio
import logging
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from kafka.consumer import KafkaConsumer
from kafka.producer import KafkaProducer
from db.database import AsyncSessionLocal
from db.models import SentimentScore
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.news_consumer = KafkaConsumer("raw-news")
        self.social_consumer = KafkaConsumer("raw-social")
        self.producer = KafkaProducer()

    async def start(self):
        await self.producer.start()
        logger.info("NLP Processor started. Listening for news and social data...")
        
        await asyncio.gather(
            self.process_stream(self.news_consumer, "news"),
            self.process_stream(self.social_consumer, "social")
        )

    def analyze_sentiment(self, text: str):
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        
        if compound >= 0.05:
            signal = "BUY"
        elif compound <= -0.05:
            signal = "SELL"
        else:
            signal = "HOLD"
            
        return compound, signal

    async def process_stream(self, consumer: KafkaConsumer, source_type: str):
        async for message in consumer.listen():
            try:
                ticker = message.get("ticker")
                # Combine title and description/text for analysis
                text_to_analyze = f"{message.get('title', '')} {message.get('description', '')} {message.get('selftext', '')}"
                
                score, signal = self.analyze_sentiment(text_to_analyze)
                
                # Prepare database record
                sentiment_record = SentimentScore(
                    ticker=ticker,
                    score=score,
                    signal=signal,
                    source=source_type,
                    headline=message.get("title", "No Title")
                )
                
                # Save to DB
                async with AsyncSessionLocal() as session:
                    session.add(sentiment_record)
                    await session.commit()
                
                # Publish to processed topic
                processed_message = {
                    "ticker": ticker,
                    "score": score,
                    "signal": signal,
                    "source": source_type,
                    "headline": message.get("title"),
                    "timestamp": message.get("publishedAt") or message.get("created_utc")
                }
                await self.producer.publish("sentiment-scores", processed_message)
                
                logger.debug(f"Processed {source_type} for {ticker}: {signal} ({score})")
                
            except Exception as e:
                logger.error(f"Error processing {source_type} message: {e}")

if __name__ == "__main__":
    processor = NLPProcessor()
    asyncio.run(processor.start())
