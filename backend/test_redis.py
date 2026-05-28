import asyncio
import redis.asyncio as redis

async def main():
    r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
    tickers = await r.smembers('active_tickers')
    print("Redis active_tickers:", tickers)
    
asyncio.run(main())
