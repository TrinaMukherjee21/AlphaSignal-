import os
import asyncio
import httpx
import logging
from dotenv import load_dotenv
from kafka.producer import KafkaProducer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "").strip()
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Track last seen article publishedAt per ticker to avoid reprocessing
last_seen_at: dict = {}

async def fetch_news_for_ticker(ticker: str, client: httpx.AsyncClient):
    try:
        # Remove country suffixes (e.g. .NS, .BO) so News API gets proper article hits
        search_query = ticker.split('.')[0]
        params = {
            "q": search_query,
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10
        }
        response = await client.get(NEWS_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

async def news_scraper_loop(tickers: list, producer: KafkaProducer):
    async with httpx.AsyncClient() as client:
        while True:
            logger.info("Starting news scrape cycle...")
            for ticker in tickers:
                articles = await fetch_news_for_ticker(ticker, client)
                new_count = 0
                for article in articles:
                    pub_at = article.get("publishedAt", "")
                    # Deduplicate: skip articles we've already seen for this ticker
                    if last_seen_at.get(ticker) and pub_at <= last_seen_at[ticker]:
                        continue
                    message = {
                        "ticker": ticker,
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "url": article.get("url"),
                        "publishedAt": pub_at,
                        "source": article.get("source", {}).get("name")
                    }
                    await producer.publish("raw-news", message)
                    new_count += 1
                    if not last_seen_at.get(ticker) or pub_at > last_seen_at[ticker]:
                        last_seen_at[ticker] = pub_at

                if new_count:
                    logger.info(f"Published {new_count} new articles for {ticker}.")

            logger.info("News scrape cycle complete. Sleeping for 60 seconds.")
            await asyncio.sleep(60)
