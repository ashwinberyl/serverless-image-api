"""
Unit tests for list_images Lambda handler.
"""
import pytest
import json
import os
from unittest.mock import patch
from moto import mock_aws
import boto3


class TestListImagesHandler:
    """Tests for list_images Lambda handler."""
    
    def _setup_dynamodb_with_data(self):
        """Helper to set up DynamoDB with test data."""
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # Add test items
        test_items = [
            {
                'image_id': 'img1',
                'user_id': 'user123',
                'title': 'Sunset Photo',
                'tags': ['sunset', 'nature'],
                'location': 'California',
                'created_at': '2024-01-01T10:00:00',
                's3_key': 'images/user123/img1.jpg'
            },
            {
                'image_id': 'img2',
                'user_id': 'user123',
                'title': 'Beach Day',
                'tags': ['beach', 'summer'],
                'location': 'Florida',
                'created_at': '2024-01-02T10:00:00',
                's3_key': 'images/user123/img2.jpg'
            },
            {
                'image_id': 'img3',
                'user_id': 'user456',
                'title': 'Mountain View',
                'tags': ['mountain', 'nature'],
                'location': 'Colorado',
                'created_at': '2024-01-03T10:00:00',
                's3_key': 'images/user456/img3.jpg'
            }
        ]
        
        for item in test_items:
            table.put_item(Item=item)
        
        return table
    
    @mock_aws
    def test_list_all_images(self):
        """Test listing all images without filters."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': None}
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'data' in body
            assert 'images' in body['data']
            assert len(body['data']['images']) == 3
    
    @mock_aws
    def test_filter_by_user_id(self):
        """Test filtering images by user ID."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': {'user_id': 'user123'}}
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert len(body['data']['images']) == 2
            for img in body['data']['images']:
                assert img['user_id'] == 'user123'
    
    @mock_aws
    def test_filter_by_title(self):
        """Test filtering images by title (contains)."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': {'title': 'Sunset'}}
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert len(body['data']['images']) == 1
            assert body['data']['images'][0]['title'] == 'Sunset Photo'
    
    @mock_aws
    def test_filter_by_tags(self):
        """Test filtering images by tags."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': {'tags': 'nature'}}
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            # Should match 'Sunset Photo' and 'Mountain View' with 'nature' tag
            assert len(body['data']['images']) == 2
    
    @mock_aws
    def test_filter_by_location(self):
        """Test filtering images by location."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': {'location': 'California'}}
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert len(body['data']['images']) == 1
            assert body['data']['images'][0]['location'] == 'California'
    
    @mock_aws
    def test_filter_by_date_range(self):
        """Test filtering images by date range."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {
                'queryStringParameters': {
                    'created_after': '2024-01-01T00:00:00',
                    'created_before': '2024-01-02T00:00:00'
                }
            }
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert len(body['data']['images']) == 1
    
    @mock_aws
    def test_pagination_limit(self):
        """Test pagination with limit parameter."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': {'limit': '2'}}
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert len(body['data']['images']) <= 2
    
    @mock_aws
    def test_combined_filters(self):
        """Test combining multiple filters."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {
                'queryStringParameters': {
                    'user_id': 'user123',
                    'tags': 'sunset'
                }
            }
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert len(body['data']['images']) == 1
    
    @mock_aws
    def test_s3_key_not_exposed(self):
        """Test that s3_key is not returned in response."""
        self._setup_dynamodb_with_data()
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': None}
            response = list_images(event, None)
            
            body = json.loads(response['body'])
            for image in body['data']['images']:
                assert 's3_key' not in image
    
    @mock_aws
    def test_empty_result(self):
        """Test empty result when no images match."""
        # Create table but don't add any items
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[{'AttributeName': 'image_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'image_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        with patch.dict(os.environ, {'LOCALSTACK': 'false'}):
            from src.handlers.list_images import list_images
            
            event = {'queryStringParameters': {'user_id': 'nonexistent'}}
            response = list_images(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['data']['images'] == []
            assert body['data']['count'] == 0
