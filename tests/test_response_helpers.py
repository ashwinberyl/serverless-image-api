"""
Unit tests for response helper functions.
"""
import pytest
import json
from src.utils.response_helpers import (
    create_response,
    create_error_response,
    create_success_response
)


class TestCreateResponse:
    """Tests for create_response function."""
    
    def test_basic_response(self):
        """Test creating a basic response."""
        response = create_response(200, {'message': 'Hello'})
        
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert 'body' in response
        
        body = json.loads(response['body'])
        assert body['message'] == 'Hello'
    
    def test_response_headers(self):
        """Test default headers are included."""
        response = create_response(200, {})
        
        assert response['headers']['Content-Type'] == 'application/json'
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
    
    def test_custom_headers(self):
        """Test custom headers are merged."""
        custom_headers = {'X-Custom-Header': 'custom-value'}
        response = create_response(200, {}, headers=custom_headers)
        
        assert response['headers']['X-Custom-Header'] == 'custom-value'
        assert response['headers']['Content-Type'] == 'application/json'
    
    def test_different_status_codes(self):
        """Test various HTTP status codes."""
        for code in [200, 201, 400, 401, 403, 404, 500]:
            response = create_response(code, {})
            assert response['statusCode'] == code
    
    def test_complex_body(self):
        """Test serialization of complex body."""
        complex_body = {
            'list': [1, 2, 3],
            'nested': {'key': 'value'},
            'string': 'text'
        }
        response = create_response(200, complex_body)
        body = json.loads(response['body'])
        
        assert body['list'] == [1, 2, 3]
        assert body['nested']['key'] == 'value'


class TestCreateErrorResponse:
    """Tests for create_error_response function."""
    
    def test_error_response_structure(self):
        """Test error response has correct structure."""
        response = create_error_response(400, 'Bad request')
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error']['message'] == 'Bad request'
    
    def test_error_response_with_code(self):
        """Test error response with error code."""
        response = create_error_response(400, 'Bad request', 'VALIDATION_ERROR')
        
        body = json.loads(response['body'])
        assert body['error']['code'] == 'VALIDATION_ERROR'
        assert body['error']['message'] == 'Bad request'
    
    def test_error_response_without_code(self):
        """Test error response without error code."""
        response = create_error_response(500, 'Server error')
        
        body = json.loads(response['body'])
        assert 'code' not in body['error']
    
    def test_common_error_codes(self):
        """Test common HTTP error status codes."""
        error_cases = [
            (400, 'Bad Request'),
            (401, 'Unauthorized'),
            (403, 'Forbidden'),
            (404, 'Not Found'),
            (500, 'Internal Server Error')
        ]
        for status, message in error_cases:
            response = create_error_response(status, message)
            assert response['statusCode'] == status


class TestCreateSuccessResponse:
    """Tests for create_success_response function."""
    
    def test_success_response_structure(self):
        """Test success response has correct structure."""
        response = create_success_response(data={'key': 'value'})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'data' in body
        assert body['data']['key'] == 'value'
    
    def test_success_response_with_message(self):
        """Test success response with message."""
        response = create_success_response(
            data={'id': 1},
            message='Operation successful'
        )
        
        body = json.loads(response['body'])
        assert body['message'] == 'Operation successful'
        assert body['data']['id'] == 1
    
    def test_success_response_without_message(self):
        """Test success response without message."""
        response = create_success_response(data={})
        
        body = json.loads(response['body'])
        assert 'message' not in body
    
    def test_success_response_custom_status_code(self):
        """Test success response with custom status code."""
        response = create_success_response(data={}, status_code=201)
        
        assert response['statusCode'] == 201
    
    def test_success_response_with_list_data(self):
        """Test success response with list data."""
        data = [{'id': 1}, {'id': 2}]
        response = create_success_response(data=data)
        
        body = json.loads(response['body'])
        assert body['data'] == data
