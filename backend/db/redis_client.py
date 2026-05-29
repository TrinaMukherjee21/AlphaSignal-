import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Improved Redis Initialization for Upstash
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    ssl_cert_reqs=None,
    health_check_interval=30,
    socket_timeout=10,
    socket_connect_timeout=10,
    retry_on_timeout=True
)
