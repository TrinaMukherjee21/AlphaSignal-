import os
import urllib.parse
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0").strip()

if REDIS_URL.startswith("rediss://"):
    parsed = urllib.parse.urlparse(REDIS_URL)
    redis_client = redis.Redis(
        host=parsed.hostname, 
        port=parsed.port or 6379, 
        password=parsed.password, 
        ssl=True, 
        ssl_cert_reqs=None,
        decode_responses=True,
        health_check_interval=30,
        socket_timeout=10,
        retry_on_timeout=True
    )
else:
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        health_check_interval=30,
        socket_timeout=10,
        retry_on_timeout=True
    )
