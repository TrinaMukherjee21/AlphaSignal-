import os
import asyncio
import logging
from dotenv import load_dotenv
from kafka.producer import KafkaProducer
from scrapers.news_scraper import news_scraper_loop
from scrapers.reddit_scraper import reddit_scraper_loop
from scrapers.price_scraper import price_scraper_loop

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TICKERS = os.getenv("TICKERS", "AAPL,TSLA,NVDA,MSFT,AMZN").split(",")

async def main():
    logger.info(f"Starting scrapers for tickers: {TICKERS}")
    
    producer = KafkaProducer()
    await producer.start()
    
    try:
        await asyncio.gather(
            news_scraper_loop(TICKERS, producer),
            reddit_scraper_loop(TICKERS, producer),
            price_scraper_loop(TICKERS, producer)
        )
    except Exception as e:
        logger.error(f"Scrapers encountered an error: {e}")
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
