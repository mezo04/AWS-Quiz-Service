# /project-root/models/quiz.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from database import Base

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    question_count = Column(Integer, nullable=False, default=0)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Non-database field for S3 data
    questions = None
    
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    responses = Column(JSON, nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    details = Column(JSON, nullable=True)
    completed_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    quiz = relationship("Quiz", back_populates="attempts")