"""
Lambda handler for uploading images with metadata.
"""
import json
import uuid
import base64
from datetime import datetime
from typing import Dict, Any

from config import S3_BUCKET_NAME, DYNAMODB_TABLE_NAME
from utils.aws_clients import get_s3_client, get_dynamodb_resource
from utils.validators import validate_image_file, validate_metadata, validate_user_id
from utils.response_helpers import create_success_response, create_error_response


def upload_image(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for uploading an image with metadata.
    
    Expected request body:
    {
        "image_data": "base64_encoded_image",
        "filename": "image.jpg",
        "user_id": "user123",
        "metadata": {
            "title": "My Image",
            "description": "A beautiful sunset",
            "tags": ["sunset", "nature"],
            "location": "California"
        }
    }
    
    Returns:
        API Gateway response with image_id and upload status
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract required fields
        image_data = body.get('image_data')
        filename = body.get('filename')
        user_id = body.get('user_id')
        metadata = body.get('metadata', {})
        
        # Validate user_id
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return create_error_response(400, error_msg, 'INVALID_USER_ID')
        
        # Validate image file
        is_valid, error_msg = validate_image_file(image_data, filename)
        if not is_valid:
            return create_error_response(400, error_msg, 'INVALID_IMAGE')
        
        # Validate metadata
        is_valid, error_msg = validate_metadata(metadata)
        if not is_valid:
            return create_error_response(400, error_msg, 'INVALID_METADATA')
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Get file extension
        file_extension = filename.rsplit('.', 1)[-1].lower()
        
        # Create S3 key
        s3_key = f"images/{user_id}/{image_id}.{file_extension}"
        
        # Decode image data
        decoded_image = base64.b64decode(image_data)
        
        # Upload to S3
        s3_client = get_s3_client()
        
        # Determine content type
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=decoded_image,
            ContentType=content_type
        )
        
        # Get current timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare DynamoDB item
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        db_item = {
            'image_id': image_id,
            'user_id': user_id,
            's3_key': s3_key,
            'filename': filename,
            'content_type': content_type,
            'file_size': len(decoded_image),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Add optional metadata fields
        if metadata.get('title'):
            db_item['title'] = metadata['title']
        if metadata.get('description'):
            db_item['description'] = metadata['description']
        if metadata.get('tags'):
            db_item['tags'] = metadata['tags']
        if metadata.get('location'):
            db_item['location'] = metadata['location']
        
        # Store metadata in DynamoDB
        table.put_item(Item=db_item)
        
        return create_success_response(
            data={
                'image_id': image_id,
                'filename': filename,
                's3_key': s3_key,
                'created_at': timestamp
            },
            message='Image uploaded successfully',
            status_code=201
        )
        
    except json.JSONDecodeError:
        return create_error_response(400, 'Invalid JSON in request body', 'INVALID_JSON')
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        return create_error_response(500, f'Internal server error: {str(e)}', 'INTERNAL_ERROR')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler entry point."""
    return upload_image(event, context)
