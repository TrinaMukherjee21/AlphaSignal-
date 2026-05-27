import os
import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, topics: list | str):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topics = [topics] if isinstance(topics, str) else topics
        self.consumer = None

    async def start(self):
        if self.consumer is not None:
            try:
                # If it's already started, this is a no-op or we can check state
                # AIOKafkaConsumer doesn't have a simple .is_started but we can manage it
                return
            except Exception:
                pass

        retry_count = 0
        while True:
            try:
                if self.consumer is None:
                    self.consumer = AIOKafkaConsumer(
                        *self.topics,
                        bootstrap_servers=self.bootstrap_servers,
                        group_id="sentiment_group",
                        auto_offset_reset='earliest',
                        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
                    )
                
                await self.consumer.start()
                logger.info(f"Kafka Consumer started for topics: {self.topics}")
                break
            except Exception as e:
                # If start fails, we clear the consumer so the next retry creates a fresh one
                self.consumer = None
                retry_count += 1
                wait_time = min(2 ** retry_count, 60)
                logger.error(f"Error connecting to Kafka: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

    async def listen(self):
        if self.consumer is None:
            await self.start()
            
        try:
            async for msg in self.consumer:
                yield msg.value
        except Exception as e:
            logger.error(f"Error during message consumption: {e}")
            # Re-start consumer on error
            await self.stop()
            # self.stop() should set self.consumer to None to be safe
            self.consumer = None
            await self.start()
            async for msg in self.listen():
                yield msg

    async def stop(self):
        if self.consumer:
            try:
                await self.consumer.stop()
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")
            finally:
                self.consumer = None
                logger.info(f"Kafka Consumer stopped for topics: {self.topics}")
