import os
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.database import get_db
from db.models import SentimentScore
from db.redis_client import redis_client
from typing import List
import yfinance as yf
from fastapi import HTTPException
import logging

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

@router.get("/sentiment/{ticker}")
async def get_sentiment(ticker: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(SentimentScore)
            .where(SentimentScore.ticker == ticker.upper())
            .order_by(desc(SentimentScore.created_at))
            .limit(50)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"[Sentiment] DB error for {ticker}: {e}")
        return []

@router.get("/signal/{ticker}")
async def get_signal(ticker: str, db: AsyncSession = Depends(get_db)):
    # 1. Try Redis cache first (fast, no DB required)
    try:
        cached = await redis_client.get(f"last_signal:{ticker.upper()}")
        if cached:
            import json
            data = json.loads(cached)
            if "signal" in data:
                return {"ticker": ticker.upper(), "signal": data["signal"]}
    except Exception as e:
        logger.warning(f"[Signal] Redis error for {ticker}: {e}")

    # 2. Try DB
    try:
        result = await db.execute(
            select(SentimentScore.signal)
            .where(SentimentScore.ticker == ticker.upper())
            .order_by(desc(SentimentScore.created_at))
            .limit(1)
        )
        signal = result.scalar_one_or_none()
        return {"ticker": ticker.upper(), "signal": signal or "HOLD"}
    except Exception as e:
        logger.error(f"[Signal] DB error for {ticker}: {e}")
        return {"ticker": ticker.upper(), "signal": "HOLD"}

@router.get("/tickers")
async def get_tickers():
    try:
        # Attempt to load from Redis
        tickers = await redis_client.smembers("active_tickers")
        
        # Log for debugging (avoiding circular import)
        import logging
        api_logger = logging.getLogger("api.sentiment")
        api_logger.info(f"🔍 [API] Ticker request. Redis set: {tickers}")

        if not tickers:
            # Fall back to env and populate Redis
            env_tickers = os.getenv("TICKERS", "AAPL,TSLA,RELIANCE.NS,TCS.NS")
            api_logger.info(f"🔄 [API] Ticker cache empty. Populating from env: {env_tickers}")
            
            default_tickers = env_tickers.split(",")
            tickers_list = [t.strip().upper() for t in default_tickers if t.strip()]
            
            if tickers_list:
                await redis_client.sadd("active_tickers", *tickers_list)
                tickers = set(tickers_list)
        
        if not tickers:
            return ["AAPL", "TSLA", "RELIANCE.NS"]
            
        return sorted(list(tickers))
    except Exception as e:
        import logging
        logging.error(f"❌ [API] Error fetching tickers: {e}")
        return ["AAPL", "TSLA", "RELIANCE.NS"] # Emergency fallback

@router.post("/tickers/{ticker}")
async def add_ticker(ticker: str):
    ticker = ticker.strip().upper()
    
    # 1. Validate with yfinance
    try:
        info = yf.Ticker(ticker).info
        if 'regularMarketPrice' not in info and 'currentPrice' not in info and 'symbol' not in info:
            raise ValueError("Invalid ticker")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ticker '{ticker}' is invalid or could not be verified via Yahoo Finance.")
        
    # 2. Add to Redis
    await redis_client.sadd("active_tickers", ticker)
    return {"message": f"Successfully added {ticker} to tracking."}
