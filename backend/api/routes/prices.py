from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.database import get_db
from db.models import PriceTick
from typing import List

router = APIRouter(prefix="/api")

@router.get("/prices/{ticker}")
async def get_prices(
    ticker: str, 
    interval: str = Query("1d", description="Time interval for candles"),
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PriceTick)
        .where(PriceTick.ticker == ticker.upper())
        .order_by(desc(PriceTick.timestamp))
        .limit(limit)
    )
    prices = result.scalars().all()
    # Return in chronological order
    return prices[::-1]
