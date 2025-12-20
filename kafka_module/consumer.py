from aiokafka import AIOKafkaConsumer
import json
import asyncio
import logging
from typing import Dict, Any

from config import settings
from database import SessionLocal
from services.quiz_generator import QuizGenerator
from s3_client import S3Client

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self):
        self.consumer: AIOKafkaConsumer = None
        self.running = False
    
    async def start(self):
        """Start the Kafka consumer"""
        self.consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_QUIZ_REQUESTED,
            settings.KAFKA_TOPIC_NOTES_GENERATED,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            enable_auto_commit=True,
            auto_commit_interval_ms=5000
        )
        
        await self.consumer.start()
        self.running = True
        logger.info("Kafka consumer started")
    
    async def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")
    
    async def consume(self):
        """Consume messages from Kafka"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    await self._process_message(message.topic, message.value)
                except Exception as e:
                    logger.error(f"Failed to process message: {e}")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
    
    async def _process_message(self, topic: str, value: Dict[str, Any]):
        """Process a Kafka message"""
        event_type = topic
        
        if event_type == "quiz.requested":
            await self._handle_quiz_requested(value)
        elif event_type == "notes.generated":
            await self._handle_notes_generated(value)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    async def _handle_quiz_requested(self, data: Dict[str, Any]):
        """Handle quiz.requested event"""
        try:
            document_id = data.get("document_id")
            user_id = data.get("user_id")
            question_count = data.get("question_count", 10)
            question_types = data.get("question_types")
            
            if not document_id or not user_id:
                logger.warning("Missing document_id or user_id in quiz.requested event")
                return
            
            # Generate quiz
            db = SessionLocal()
            try:
                quiz_generator = QuizGenerator(db)
                quiz = quiz_generator.generate_from_document(
                    document_id=document_id,
                    user_id=user_id,
                    question_count=question_count,
                    question_types=question_types
                )
                
                logger.info(f"Generated quiz {quiz.id} for document {document_id}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to handle quiz.requested: {e}")
    
    async def _handle_notes_generated(self, data: Dict[str, Any]):
        """Handle notes.generated event"""
        # upload notes to S3 or process as needed
        s3_client = S3Client()
        s3_client.upload_notes(data.get('document_id'), data.get('summary'))

# Global instance
kafka_consumer = KafkaConsumer()

async def start_kafka_consumer():
    """Start the Kafka consumer in the background"""
    await kafka_consumer.start()
    asyncio.create_task(kafka_consumer.consume())

async def stop_kafka_consumer(task: asyncio.Task):
    """Stop the Kafka consumer"""
    await kafka_consumer.stop()
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass