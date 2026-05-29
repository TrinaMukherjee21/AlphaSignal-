import os
import asyncio
import logging
from datetime import datetime
import yfinance as yf
from kafka.producer import KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track last seen article timestamps per ticker to avoid reprocessing
last_seen_published: dict = {}

async def news_scraper_loop(tickers: list, producer: KafkaProducer):
    while True:
        logger.info("Starting Yahoo Finance news scrape cycle...")
        for ticker in tickers:
            try:
                # Use yfinance instead of NewsAPI to avoid 429 Rate Limits
                symbol = ticker.upper()
                news = await asyncio.to_thread(lambda: yf.Ticker(symbol).news)
                
                if not news:
                    logger.debug(f"No news found for {ticker} via yfinance.")
                    continue

                new_count = 0
                for article in reversed(news): # Process oldest to newest
                    title = article.get("title")
                    link = article.get("link")
                    pub_time = article.get("providerPublishTime") # Unix timestamp
                    
                    if not title or not pub_time:
                        continue
                        
                    # Deduplicate: skip articles we've already seen
                    if last_seen_published.get(ticker) and pub_time <= last_seen_published[ticker]:
                        continue
                        
                    message_data = {
                        "ticker": ticker,
                        "title": title,
                        "selftext": title, # Use title for NLP sentiment
                        "score": 1,
                        "url": link,
                        "created_utc": pub_time,
                        "source": article.get("publisher", "Yahoo Finance")
                    }
                    
                    await producer.publish("raw-news", message_data)
                    new_count += 1
                    
                    if not last_seen_published.get(ticker) or pub_time > last_seen_published[ticker]:
                        last_seen_published[ticker] = pub_time

                if new_count:
                    logger.info(f"YFinance: Published {new_count} new articles for {ticker}.")

            except Exception as e:
                logger.error(f"Error fetching YFinance news for {ticker}: {e}")
                
        logger.info("News scrape cycle complete. Sleeping for 60 seconds.")
        await asyncio.sleep(60)
