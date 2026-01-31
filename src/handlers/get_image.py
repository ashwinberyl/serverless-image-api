"""
Lambda handler for viewing/downloading images.
"""
import json
import base64
from typing import Dict, Any

from config import S3_BUCKET_NAME, DYNAMODB_TABLE_NAME
from utils.aws_clients import get_s3_client, get_dynamodb_resource
from utils.validators import validate_image_id
from utils.response_helpers import create_response, create_success_response, create_error_response


def get_image(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for viewing/downloading an image.
    
    Path parameter:
    - image_id: The unique identifier of the image
    
    Query parameters:
    - download: If 'true', returns the image data; otherwise returns metadata and presigned URL
    
    Returns:
        API Gateway response with image data or metadata with presigned URL
    """
    try:
        # Get image_id from path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('image_id')
        
        # Validate image_id
        is_valid, error_msg = validate_image_id(image_id)
        if not is_valid:
            return create_error_response(400, error_msg, 'INVALID_IMAGE_ID')
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        download = query_params.get('download', 'false').lower() == 'true'
        
        # Get metadata from DynamoDB
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        response = table.get_item(Key={'image_id': image_id})
        
        if 'Item' not in response:
            return create_error_response(404, 'Image not found', 'IMAGE_NOT_FOUND')
        
        item = response['Item']
        s3_key = item.get('s3_key')
        
        # Get S3 client
        s3_client = get_s3_client()
        
        if download:
            # Download and return the actual image data
            try:
                s3_response = s3_client.get_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=s3_key
                )
                
                image_data = s3_response['Body'].read()
                encoded_image = base64.b64encode(image_data).decode('utf-8')
                
                return create_response(
                    status_code=200,
                    body={
                        'image_id': image_id,
                        'filename': item.get('filename'),
                        'content_type': item.get('content_type'),
                        'image_data': encoded_image
                    }
                )
                
            except s3_client.exceptions.NoSuchKey:
                return create_error_response(404, 'Image file not found in storage', 'FILE_NOT_FOUND')
        else:
            # Generate presigned URL for viewing
            try:
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': S3_BUCKET_NAME,
                        'Key': s3_key
                    },
                    ExpiresIn=3600  # URL valid for 1 hour
                )
            except Exception as e:
                presigned_url = None
                print(f"Error generating presigned URL: {str(e)}")
            
            # Prepare metadata response (exclude s3_key for security)
            metadata = {
                'image_id': item.get('image_id'),
                'user_id': item.get('user_id'),
                'filename': item.get('filename'),
                'content_type': item.get('content_type'),
                'file_size': item.get('file_size'),
                'title': item.get('title'),
                'description': item.get('description'),
                'tags': item.get('tags'),
                'location': item.get('location'),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at')
            }
            
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            if presigned_url:
                metadata['download_url'] = presigned_url
                metadata['url_expires_in'] = 3600
            
            return create_success_response(data=metadata)
        
    except Exception as e:
        print(f"Error getting image: {str(e)}")
        return create_error_response(500, f'Internal server error: {str(e)}', 'INTERNAL_ERROR')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler entry point."""
    return get_image(event, context)
