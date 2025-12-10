# /project-root/services/score_service.py
from typing import List, Dict, Any, Tuple
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ScoringResult(BaseModel):
    score: float
    max_score: float
    passed: bool
    details: Dict[str, Any]

class ScoreService:
    def calculate_score(
        self,
        questions: List[Dict[str, Any]],
        responses: List[Dict[str, Any]]
    ) -> ScoringResult:
        """Calculate score for quiz responses"""
        try:
            total_score = 0
            max_score = len(questions)
            feedback = []
            explanations = []
            
            # Create response mapping by question_id
            response_map = {r["question_id"]: r for r in responses}
            
            for i, question in enumerate(questions):
                question_id = question["id"]
                user_response = response_map.get(question_id, {})
                
                # Calculate score for this question
                question_score, question_feedback, explanation = self._score_question(
                    question, user_response
                )
                
                total_score += question_score
                feedback.append({
                    "question_id": question_id,
                    "question_index": i,
                    "score": question_score,
                    "max_score": 1,
                    "feedback": question_feedback
                })
                explanations.append({
                    "question_id": question_id,
                    "explanation": explanation
                })
            
            passed = total_score >= (max_score * 0.7)  # 70% passing
            
            return ScoringResult(
                score=total_score,
                max_score=float(max_score),
                passed=passed,
                details={
                    "feedback": feedback,
                    "explanations": explanations
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate score: {e}")
            raise
    
    def _score_question(
        self,
        question: Dict[str, Any],
        response: Dict[str, Any]
    ) -> Tuple[float, str, str]:
        """Score a single question"""
        question_type = question["type"]
        correct_answer = question["correct_answer"]
        user_answer = response.get("answer", "")
        
        if question_type == "multiple_choice":
            if user_answer == correct_answer:
                return 1.0, "Correct", question.get("explanation", "Well done!")
            else:
                return 0.0, f"Incorrect. The correct answer was {correct_answer}", question.get("explanation", "")
        
        elif question_type == "true_false":
            user_bool = str(user_answer).lower() in ["true", "1", "yes"]
            correct_bool = bool(correct_answer)
            if user_bool == correct_bool:
                return 1.0, "Correct", question.get("explanation", "Well done!")
            else:
                correct_text = "True" if correct_bool else "False"
                return 0.0, f"Incorrect. The correct answer was {correct_text}", question.get("explanation", "")
        
        elif question_type == "short_answer":
            # Simple keyword matching for short answers
            user_text = str(user_answer).lower()
            correct_text = str(correct_answer).lower()
            
            # Check if any keywords from correct answer are in user's answer
            keywords = [word for word in correct_text.split() if len(word) > 3]
            matches = sum(1 for keyword in keywords if keyword in user_text)
            
            if matches > 0:
                score = min(1.0, matches / len(keywords))
                return score, f"Partial credit: {int(score*100)}%", question.get("explanation", "")
            else:
                return 0.0, "Incorrect", question.get("explanation", "")
        
        else:
            logger.warning(f"Unknown question type: {question_type}")
            return 0.0, "Question type not supported", "No explanation available"