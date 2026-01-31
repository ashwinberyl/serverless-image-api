"""
Pytest fixtures and configuration for testing.
"""
import pytest
import boto3
import os
from moto import mock_aws

# Set environment variables for testing
os.environ['LOCALSTACK'] = 'false'  # Use moto instead of LocalStack for tests
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['S3_BUCKET_NAME'] = 'test-image-bucket'
os.environ['DYNAMODB_TABLE_NAME'] = 'TestImageMetadata'


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def s3_client(aws_credentials):
    """Create a mocked S3 client and bucket."""
    with mock_aws():
        client = boto3.client('s3', region_name='us-east-1')
        client.create_bucket(Bucket='test-image-bucket')
        yield client


@pytest.fixture
def dynamodb_resource(aws_credentials):
    """Create a mocked DynamoDB resource and table."""
    with mock_aws():
        resource = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create table
        table = resource.create_table(
            TableName='TestImageMetadata',
            KeySchema=[
                {'AttributeName': 'image_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'image_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        
        yield resource


@pytest.fixture
def mock_aws_services(aws_credentials):
    """Create all mocked AWS services together."""
    with mock_aws():
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-image-bucket')
        
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='TestImageMetadata',
            KeySchema=[
                {'AttributeName': 'image_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'image_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        
        yield {
            's3': s3,
            'dynamodb': dynamodb,
            'table': table
        }


@pytest.fixture
def sample_image_base64():
    """Return a sample base64 encoded image (1x1 red pixel PNG)."""
    # This is a minimal valid PNG file (1x1 red pixel)
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


@pytest.fixture
def sample_upload_event(sample_image_base64):
    """Return a sample upload event."""
    import json
    return {
        'body': json.dumps({
            'image_data': sample_image_base64,
            'filename': 'test_image.png',
            'user_id': 'user123',
            'metadata': {
                'title': 'Test Image',
                'description': 'A test image',
                'tags': ['test', 'sample'],
                'location': 'Test Location'
            }
        })
    }


@pytest.fixture
def sample_list_event():
    """Return a sample list event."""
    return {
        'queryStringParameters': {
            'user_id': 'user123',
            'limit': '10'
        }
    }


@pytest.fixture
def sample_get_event():
    """Return a sample get event."""
    return {
        'pathParameters': {
            'image_id': 'test-image-id'
        },
        'queryStringParameters': {
            'download': 'false'
        }
    }


@pytest.fixture
def sample_delete_event():
    """Return a sample delete event."""
    return {
        'pathParameters': {
            'image_id': 'test-image-id'
        },
        'queryStringParameters': {
            'user_id': 'user123'
        }
    }
