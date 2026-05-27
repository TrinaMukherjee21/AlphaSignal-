import os
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.database import get_db
from db.models import SentimentScore
from typing import List

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
    tickers = os.getenv("TICKERS", "AAPL,TSLA,RELIANCE.NS,TCS.NS").split(",")
    return [t.strip().upper() for t in tickers]
