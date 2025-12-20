from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging

from database import get_db
from schemas.quiz import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizResultsResponse,
    QuizHistoryResponse
)
from services.quiz_generator import QuizGenerator
from services.score_service import ScoreService
from models.quiz import Quiz, QuizAttempt
from s3_client import s3_client
from kafka_module.producer import KafkaProducer

router = APIRouter()
logger = logging.getLogger(__name__)

def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user ID from header. In production, this would be from JWT."""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header required")
    return x_user_id

@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    x_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Generate a quiz from a document"""
    try:
        quiz_generator = QuizGenerator(db)
        quiz = await quiz_generator.generate_from_document(
            document_id=request.document_id,
            user_id=x_user_id,
            question_count=request.question_count,
            question_types=request.question_types
        )

        # Store quiz template in S3
        s3_client.upload_quiz_template(quiz)
        
        # Produce Kafka event
        await KafkaProducer.send_quiz_generated(
            quiz_id=str(quiz.id),
            document_id=request.document_id,
            user_id=x_user_id
        )
        
        return QuizGenerateResponse(
            quiz_id=str(quiz.id),
            message="Quiz generated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to generate quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: str,
    x_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get quiz questions"""
    try:
        # Get quiz from database
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get quiz template from S3
        quiz_data = s3_client.get_quiz_template(quiz_id)
        if not quiz_data:
            raise HTTPException(status_code=404, detail="Quiz template not found")
        
        return QuizResponse(
            id=quiz.id,
            document_id=quiz.document_id,
            questions=quiz_data["questions"],
            created_at=quiz.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{quiz_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    quiz_id: str,
    request: QuizSubmitRequest,
    x_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Submit quiz responses"""
    try:
        # Get quiz from database
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get quiz template from S3 for answers
        quiz_data = s3_client.get_quiz(quiz_id)
        if not quiz_data:
            raise HTTPException(status_code=404, detail="Quiz template not found")
        
        # Calculate score
        score_service = ScoreService()
        result = score_service.calculate_score(
            quiz_data["questions"],
            request.responses
        )
        
        # Store attempt
        attempt = QuizAttempt(
            id=str(uuid.uuid4()),
            quiz_id=quiz_id,
            user_id=x_user_id,
            responses=request.responses,
            score=result.score,
            max_score=result.max_score,
            details=result.details
        )
        db.add(attempt)
        db.commit()
        
        return QuizSubmitResponse(
            attempt_id=str(attempt.id),
            score=result.score,
            max_score=result.max_score,
            passed=result.passed
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{quiz_id}/results", response_model=QuizResultsResponse)
def get_quiz_results(
    quiz_id: str,
    attempt_id: Optional[str] = None,
    x_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get quiz results with feedback"""
    try:
        query = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == x_user_id
        )
        
        if attempt_id:
            query = query.filter(QuizAttempt.id == attempt_id)
        
        attempt = query.order_by(QuizAttempt.completed_at.desc()).first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="Quiz attempt not found")
        
        return QuizResultsResponse(
            attempt_id=str(attempt.id),
            quiz_id=str(attempt.quiz_id),
            score=attempt.score,
            max_score=attempt.max_score,
            passed=attempt.score >= (attempt.max_score * 0.7),  # 70% passing threshold
            feedback=attempt.details.get("feedback", []),
            explanations=attempt.details.get("explanations", []),
            completed_at=attempt.completed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quiz results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[QuizHistoryResponse])
def get_quiz_history(
    x_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """Get user's quiz history"""
    try:
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == x_user_id
        ).order_by(
            QuizAttempt.completed_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            QuizHistoryResponse(
                attempt_id=str(attempt.id),
                quiz_id=str(attempt.quiz_id),
                score=attempt.score,
                max_score=attempt.max_score,
                passed=attempt.score >= (attempt.max_score * 0.7),
                completed_at=attempt.completed_at
            )
            for attempt in attempts
        ]
    except Exception as e:
        logger.error(f"Failed to get quiz history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{quiz_id}")
def delete_quiz(
    quiz_id: str,
    x_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Delete a quiz"""
    try:
        # Check if quiz exists and belongs to user
        quiz = db.query(Quiz).filter(
            Quiz.id == quiz_id,
            Quiz.user_id == x_user_id
        ).first()
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Delete from S3
        s3_client.delete_quiz_template(quiz_id)
        
        # Delete from database (cascade will delete attempts)
        db.delete(quiz)
        db.commit()
        
        return {"message": "Quiz deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e))