import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as c:
        try:
            print("1. GET /api/tickers")
            r = await c.get("http://localhost:8000/api/tickers")
            print(r.status_code, r.text)
            
            print("\n2. POST /api/tickers/MSFT")
            r = await c.post("http://localhost:8000/api/tickers/MSFT")
            print(r.status_code, r.text)
            
            print("\n3. GET /api/tickers again")
            r = await c.get("http://localhost:8000/api/tickers")
            print(r.status_code, r.text)
        except Exception as e:
            print("Connection error:", e)
        
asyncio.run(test())
