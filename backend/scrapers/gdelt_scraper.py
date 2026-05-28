import asyncio
import httpx
import logging
from kafka.producer import KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Track last seen article url per ticker to avoid reprocessing
last_seen_urls: dict = {}

async def fetch_gdelt_news(ticker: str, client: httpx.AsyncClient):
    """Fetch recent global news from GDELT (free, no API key required)."""
    try:
        search_query = ticker.split('.')[0]  # Strip .NS/.BO etc.
        params = {
            "query": search_query,
            "mode": "artlist",
            "maxrecords": 10,
            "format": "json",
            "sort": "DateDesc"
        }
        response = await client.get(GDELT_URL, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except Exception as e:
        logger.error(f"GDELT fetch error for {ticker}: {e}")
        return []

async def gdelt_scraper_loop(tickers: list, producer: KafkaProducer):
    async with httpx.AsyncClient() as client:
        while True:
            logger.info("Starting GDELT news scrape cycle...")
            for ticker in tickers:
                articles = await fetch_gdelt_news(ticker, client)
                new_count = 0
                for article in articles:
                    url = article.get("url", "")
                    # Deduplicate by URL
                    if url in last_seen_urls.get(ticker, set()):
                        continue
                    message = {
                        "ticker": ticker,
                        "title": article.get("title"),
                        "description": article.get("seendate", ""),
                        "url": url,
                        "publishedAt": article.get("seendate", ""),
                        "source": article.get("domain", "GDELT")
                    }
                    await producer.publish("raw-news", message)
                    new_count += 1
                    if ticker not in last_seen_urls:
                        last_seen_urls[ticker] = set()
                    last_seen_urls[ticker].add(url)

                if new_count:
                    logger.info(f"GDELT: Published {new_count} new articles for {ticker}.")

            logger.info("GDELT scrape cycle complete. Sleeping for 15 minutes.")
            await asyncio.sleep(900)  # GDELT updates every ~15 mins
