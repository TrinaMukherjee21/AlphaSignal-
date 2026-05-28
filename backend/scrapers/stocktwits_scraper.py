import os
import asyncio
import httpx
import logging
from datetime import datetime
from dotenv import load_dotenv
from kafka.producer import KafkaProducer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STOCKTWITS_API_URL = "https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"

# Track last seen message ID per ticker to avoid reprocessing
last_seen_ids: dict = {}

async def fetch_stocktwits_for_ticker(ticker: str, client: httpx.AsyncClient):
    try:
        # StockTwits uses clean symbols (no .NS etc for major ones, but let's see)
        # Actually for Indian stocks it might be different, but for AAPL/TSLA it's just the ticker.
        symbol = ticker.split('.')[0]
        url = STOCKTWITS_API_URL.format(ticker=symbol)
        
        response = await client.get(url, timeout=10.0)
        if response.status_code == 429:
            logger.warning(f"StockTwits rate limit hit for {symbol}. Sleeping...")
            return []
        response.raise_for_status()
        data = response.json()
        return data.get("messages", [])
    except Exception as e:
        logger.error(f"Error fetching StockTwits for {ticker}: {e}")
        return []

async def stocktwits_scraper_loop(tickers: list, producer: KafkaProducer):
    async with httpx.AsyncClient() as client:
        while True:
            logger.info("Starting StockTwits scrape cycle...")
            for ticker in tickers:
                messages = await fetch_stocktwits_for_ticker(ticker, client)
                new_count = 0
                for msg in messages:
                    msg_id = msg.get("id")
                    # Deduplicate: skip messages we've already seen for this ticker
                    if last_seen_ids.get(ticker) and msg_id <= last_seen_ids[ticker]:
                        continue
                    
                    # StockTwits messages are already very 'social'
                    message_data = {
                        "ticker": ticker,
                        "title": f"StockTwits Post by {msg.get('user', {}).get('username')}",
                        "selftext": msg.get("body"),
                        "score": 1, # Default score
                        "url": f"https://stocktwits.com/message/{msg_id}",
                        "created_utc": datetime.fromisoformat(msg.get("created_at").replace('Z', '+00:00')).timestamp() if msg.get("created_at") else 0,
                        "source": "StockTwits"
                    }
                    await producer.publish("raw-social", message_data)
                    new_count += 1
                    
                    # Track the most recent message ID
                    if not last_seen_ids.get(ticker) or msg_id > last_seen_ids[ticker]:
                        last_seen_ids[ticker] = msg_id

                if new_count:
                    logger.info(f"Published {new_count} new StockTwits messages for {ticker}.")

            logger.info("StockTwits scrape cycle complete. Sleeping for 60 seconds.")
            await asyncio.sleep(60)
