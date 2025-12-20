from aiokafka import AIOKafkaProducer
import json
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self):
        self.producer: AIOKafkaProducer = None
    
    async def start(self):
        """Start the Kafka producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        logger.info("Kafka producer started")
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
    
    async def send_quiz_generated(self, quiz_id: str, document_id: str, user_id: str):
        """Send quiz.generated event"""
        try:
            message = {
                "quiz_id": quiz_id,
                "document_id": document_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.producer.send_and_wait(
                settings.KAFKA_TOPIC_QUIZ_GENERATED,
                message
            )
            logger.info(f"Sent quiz.generated event for quiz {quiz_id}")
        except Exception as e:
            logger.error(f"Failed to send quiz.generated event: {e}")

# Global instance
kafka_producer = KafkaProducer()