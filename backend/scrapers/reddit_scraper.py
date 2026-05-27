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
    'User-Agent': 'TradeSentiment/1.0'
}

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
                    
                    for post in posts:
                        data = post.get("data", {})
                        message = {
                            "ticker": ticker,
                            "title": data.get("title"),
                            "selftext": data.get("selftext"),
                            "score": data.get("score"),
                            "url": f"https://www.reddit.com{data.get('permalink')}",
                            "created_utc": data.get("created_utc")
                        }
                        await producer.publish("raw-social", message)
                    
                    # Small delay between subreddit requests to avoid rate limits
                    await asyncio.sleep(1)
            
            logger.info("Reddit scrape cycle complete. Sleeping for 3 minutes.")
            await asyncio.sleep(180)
