from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.database import get_db
from db.models import PriceTick
import yfinance as yf
import asyncio
from typing import List

router = APIRouter(prefix="/api")

import logging

logger = logging.getLogger(__name__)

def fetch_history(ticker: str, period: str, interval: str):
    logger.info(f"Fetching yfinance history for {ticker} (p={period}, i={interval})")
    try:
        t = yf.Ticker(ticker.upper())
        df = t.history(period=period, interval=interval)
        if df.empty:
            logger.warning(f"No history found for {ticker} via yfinance")
            return []
        
        prices = []
        for timestamp, row in df.iterrows():
            prices.append({
                "ticker": ticker.upper(),
                "timestamp": timestamp.isoformat(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
        logger.info(f"Yfinance returned {len(prices)} ticks for {ticker}")
        return prices
    except Exception as e:
        logger.error(f"Yfinance fetch failed for {ticker}: {e}")
        return []

@router.get("/prices/{ticker}")
async def get_prices(
    ticker: str, 
    period: str = Query("1d", description="Time period (1d, 1wk, 1mo)"),
    db: AsyncSession = Depends(get_db)
):
    # Map each timeframe to appropriate yfinance parameters
    param_map = {
        "1d":  ("5d",  "5m"),   # 5 days of 5-min bars — enough to always show something and span market hours
        "1wk": ("1mo", "1h"),   # 1 month of hourly bars for the weekly view
        "1mo": ("3mo", "1d"),   # 3 months of daily bars for the monthly view
    }
    
    yf_period, yf_interval = param_map.get(period, ("5d", "5m"))
    
    try:
        prices = await asyncio.to_thread(fetch_history, ticker, yf_period, yf_interval)
        if prices:
            return prices
    except Exception as e:
        logger.error(f"yfinance fetch failed: {e}")
    
    # Fallback to Postgres live tick DB if yfinance fails
    result = await db.execute(
        select(PriceTick)
        .where(PriceTick.ticker == ticker.upper())
        .order_by(desc(PriceTick.timestamp))
        .limit(300)
    )
    prices_db = result.scalars().all()
    return prices_db[::-1]
