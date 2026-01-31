"""
HTTP Response helper functions for Lambda handlers.
"""
import json
from typing import Any, Dict, Optional


def create_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API Gateway response.
    
    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Optional additional headers
        
    Returns:
        API Gateway compatible response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)
    }


def create_error_response(
    status_code: int,
    error_message: str,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Human-readable error message
        error_code: Optional machine-readable error code
        
    Returns:
        API Gateway compatible error response dictionary
    """
    body = {
        'error': {
            'message': error_message
        }
    }
    
    if error_code:
        body['error']['code'] = error_code
    
    return create_response(status_code, body)


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default 200)
        
    Returns:
        API Gateway compatible success response dictionary
    """
    body = {'data': data}
    
    if message:
        body['message'] = message
    
    return create_response(status_code, body)
