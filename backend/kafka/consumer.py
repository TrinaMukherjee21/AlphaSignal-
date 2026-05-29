import json
import logging
import asyncio
from db.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, topics: list | str):
        self.topics = [topics] if isinstance(topics, str) else topics
        self.pubsub = redis_client.pubsub()
        self._is_started = False

    async def start(self):
        if self._is_started:
            return
        try:
            for topic in self.topics:
                await self.pubsub.subscribe(topic)
            logger.info(f"Redis-based Consumer (replacing Kafka) started for topics: {self.topics}")
            self._is_started = True
        except Exception as e:
            logger.error(f"Error subscribing to Redis topics: {e}")

    async def listen(self):
        if not self._is_started:
            await self.start()
            
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    data = message['data']
                    if isinstance(data, bytes):
                        data = data.decode('utf-8')
                    if isinstance(data, str):
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode message data: {data}")
        except Exception as e:
            logger.error(f"Error during message consumption: {e}")
            await asyncio.sleep(1)

    async def stop(self):
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
            self._is_started = False
            logger.info(f"Redis Consumer stopped for topics: {self.topics}")
