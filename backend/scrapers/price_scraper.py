import os
import asyncio
import yfinance as yf
import logging
from datetime import datetime
from dotenv import load_dotenv
from kafka.producer import KafkaProducer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track the last published timestamp for each ticker to avoid duplicates
last_published_timestamps = {}

def fetch_ticker_history(ticker: str):
    try:
        t = yf.Ticker(ticker)
        # Fetch 1m data for the last day
        df = t.history(period="1d", interval="1m")
        return ticker, df
    except Exception as e:
        logger.error(f"Error fetching yfinance history for {ticker}: {e}")
        return ticker, None

async def price_scraper_loop(tickers: list, producer: KafkaProducer):
    global last_published_timestamps
    
    while True:
        logger.info("Starting price scrape cycle...")
        
        # yfinance is synchronous, run them in parallel threads
        tasks = [asyncio.to_thread(fetch_ticker_history, t) for t in tickers]
        results = await asyncio.gather(*tasks)
        
        for ticker, df in results:
            if df is not None and not df.empty:
                try:
                    published_count = 0
                    
                    # Iterate through all candles returned
                    for timestamp, row in df.iterrows():
                        ts_iso = timestamp.isoformat()
                        
                        # Only publish if this candle is newer than the last one we published
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
                            
                    logger.info(f"Published {published_count} new price candles for {ticker}.")
                except Exception as e:
                    logger.error(f"Error processing price history for {ticker}: {e}")

        logger.info("Price scrape cycle complete. Sleeping for 1 minute.")
        await asyncio.sleep(60)
