# /project-root/s3_client.py
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
    
    def upload_quiz_template(self, quiz_id: str, quiz_data: Dict[str, Any]) -> bool:
        """Upload quiz template to S3"""
        try:
            key = f"quiz-templates/{quiz_id}.json"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(quiz_data),
                ContentType='application/json'
            )
            logger.info(f"Uploaded quiz template to s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload quiz template: {e}")
            return False
    
    def get_quiz_template(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve quiz template from S3"""
        try:
            key = f"quiz-templates/{quiz_id}.json"
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            quiz_data = json.loads(response['Body'].read().decode('utf-8'))
            return quiz_data
        except ClientError as e:
            logger.error(f"Failed to get quiz template: {e}")
            return None
    
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