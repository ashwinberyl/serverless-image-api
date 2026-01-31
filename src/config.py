"""
Configuration settings for the Image Service.
"""
import os

# AWS/LocalStack Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')

# S3 Configuration
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'image-storage-bucket')

# DynamoDB Configuration
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'ImageMetadata')

# Image Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
