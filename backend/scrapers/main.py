import os
import asyncio
import logging
from dotenv import load_dotenv
from kafka.producer import KafkaProducer
from scrapers.news_scraper import news_scraper_loop
from scrapers.reddit_scraper import reddit_scraper_loop
from scrapers.price_scraper import price_scraper_loop
from scrapers.gdelt_scraper import gdelt_scraper_loop
from scrapers.stocktwits_scraper import stocktwits_scraper_loop

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    tickers = [t.strip().upper() for t in os.getenv("TICKERS", "AAPL,TSLA,RELIANCE.NS,TCS.NS").split(",")]
    logger.info(f"Starting scrapers engine for tickers: {tickers}")
    
    producer = KafkaProducer()
    await producer.start()
    
    try:
        await asyncio.gather(
            news_scraper_loop(tickers, producer),
            reddit_scraper_loop(tickers, producer),
            price_scraper_loop(producer),       # price scraper reads tickers from Redis dynamically
            gdelt_scraper_loop(tickers, producer),
            stocktwits_scraper_loop(tickers, producer),
        )
    except Exception as e:
        logger.error(f"Scrapers encountered an error: {e}")
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
