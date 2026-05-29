import os
import asyncio
import httpx
import logging
from dotenv import load_dotenv
from kafka.producer import KafkaProducer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Track last seen post timestamp per (ticker, subreddit) to avoid reprocessing
last_seen_utc: dict = {}

async def fetch_reddit_search(ticker: str, subreddit: str, client: httpx.AsyncClient):
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={ticker}&sort=new&limit=10"
    try:
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 429:
            logger.warning(f"Reddit rate limit hit for {subreddit}. Sleeping...")
            return []
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("children", [])
    except Exception as e:
        logger.error(f"Error fetching Reddit feed for {ticker} in {subreddit}: {e}")
        return []

async def reddit_scraper_loop(tickers: list, producer: KafkaProducer):
    async with httpx.AsyncClient() as client:
        while True:
            logger.info("Starting Reddit JSON feed scrape cycle...")

            for ticker in tickers:
                is_indian_market = ticker.endswith('.NS') or ticker.endswith('.BO')
                active_subreddits = ["IndianStreetBets", "IndiaInvestments"] if is_indian_market else ["stocks", "wallstreetbets"]
                search_query = ticker.split('.')[0]

                for sub in active_subreddits:
                    posts = await fetch_reddit_search(search_query, sub, client)
                    dedup_key = f"{ticker}:{sub}"
                    new_count = 0

                    for post in posts:
                        data = post.get("data", {})
                        created_utc = data.get("created_utc", 0)

                        # Deduplicate: skip posts we've already seen
                        if last_seen_utc.get(dedup_key, 0) >= created_utc:
                            continue

                        message = {
                            "ticker": ticker,
                            "title": data.get("title"),
                            "selftext": data.get("selftext"),
                            "score": data.get("score"),
                            "url": f"https://www.reddit.com{data.get('permalink')}",
                            "created_utc": created_utc
                        }
                        await producer.publish("raw-social", message)
                        new_count += 1
                        if created_utc > last_seen_utc.get(dedup_key, 0):
                            last_seen_utc[dedup_key] = created_utc

                    if new_count:
                        logger.info(f"Published {new_count} new Reddit posts for {ticker} from r/{sub}.")

                    await asyncio.sleep(1)  # Small delay between subreddits

            logger.info("Reddit scrape cycle complete. Sleeping for 600 seconds to respect IP rate limits.")
            await asyncio.sleep(600)
