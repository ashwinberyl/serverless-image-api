"""
AWS Client Factory for LocalStack and Production environments.
"""
import os
import boto3
from config import LOCALSTACK_ENDPOINT, AWS_REGION

# Read credentials from environment variables
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')


def is_local_environment():
    """Check if running in local development environment."""
    return os.environ.get('AWS_SAM_LOCAL') == 'true' or \
           os.environ.get('LOCALSTACK', 'true').lower() == 'true'


def get_s3_client():
    """
    Get S3 client configured for LocalStack or AWS.
    
    Returns:
        boto3.client: S3 client instance
    """
    if is_local_environment():
        return boto3.client(
            's3',
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    return boto3.client('s3', region_name=AWS_REGION)


def get_dynamodb_resource():
    """
    Get DynamoDB resource configured for LocalStack or AWS.
    
    Returns:
        boto3.resource: DynamoDB resource instance
    """
    if is_local_environment():
        return boto3.resource(
            'dynamodb',
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    return boto3.resource('dynamodb', region_name=AWS_REGION)


def get_dynamodb_client():
    """
    Get DynamoDB client configured for LocalStack or AWS.
    
    Returns:
        boto3.client: DynamoDB client instance
    """
    if is_local_environment():
        return boto3.client(
            'dynamodb',
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    return boto3.client('dynamodb', region_name=AWS_REGION)
