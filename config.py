# /project-root/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/quizdb"
    
    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = "None"
    AWS_SECRET_ACCESS_KEY: Optional[str] = "None"

    AWS_REGION: str = "us-east-1"
    S3_BUCKET_PREFIX: str = "quiz-service-storage"
    ENVIRONMENT: str = "dev"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_QUIZ_REQUESTED: str = "quiz.requested"
    KAFKA_TOPIC_QUIZ_GENERATED: str = "quiz.generated"
    KAFKA_TOPIC_NOTES_GENERATED: str = "notes.generated"
    KAFKA_CONSUMER_GROUP: str = "quiz-service-group"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = "None"
    
    # Application
    DEBUG: bool = False
    
    @property
    def s3_bucket_name(self):
        return f"{self.S3_BUCKET_PREFIX}-{self.ENVIRONMENT}"
    
    class Config:
        env_file = ".env"

settings = Settings()