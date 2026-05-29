import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Use decode_responses=True for string results
# Use ssl_cert_reqs=None if needed for Upstash
redis_client = redis.from_url(
    REDIS_URL, 
    decode_responses=True,
    ssl_cert_reqs=None
)
