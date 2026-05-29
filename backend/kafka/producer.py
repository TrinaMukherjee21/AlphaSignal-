import json
import logging
from db.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer = redis_client

    async def start(self):
        logger.info("Redis-based Producer (replacing Kafka) started")

    async def stop(self):
        pass

    async def publish(self, topic: str, message_dict: dict):
        try:
            await self.producer.publish(topic, json.dumps(message_dict))
            logger.debug(f"Published message to {topic}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
