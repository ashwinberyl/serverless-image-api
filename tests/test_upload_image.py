"""
Unit tests for upload_image Lambda handler.
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3


class TestUploadImageHandler:
    """Tests for upload_image Lambda handler."""
    
    @mock_aws
    def test_successful_upload(self, sample_image_base64):
        """Test successful image upload."""
        # Setup mocked AWS resources
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-image-bucket')
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Import handler after mocking
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.upload_image import upload_image
            
            event = {
                'body': json.dumps({
                    'image_data': sample_image_base64,
                    'filename': 'test_image.png',
                    'user_id': 'user123',
                    'metadata': {
                        'title': 'Test Image',
                        'description': 'A test image'
                    }
                })
            }
            
            response = upload_image(event, None)
            
            assert response['statusCode'] == 201
            body = json.loads(response['body'])
            assert 'data' in body
            assert 'image_id' in body['data']
            assert body['data']['filename'] == 'test_image.png'
    
    def test_missing_image_data(self):
        """Test upload fails when image_data is missing."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.upload_image import upload_image
            
            event = {
                'body': json.dumps({
                    'filename': 'test.png',
                    'user_id': 'user123'
                })
            }
            
            response = upload_image(event, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'error' in body
    
    def test_missing_user_id(self, sample_image_base64):
        """Test upload fails when user_id is missing."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.upload_image import upload_image
            
            event = {
                'body': json.dumps({
                    'image_data': sample_image_base64,
                    'filename': 'test.png'
                })
            }
            
            response = upload_image(event, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INVALID_USER_ID'
    
    def test_invalid_json_body(self):
        """Test upload fails for invalid JSON body."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.upload_image import upload_image
            
            event = {'body': 'not valid json'}
            
            response = upload_image(event, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INVALID_JSON'
    
    def test_invalid_file_extension(self, sample_image_base64):
        """Test upload fails for invalid file extension."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.upload_image import upload_image
            
            event = {
                'body': json.dumps({
                    'image_data': sample_image_base64,
                    'filename': 'test.pdf',
                    'user_id': 'user123'
                })
            }
            
            response = upload_image(event, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INVALID_IMAGE'
    
    def test_invalid_metadata(self, sample_image_base64):
        """Test upload fails for invalid metadata."""
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.upload_image import upload_image
            
            event = {
                'body': json.dumps({
                    'image_data': sample_image_base64,
                    'filename': 'test.png',
                    'user_id': 'user123',
                    'metadata': 'invalid metadata'  # Should be dict
                })
            }
            
            response = upload_image(event, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['error']['code'] == 'INVALID_METADATA'
    
    @mock_aws
    def test_upload_with_all_metadata_fields(self, sample_image_base64):
        """Test upload with all metadata fields."""
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-image-bucket')
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.upload_image import upload_image
            
            event = {
                'body': json.dumps({
                    'image_data': sample_image_base64,
                    'filename': 'test_image.jpg',
                    'user_id': 'user123',
                    'metadata': {
                        'title': 'Test Image',
                        'description': 'A test description',
                        'tags': ['tag1', 'tag2'],
                        'location': 'New York'
                    }
                })
            }
            
            response = upload_image(event, None)
            
            assert response['statusCode'] == 201
            body = json.loads(response['body'])
            assert 'image_id' in body['data']
