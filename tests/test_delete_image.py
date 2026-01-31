"""
Unit tests for delete_image Lambda handler.
"""
import pytest
import json
import os
import base64
from unittest.mock import patch
from moto import mock_aws
import boto3


class TestDeleteImageHandler:
    """Tests for delete_image Lambda handler."""
    
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
            's3_key': 'images/user123/test-image-id.png',
            'created_at': '2024-01-01T10:00:00'
        })
        
        return s3, table
    
    @mock_aws
    def test_successful_delete(self, sample_image_base64):
        """Test successful image deletion."""
        s3, table = self._setup_aws_resources(sample_image_base64)
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.delete_image import delete_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': {'user_id': 'user123'}
            }
            response = delete_image(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['data']['deleted'] is True
            assert body['data']['image_id'] == 'test-image-id'
            
            # Verify image is deleted from DynamoDB
            result = table.get_item(Key={'image_id': 'test-image-id'})
            assert 'Item' not in result
    
    @mock_aws
    def test_delete_nonexistent_image(self):
        """Test deleting a non-existent image."""
        # Create empty table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.delete_image import delete_image
            
            event = {
                'pathParameters': {'image_id': 'nonexistent-id'},
                'queryStringParameters': None
            }
            response = delete_image(event, None)
            
            assert response['statusCode'] == 404
            body = json.loads(response['body'])
            assert body['error']['code'] == 'IMAGE_NOT_FOUND'
    
    @mock_aws
    def test_delete_unauthorized(self, sample_image_base64):
        """Test deleting an image owned by another user."""
        self._setup_aws_resources(sample_image_base64)
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.delete_image import delete_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': {'user_id': 'different-user'}
            }
            response = delete_image(event, None)
            
            assert response['statusCode'] == 403
            body = json.loads(response['body'])
            assert body['error']['code'] == 'FORBIDDEN'
    
    @mock_aws
    def test_delete_without_user_id(self, sample_image_base64):
        """Test deletion without user_id (admin delete)."""
        s3, table = self._setup_aws_resources(sample_image_base64)
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.delete_image import delete_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': None  # No user_id = admin delete
            }
            response = delete_image(event, None)
            
            # Should succeed without user authorization check
            assert response['statusCode'] == 200
    
    def test_missing_image_id(self):
        """Test delete with missing image_id."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.delete_image import delete_image
            
            event = {
                'pathParameters': {},
                'queryStringParameters': None
            }
            response = delete_image(event, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INVALID_IMAGE_ID'
    
    def test_empty_image_id(self):
        """Test delete with empty image_id."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.delete_image import delete_image
            
            event = {
                'pathParameters': {'image_id': ''},
                'queryStringParameters': None
            }
            response = delete_image(event, None)
            
            assert response['statusCode'] == 400
    
    @mock_aws
    def test_s3_deletion_failure_continues(self, sample_image_base64):
        """Test that DynamoDB deletion continues even if S3 fails."""
        # Create DynamoDB only (S3 object doesn't exist)
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
            's3_key': 'images/user123/nonexistent.png'
        })
        
        # Create empty bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-image-bucket')
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.delete_image import delete_image
            
            event = {
                'pathParameters': {'image_id': 'test-image-id'},
                'queryStringParameters': None
            }
            response = delete_image(event, None)
            
            # Should still succeed (DynamoDB deletion should work)
            assert response['statusCode'] == 200
            
            # Verify DynamoDB item is deleted
            result = table.get_item(Key={'image_id': 'test-image-id'})
            assert 'Item' not in result
