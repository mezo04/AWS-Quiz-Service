from sqlalchemy.orm import Session
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Any, Optional
import uuid
import logging
from datetime import datetime
from encryption import crypto_instance

from s3_client import s3_client
from models.quiz import Quiz
from config import settings

logger = logging.getLogger(__name__)

class Question(BaseModel):
    id: str = Field(description="Unique question identifier")
    type: str = Field(description="Question type: multiple_choice, true_false, or short_answer")
    text: str = Field(description="The question text")
    options: Optional[List[str]] = Field(default=None, description="Options for multiple choice")
    correct_answer: Any = Field(description="The correct answer")
    explanation: str = Field(description="Explanation of the correct answer")

class GeneratedQuiz(BaseModel):
    questions: List[Question] = Field(description="List of generated questions")

class QuizGenerator:
    def __init__(self, db: Session):
        self.db = db
        # Use the langchain_openai OpenAI client for compatibility with
        # the installed langchain/langchain-openai packages
        self.llm = OpenAI(
            temperature=0.7,
            model="gpt-3.5-turbo",
            api_key=settings.OPENAI_API_KEY
        )
        
    def generate_from_document(
        self,
        document_id: str,
        user_id: str,
        question_count: int = 10,
        question_types: Optional[List[str]] = None
    ) -> Quiz:
        """Generate quiz questions from a document"""
        try:
            document_content = self._get_document_content(document_id)
            
            if not document_content:
                raise ValueError(f"Document {document_id} not found or empty")
            
            # Generate questions using LangChain
            questions = self._generate_questions(
                content=document_content,
                count=question_count,
                types=question_types or ["multiple_choice", "true_false", "short_answer"]
            )
            question_types_str = ",".join(question_types) if question_types else "all"
            # Create quiz in database
            quiz = Quiz(
                id=str(uuid.uuid4()),
                document_id=crypto_instance.encrypt(document_id),
                user_id=crypto_instance.encrypt(user_id),
                question_count=crypto_instance.encrypt(str(len(questions))),
                question_types=crypto_instance.encrypt(question_types_str),
                created_at=datetime.now(datetime.timezone.utc)
            )
            self.db.add(quiz)
            self.db.commit()
            
            # Store questions in quiz object for S3 storage
            quiz.questions = [q.model_dump() for q in questions]
            
            return quiz
            
        except Exception as e:
            logger.error(f"Failed to generate quiz: {e}")
            raise
    
    def _get_document_content(self, document_id: str) -> str:
        """Get document content from AWS S3
        
        Args:
            document_id: The unique identifier of the document
            
        Returns:
            The document content as a string
            
        Raises:
            ValueError: If document is not found in the database
        """
        try:
            
            document_content = s3_client.get_document_content(document_id)
            logger.info(f"Successfully retrieved document {document_id} from S3")
            return document_content
            
        except Exception as e:
            logger.error(f"Failed to fetch document from S3: {e}")
            raise
    
    def _generate_questions(
        self,
        content: str,
        count: int,
        types: List[str]
    ) -> List[Question]:
        """Generate questions using LangChain and OpenAI"""
        try:
            prompt_template = PromptTemplate(
                template="""Generate {count} quiz questions from the following content.
                Include these question types only: {types}.
                
                Content: {content}
                
                Format the output as a JSON object with this structure:
                {{
                    "questions": [
                        {{
                            "id": "unique_id",
                            "type": "multiple_choice|true_false|short_answer",
                            "text": "question text",
                            "options": ["option1", "option2"],
                            "correct_answer": "answer",
                            "explanation": "explanation"
                        }}
                    ]
                }}
                Ensure questions are clear and concise.
                Provide a variety of question difficulties and ensure explanations are educational.""",
                input_variables=["content", "count", "types"]
            )
            
            prompt = prompt_template.format(
                content=content,
                count=count,
                types=", ".join(types)
            )

            response = self.llm(prompt)
            
            # Parse JSON response
            import json
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    parsed_data = json.loads(json_str)
                    questions_data = parsed_data.get('questions', [])
                    questions = [Question(**q) for q in questions_data]
                    return questions
            except (json.JSONDecodeError, KeyError, TypeError) as parse_error:
                logger.warning(f"Failed to parse LLM response as JSON: {parse_error}")
            
            return self._generate_fallback_questions(content, count)
            
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            return self._generate_fallback_questions(content, count)
    
    def _generate_fallback_questions(self, content: str, count: int) -> List[Question]:
        """Generate simple fallback questions if LLM fails"""
        questions = []
        sentences = content.split('. ')
        
        for i in range(min(count, len(sentences))):
            sentence = sentences[i % len(sentences)]
            q_id = str(uuid.uuid4())
            
            if i % 3 == 0:
                # Multiple choice
                questions.append(Question(
                    id=q_id,
                    type="multiple_choice",
                    text=f"What is the main idea of: '{sentence}'?",
                    options=["Option A", "Option B", "Option C", "Option D"],
                    correct_answer="Option A",
                    explanation="This is the correct answer because..."
                ))
            elif i % 3 == 1:
                # True/False
                questions.append(Question(
                    id=q_id,
                    type="true_false",
                    text=f"True or False: This sentence is about technology: '{sentence}'",
                    correct_answer=True,
                    explanation="The sentence discusses technological concepts."
                ))
            else:
                # Short answer
                questions.append(Question(
                    id=q_id,
                    type="short_answer",
                    text=f"Summarize this sentence: '{sentence}'",
                    correct_answer="A valid summary of the sentence",
                    explanation="A good summary should capture the main point."
                ))
        
        return questions