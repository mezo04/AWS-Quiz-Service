import boto3
from botocore.exceptions import ClientError
import json
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.s3_bucket_name
    
    def upload_document(self, document_id: str, content: str) -> bool: 
        """Upload document content to S3"""
        try:
            key = f"documents/{document_id}.txt"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType='text/plain',
                encode_utf8=True
            )
            logger.info(f"Uploaded document to s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload document: {e}")
            return False
    
    def upload_quiz(self, quiz) -> bool:
        """Upload quiz template to S3"""
        try:
            key = f"quiz-templates/{quiz.id}.json"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps({
                    "id": str(quiz.id),
                    "questions": quiz.questions
                }),
                ContentType='application/json'
            )
            logger.info(f"Uploaded quiz template to s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload quiz template: {e}")
            return False

    def get_quiz(self,quiz_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve quiz template from S3"""
        try:
            key = f"quiz-templates/{quiz_id}.json"
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            content = response['Body'].read().decode('utf-8')
            quiz_data = json.loads(content)
            return quiz_data
        except ClientError as e:
            logger.error(f"Failed to get quiz template from S3: {e}")
            return None
    
    def get_document_content(self, document_id) -> str:
        """Retrieve document content from S3 given a Document model instance"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=f"documents/{document_id}.txt"
            )
            content = response['Body'].read().decode('utf-8')
            return content
        except ClientError as e:
            logger.error(f"Failed to get document content from S3: {e}")
            return ""

    def delete_quiz_template(self, quiz_id: str) -> bool:
        """Delete quiz template from S3"""
        try:
            key = f"quiz-templates/{quiz_id}.json"
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"Deleted quiz template from s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete quiz template: {e}")
            return False

# Global instance
s3_client = S3Client()