import httpx
import asyncio

async def test():
    async with httpx.AsyncClient(timeout=30.0) as c:
        for p in ["1d", "1wk", "1mo"]:
            print(f"-- Testing period: {p} --")
            try:
                r = await c.get(f"http://localhost:8000/api/prices/AAPL?period={p}")
                data = r.json()
                print(f"Status: {r.status_code}, Length: {len(data)}")
                if len(data) > 0:
                    print(f"First: {data[0]['timestamp']}, Last: {data[-1]['timestamp']}")
            except Exception as e:
                print(f"Error test {p}: {e}")

asyncio.run(test())
