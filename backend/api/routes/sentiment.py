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

router = APIRouter(prefix="/api")

@router.get("/sentiment/{ticker}")
async def get_sentiment(ticker: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SentimentScore)
        .where(SentimentScore.ticker == ticker.upper())
        .order_by(desc(SentimentScore.created_at))
        .limit(50)
    )
    return result.scalars().all()

@router.get("/signal/{ticker}")
async def get_signal(ticker: str, db: AsyncSession = Depends(get_db)):
    # Get the latest signal from DB
    result = await db.execute(
        select(SentimentScore.signal)
        .where(SentimentScore.ticker == ticker.upper())
        .order_by(desc(SentimentScore.created_at))
        .limit(1)
    )
    signal = result.scalar_one_or_none()
    return {"ticker": ticker.upper(), "signal": signal or "HOLD"}

@router.get("/tickers")
async def get_tickers():
    # Attempt to load from Redis
    tickers = await redis_client.smembers("active_tickers")
    if not tickers:
        # Fall back to env and populate Redis
        default_tickers = os.getenv("TICKERS", "AAPL,TSLA,RELIANCE.NS,TCS.NS").split(",")
        tickers = [t.strip().upper() for t in default_tickers]
        if tickers:
            await redis_client.sadd("active_tickers", *tickers)
    
    return sorted(list(tickers))

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
