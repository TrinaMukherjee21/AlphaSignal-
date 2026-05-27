import asyncio
import logging
from datetime import datetime
from kafka.consumer import KafkaConsumer
from db.database import AsyncSessionLocal
from db.models import PriceTick

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceProcessor:
    def __init__(self):
        self.consumer = KafkaConsumer("price-ticks")

    async def start(self):
        logger.info("Price Processor started. Listening for price ticks...")
        async for message in self.consumer.listen():
            try:
                # Convert timestamp string back to datetime if needed
                ts_str = message.get("timestamp")
                ts = datetime.fromisoformat(ts_str) if ts_str else datetime.utcnow()
                
                price_record = PriceTick(
                    ticker=message.get("ticker"),
                    open=message.get("open"),
                    high=message.get("high"),
                    low=message.get("low"),
                    close=message.get("close"),
                    volume=message.get("volume"),
                    timestamp=ts
                )
                
                async with AsyncSessionLocal() as session:
                    session.add(price_record)
                    await session.commit()
                
                logger.debug(f"Saved price tick for {message.get('ticker')} at {ts}")
                
            except Exception as e:
                logger.error(f"Error processing price tick: {e}")

if __name__ == "__main__":
    processor = PriceProcessor()
    asyncio.run(processor.start())
