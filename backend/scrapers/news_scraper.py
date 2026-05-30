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
                    content = article.get("content", {})
                    # For older versions of yfinance, it might be flat, so fallback to article.get
                    title = content.get("title") or article.get("title")
                    
                    # URL could be nested in clickThroughUrl or flat
                    link = content.get("clickThroughUrl", {}).get("url") or article.get("link")
                    
                    # Time could be pubDate (ISO string) or providerPublishTime (unix timestamp)
                    pub_time = None
                    if "pubDate" in content:
                        try:
                            # e.g., '2022-05-30T10:00:00Z'
                            pub_time_str = content["pubDate"].replace('Z', '+00:00')
                            pub_time = datetime.fromisoformat(pub_time_str).timestamp()
                        except:
                            pass
                    if not pub_time:
                        pub_time = article.get("providerPublishTime") # Unix timestamp fallback
                    
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
                        "url": link or "https://finance.yahoo.com",
                        "created_utc": pub_time,
                        "source": content.get("provider", {}).get("displayName") or article.get("publisher", "Yahoo Finance")
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
