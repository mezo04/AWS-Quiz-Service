# /project-root/schemas/quiz.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Request schemas
class QuizGenerateRequest(BaseModel):
    document_id: str = Field(..., description="ID of the document to generate quiz from")
    question_count: Optional[int] = Field(10, ge=1, le=50, description="Number of questions to generate")
    question_types: Optional[List[str]] = Field(
        ["multiple_choice", "true_false", "short_answer"],
        description="Types of questions to generate"
    )

class QuizSubmitRequest(BaseModel):
    responses: List[Dict[str, Any]] = Field(
        ...,
        description="List of question responses. Each response should contain 'question_id' and 'answer'"
    )

# Response schemas
class QuizGenerateResponse(BaseModel):
    quiz_id: str
    message: str

class QuestionResponse(BaseModel):
    id: str
    type: str
    text: str
    options: Optional[List[str]] = None

class QuizResponse(BaseModel):
    id: str
    document_id: str
    questions: List[QuestionResponse]
    created_at: datetime

class QuizSubmitResponse(BaseModel):
    attempt_id: str
    score: float
    max_score: float
    passed: bool

class FeedbackItem(BaseModel):
    question_id: str
    question_index: int
    score: float
    max_score: float
    feedback: str

class ExplanationItem(BaseModel):
    question_id: str
    explanation: str

class QuizResultsResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: float
    max_score: float
    passed: bool
    feedback: List[FeedbackItem]
    explanations: List[ExplanationItem]
    completed_at: datetime

class QuizHistoryResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: float
    max_score: float
    passed: bool
    completed_at: datetime