"""
Lambda handler for listing images with filtering support.
"""
import json
from typing import Dict, Any, Optional
from boto3.dynamodb.conditions import Key, Attr

from config import DYNAMODB_TABLE_NAME, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from utils.aws_clients import get_dynamodb_resource
from utils.response_helpers import create_success_response, create_error_response


def list_images(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for listing images with filter support.
    
    Supports the following query parameters:
    - user_id: Filter by user ID (required)
    - title: Filter by title (contains)
    - tags: Filter by tags (comma-separated, any match)
    - location: Filter by location (contains)
    - created_after: Filter by creation date (ISO format)
    - created_before: Filter by creation date (ISO format)
    - limit: Number of results per page (default 20, max 100)
    - last_evaluated_key: For pagination
    
    Returns:
        API Gateway response with list of images and pagination info
    """
    try:
        # Get query parameters
        params = event.get('queryStringParameters') or {}
        
        user_id = params.get('user_id')
        title_filter = params.get('title')
        tags_filter = params.get('tags')
        location_filter = params.get('location')
        created_after = params.get('created_after')
        created_before = params.get('created_before')
        
        # Pagination parameters
        limit = min(int(params.get('limit', DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE)
        last_key = params.get('last_evaluated_key')
        
        # Get DynamoDB table
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        # Build filter expression
        filter_expression = None
        expression_values = {}
        expression_names = {}
        
        # User ID filter (if provided, use query instead of scan)
        if user_id:
            filter_expression = Attr('user_id').eq(user_id)
        
        # Title filter (contains)
        if title_filter:
            title_condition = Attr('title').contains(title_filter)
            filter_expression = title_condition if not filter_expression else filter_expression & title_condition
        
        # Tags filter (any match from comma-separated list)
        if tags_filter:
            tags_list = [tag.strip() for tag in tags_filter.split(',')]
            # Create condition for any tag matching
            tags_condition = None
            for tag in tags_list:
                tag_cond = Attr('tags').contains(tag)
                tags_condition = tag_cond if not tags_condition else tags_condition | tag_cond
            if tags_condition:
                filter_expression = tags_condition if not filter_expression else filter_expression & tags_condition
        
        # Location filter (contains)
        if location_filter:
            location_condition = Attr('location').contains(location_filter)
            filter_expression = location_condition if not filter_expression else filter_expression & location_condition
        
        # Date range filters
        if created_after:
            after_condition = Attr('created_at').gte(created_after)
            filter_expression = after_condition if not filter_expression else filter_expression & after_condition
        
        if created_before:
            before_condition = Attr('created_at').lte(created_before)
            filter_expression = before_condition if not filter_expression else filter_expression & before_condition
        
        # Build scan parameters
        scan_params = {
            'Limit': limit
        }
        
        if filter_expression:
            scan_params['FilterExpression'] = filter_expression
        
        if last_key:
            try:
                scan_params['ExclusiveStartKey'] = json.loads(last_key)
            except json.JSONDecodeError:
                return create_error_response(400, 'Invalid last_evaluated_key format', 'INVALID_PAGINATION')
        
        # Execute scan
        response = table.scan(**scan_params)
        
        # Prepare response
        items = response.get('Items', [])
        
        # Remove s3_key from response (security)
        for item in items:
            if 's3_key' in item:
                del item['s3_key']
        
        result = {
            'images': items,
            'count': len(items),
            'scanned_count': response.get('ScannedCount', 0)
        }
        
        # Add pagination key if more results exist
        if 'LastEvaluatedKey' in response:
            result['last_evaluated_key'] = json.dumps(response['LastEvaluatedKey'])
            result['has_more'] = True
        else:
            result['has_more'] = False
        
        return create_success_response(data=result)
        
    except ValueError as e:
        return create_error_response(400, f'Invalid parameter value: {str(e)}', 'INVALID_PARAMETER')
    except Exception as e:
        print(f"Error listing images: {str(e)}")
        return create_error_response(500, f'Internal server error: {str(e)}', 'INTERNAL_ERROR')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler entry point."""
    return list_images(event, context)
