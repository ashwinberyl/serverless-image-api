"""
Unit tests for get_image Lambda handler.
"""
import pytest
import json
import os
import base64
from unittest.mock import patch
from moto import mock_aws
import boto3


class TestGetImageHandler:
    """Tests for get_image Lambda handler."""
    
    def _setup_aws_resources(self, sample_image_data):
        """Helper to set up S3 and DynamoDB with test data."""
        # Create S3 bucket and upload image
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-image-bucket')
        s3.put_object(
            Bucket='test-image-bucket',
            Key='images/user123/test-image-id.png',
            Body=base64.b64decode(sample_image_data),
            ContentType='image/png'
        )
        
        # Create DynamoDB table and add item
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        table.put_item(Item={
            'image_id': 'test-image-id',
            'user_id': 'user123',
            'filename': 'test.png',
            'content_type': 'image/png',
            'file_size': 100,
            's3_key': 'images/user123/test-image-id.png',
            'title': 'Test Image',
            'description': 'A test image',
            'tags': ['test'],
            'location': 'Test Location',
            'created_at': '2024-01-01T10:00:00',
            'updated_at': '2024-01-01T10:00:00'
        })
        
        return s3, table
    
    @mock_aws
    def test_get_image_metadata(self, sample_image_base64):
        """Test getting image metadata (without download)."""
        self._setup_aws_resources(sample_image_base64)
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.get_image import get_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': {'download': 'false'}
            }
            response = get_image(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'data' in body
            assert body['data']['image_id'] == 'test-image-id'
            assert body['data']['title'] == 'Test Image'
            assert 'download_url' in body['data']
            assert 's3_key' not in body['data']  # Should not expose s3_key
    
    @mock_aws
    def test_get_image_download(self, sample_image_base64):
        """Test downloading image data."""
        self._setup_aws_resources(sample_image_base64)
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.get_image import get_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': {'download': 'true'}
            }
            response = get_image(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'image_data' in body
            assert body['filename'] == 'test.png'
            assert body['content_type'] == 'image/png'
    
    @mock_aws
    def test_get_nonexistent_image(self):
        """Test getting a non-existent image."""
        # Create empty table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.get_image import get_image
            
            event = {
                'pathParameters': {'image_id': 'nonexistent-id'},
                'queryStringParameters': None
            }
            response = get_image(event, None)
            
            assert response['statusCode'] == 404
            body = json.loads(response['body'])
            assert body['error']['code'] == 'IMAGE_NOT_FOUND'
    
    def test_missing_image_id(self):
        """Test request with missing image_id."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.get_image import get_image
            
            event = {
                'pathParameters': {},
                'queryStringParameters': None
            }
            response = get_image(event, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INVALID_IMAGE_ID'
    
    def test_empty_image_id(self):
        """Test request with empty image_id."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.get_image import get_image
            
            event = {
                'pathParameters': {'image_id': ''},
                'queryStringParameters': None
            }
            response = get_image(event, None)
            
            assert response['statusCode'] == 400
    
    @mock_aws
    def test_default_download_false(self, sample_image_base64):
        """Test that download defaults to false."""
        self._setup_aws_resources(sample_image_base64)
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.get_image import get_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': None  # No download parameter
            }
            response = get_image(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            # Should return metadata, not image data
            assert 'image_data' not in body
            assert 'download_url' in body['data']
    
    @mock_aws
    def test_presigned_url_expiry(self, sample_image_base64):
        """Test that presigned URL has expiry information."""
        self._setup_aws_resources(sample_image_base64)
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.get_image import get_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': {'download': 'false'}
            }
            response = get_image(event, None)
            
            body = json.loads(response['body'])
            assert body['data']['url_expires_in'] == 3600
