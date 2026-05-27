import os
import json
import logging
from aiokafka import AIOKafkaProducer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.producer = None

    async def start(self):
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info(f"Kafka Producer started, connecting to {self.bootstrap_servers}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka Producer stopped")

    async def publish(self, topic: str, message_dict: dict):
        if self.producer is None:
            await self.start()
        
        try:
            await self.producer.send_and_wait(topic, message_dict)
            logger.debug(f"Published message to {topic}: {message_dict}")
        except Exception as e:
            logger.error(f"Failed to publish message to {topic}: {e}")
            raise
