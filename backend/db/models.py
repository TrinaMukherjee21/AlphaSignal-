from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    score = Column(Float)
    signal = Column(String)  # BUY, SELL, HOLD
    source = Column(String)  # news, social
    headline = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PriceTick(Base):
    __tablename__ = "price_ticks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    timestamp = Column(DateTime(timezone=True), index=True)
