# /project-root/services/quiz_generator.py
from sqlalchemy.orm import Session
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Any, Optional
import uuid
import logging
from datetime import datetime

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
            # In a real implementation, we would fetch the document content
            # from a document service via Kafka event or API
            # For now, we'll simulate document content
            document_content = self._get_document_content(document_id)
            
            if not document_content:
                raise ValueError(f"Document {document_id} not found or empty")
            
            # Generate questions using LangChain
            questions = self._generate_questions(
                content=document_content,
                count=question_count,
                types=question_types or ["multiple_choice", "true_false", "short_answer"]
            )
            
            # Create quiz in database
            quiz = Quiz(
                id=str(uuid.uuid4()),
                document_id=document_id,
                user_id=user_id,
                question_count=len(questions),
                metadata={
                    "question_types": question_types,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            self.db.add(quiz)
            self.db.commit()
            
            # Store questions in quiz object for S3 storage
            quiz.questions = [q.dict() for q in questions]
            
            return quiz
            
        except Exception as e:
            logger.error(f"Failed to generate quiz: {e}")
            raise
    
    def _get_document_content(self, document_id: str) -> str:
        """Get document content from document service"""
        # This would typically come from a Kafka event or API call
        # For now, return simulated content
        return f"Document content for {document_id}. This is sample text about machine learning. Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. There are three main types: supervised learning, unsupervised learning, and reinforcement learning."
    
    def _generate_questions(
        self,
        content: str,
        count: int,
        types: List[str]
    ) -> List[Question]:
        """Generate questions using LangChain and OpenAI"""
        try:
            parser = PydanticOutputParser(pydantic_object=GeneratedQuiz)
            
            prompt_template = PromptTemplate(
                template="""Generate {count} quiz questions from the following content.
                Include these question types: {types}.
                
                Content: {content}
                
                {format_instructions}
                
                Provide a variety of question difficulties and ensure explanations are educational.""",
                input_variables=["content", "count", "types"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            # Use the LCEL pipeline style: PromptTemplate | LLM
            chain = prompt_template | self.llm

            response = chain.invoke({
                "content": content,
                "count": count,
                "types": ", ".join(types)
            })
            
            parsed = parser.parse(response)
            return parsed.questions
            
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            # Fallback to simple question generation
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