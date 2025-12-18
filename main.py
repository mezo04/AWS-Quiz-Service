from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from database import engine, Base
from routers import quiz
from kafka.consumer import start_kafka_consumer, stop_kafka_consumer
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    logger.info("Starting Kafka consumer...")
    consumer_task = asyncio.create_task(start_kafka_consumer())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kafka consumer...")
    await stop_kafka_consumer(consumer_task)

app = FastAPI(
    title="Quiz and Exercise Service",
    description="Service for generating quizzes from documents and managing quiz responses",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "quiz-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)