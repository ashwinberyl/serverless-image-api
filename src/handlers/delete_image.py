"""
Lambda handler for deleting images.
"""
import json
from typing import Dict, Any

from config import S3_BUCKET_NAME, DYNAMODB_TABLE_NAME
from utils.aws_clients import get_s3_client, get_dynamodb_resource
from utils.validators import validate_image_id, validate_user_id
from utils.response_helpers import create_success_response, create_error_response


def delete_image(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for deleting an image.
    
    Path parameter:
    - image_id: The unique identifier of the image to delete
    
    Query parameter (optional):
    - user_id: The user ID for authorization check
    
    Returns:
        API Gateway response confirming deletion
    """
    try:
        # Get image_id from path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('image_id')
        
        # Validate image_id
        is_valid, error_msg = validate_image_id(image_id)
        if not is_valid:
            return create_error_response(400, error_msg, 'INVALID_IMAGE_ID')
        
        # Get user_id from query parameters (for authorization)
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        
        # Get metadata from DynamoDB
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        response = table.get_item(Key={'image_id': image_id})
        
        if 'Item' not in response:
            return create_error_response(404, 'Image not found', 'IMAGE_NOT_FOUND')
        
        item = response['Item']
        
        # Authorization check: ensure user owns the image (if user_id provided)
        if user_id and item.get('user_id') != user_id:
            return create_error_response(403, 'Not authorized to delete this image', 'FORBIDDEN')
        
        s3_key = item.get('s3_key')
        
        # Delete from S3
        s3_client = get_s3_client()
        try:
            s3_client.delete_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key
            )
        except Exception as e:
            print(f"Warning: Could not delete S3 object {s3_key}: {str(e)}")
            # Continue with DynamoDB deletion even if S3 fails
        
        # Delete from DynamoDB
        table.delete_item(Key={'image_id': image_id})
        
        return create_success_response(
            data={
                'image_id': image_id,
                'deleted': True
            },
            message='Image deleted successfully'
        )
        
    except Exception as e:
        print(f"Error deleting image: {str(e)}")
        return create_error_response(500, f'Internal server error: {str(e)}', 'INTERNAL_ERROR')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler entry point."""
    return delete_image(event, context)
