import os
import asyncio
import yfinance as yf
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from kafka.producer import KafkaProducer
from db.redis_client import redis_client

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track last published candle timestamp per ticker to avoid duplicates
last_published_timestamps = {}

def is_market_open() -> bool:
    """Check if any major market (NYSE or NSE) is currently open."""
    now = datetime.now(timezone.utc)
    weekday = now.weekday()  # 0=Mon, 6=Sun
    if weekday >= 5:
        return False
    hour, minute = now.hour, now.minute
    # NYSE: 14:30–21:00 UTC
    nyse_open = (hour == 14 and minute >= 30) or (14 < hour < 21)
    # NSE: 03:45–10:00 UTC
    nse_open = (hour == 3 and minute >= 45) or (3 < hour < 10)
    return nyse_open or nse_open

def fetch_ticker_history(ticker: str):
    try:
        t = yf.Ticker(ticker)
        interval = "1m" if is_market_open() else "5m"
        df = t.history(period="1d", interval=interval)
        return ticker, df
    except Exception as e:
        logger.error(f"Error fetching yfinance history for {ticker}: {e}")
        return ticker, None

async def price_scraper_loop(producer: KafkaProducer):
    global last_published_timestamps

    while True:
        sleep_secs = 10 if is_market_open() else 60
        logger.info(f"Starting price scrape cycle (market {'OPEN' if sleep_secs == 10 else 'CLOSED'} – next in {sleep_secs}s)...")

        active_tickers = await redis_client.smembers("active_tickers")
        if not active_tickers:
            await asyncio.sleep(sleep_secs)
            continue

        tickers = list(active_tickers)
        tasks = [asyncio.to_thread(fetch_ticker_history, t) for t in tickers]
        results = await asyncio.gather(*tasks)

        for ticker, df in results:
            if df is not None and not df.empty:
                try:
                    published_count = 0
                    for timestamp, row in df.iterrows():
                        ts_iso = timestamp.isoformat()
                        # Deduplicate: only publish candles newer than the last one sent
                        if ticker not in last_published_timestamps or ts_iso > last_published_timestamps[ticker]:
                            message = {
                                "ticker": ticker,
                                "open": float(row["Open"]),
                                "high": float(row["High"]),
                                "low": float(row["Low"]),
                                "close": float(row["Close"]),
                                "volume": int(row["Volume"]),
                                "timestamp": ts_iso
                            }
                            await producer.publish("price-ticks", message)
                            last_published_timestamps[ticker] = ts_iso
                            published_count += 1

                    if published_count:
                        logger.info(f"Published {published_count} new price candles for {ticker}.")
                except Exception as e:
                    logger.error(f"Error processing price history for {ticker}: {e}")

        await asyncio.sleep(sleep_secs)
