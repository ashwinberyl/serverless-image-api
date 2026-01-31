"""
Unit tests for validator functions.
"""
import pytest
import base64
from src.utils.validators import (
    validate_image_file,
    validate_metadata,
    validate_image_id,
    validate_user_id
)


class TestValidateImageFile:
    """Tests for validate_image_file function."""
    
    def test_valid_image(self, sample_image_base64):
        """Test validation passes for valid image."""
        is_valid, error = validate_image_file(sample_image_base64, 'test.png')
        assert is_valid is True
        assert error is None
    
    def test_empty_image_data(self):
        """Test validation fails for empty image data."""
        is_valid, error = validate_image_file('', 'test.png')
        assert is_valid is False
        assert 'Image data is required' in error
    
    def test_none_image_data(self):
        """Test validation fails for None image data."""
        is_valid, error = validate_image_file(None, 'test.png')
        assert is_valid is False
        assert 'Image data is required' in error
    
    def test_empty_filename(self, sample_image_base64):
        """Test validation fails for empty filename."""
        is_valid, error = validate_image_file(sample_image_base64, '')
        assert is_valid is False
        assert 'Filename is required' in error
    
    def test_none_filename(self, sample_image_base64):
        """Test validation fails for None filename."""
        is_valid, error = validate_image_file(sample_image_base64, None)
        assert is_valid is False
        assert 'Filename is required' in error
    
    def test_invalid_extension(self, sample_image_base64):
        """Test validation fails for invalid file extension."""
        is_valid, error = validate_image_file(sample_image_base64, 'test.pdf')
        assert is_valid is False
        assert 'not allowed' in error
    
    def test_valid_extensions(self, sample_image_base64):
        """Test validation passes for all valid extensions."""
        valid_extensions = ['png', 'jpg', 'jpeg', 'gif', 'webp']
        for ext in valid_extensions:
            is_valid, error = validate_image_file(sample_image_base64, f'test.{ext}')
            assert is_valid is True, f"Extension {ext} should be valid"
    
    def test_invalid_base64(self):
        """Test validation fails for invalid base64 data."""
        is_valid, error = validate_image_file('not-valid-base64!!!', 'test.png')
        assert is_valid is False
        assert 'Invalid base64' in error
    
    def test_no_extension(self, sample_image_base64):
        """Test validation fails for filename without extension."""
        is_valid, error = validate_image_file(sample_image_base64, 'testimage')
        assert is_valid is False
        assert 'not allowed' in error


class TestValidateMetadata:
    """Tests for validate_metadata function."""
    
    def test_valid_metadata(self):
        """Test validation passes for valid metadata."""
        metadata = {
            'title': 'Test Title',
            'description': 'Test Description',
            'tags': ['tag1', 'tag2'],
            'location': 'Test Location'
        }
        is_valid, error = validate_metadata(metadata)
        assert is_valid is True
        assert error is None
    
    def test_empty_metadata(self):
        """Test validation passes for empty metadata."""
        is_valid, error = validate_metadata({})
        assert is_valid is True
        assert error is None
    
    def test_none_metadata(self):
        """Test validation passes for None metadata."""
        is_valid, error = validate_metadata(None)
        assert is_valid is True
        assert error is None
    
    def test_invalid_metadata_type(self):
        """Test validation fails for non-dict metadata."""
        is_valid, error = validate_metadata('not a dict')
        assert is_valid is False
        assert 'must be a dictionary' in error
    
    def test_title_too_long(self):
        """Test validation fails for title > 256 characters."""
        metadata = {'title': 'x' * 257}
        is_valid, error = validate_metadata(metadata)
        assert is_valid is False
        assert 'Title must be 256 characters' in error
    
    def test_description_too_long(self):
        """Test validation fails for description > 2048 characters."""
        metadata = {'description': 'x' * 2049}
        is_valid, error = validate_metadata(metadata)
        assert is_valid is False
        assert 'Description must be 2048 characters' in error
    
    def test_tags_not_list(self):
        """Test validation fails when tags is not a list."""
        metadata = {'tags': 'single-tag'}
        is_valid, error = validate_metadata(metadata)
        assert is_valid is False
        assert 'Tags must be a list' in error
    
    def test_too_many_tags(self):
        """Test validation fails for more than 20 tags."""
        metadata = {'tags': [f'tag{i}' for i in range(21)]}
        is_valid, error = validate_metadata(metadata)
        assert is_valid is False
        assert 'Maximum 20 tags' in error
    
    def test_tag_too_long(self):
        """Test validation fails for tag > 50 characters."""
        metadata = {'tags': ['x' * 51]}
        is_valid, error = validate_metadata(metadata)
        assert is_valid is False
        assert '50 characters or less' in error
    
    def test_tag_not_string(self):
        """Test validation fails for non-string tag."""
        metadata = {'tags': [123]}
        is_valid, error = validate_metadata(metadata)
        assert is_valid is False
        assert 'must be a string' in error


class TestValidateImageId:
    """Tests for validate_image_id function."""
    
    def test_valid_image_id(self):
        """Test validation passes for valid image ID."""
        is_valid, error = validate_image_id('valid-image-id-123')
        assert is_valid is True
        assert error is None
    
    def test_empty_image_id(self):
        """Test validation fails for empty image ID."""
        is_valid, error = validate_image_id('')
        assert is_valid is False
        assert 'Image ID is required' in error
    
    def test_none_image_id(self):
        """Test validation fails for None image ID."""
        is_valid, error = validate_image_id(None)
        assert is_valid is False
        assert 'Image ID is required' in error
    
    def test_image_id_too_long(self):
        """Test validation fails for image ID > 128 characters."""
        is_valid, error = validate_image_id('x' * 129)
        assert is_valid is False
        assert 'too long' in error
    
    def test_non_string_image_id(self):
        """Test validation fails for non-string image ID."""
        is_valid, error = validate_image_id(12345)
        assert is_valid is False
        assert 'must be a string' in error


class TestValidateUserId:
    """Tests for validate_user_id function."""
    
    def test_valid_user_id(self):
        """Test validation passes for valid user ID."""
        is_valid, error = validate_user_id('user123')
        assert is_valid is True
        assert error is None
    
    def test_empty_user_id(self):
        """Test validation fails for empty user ID."""
        is_valid, error = validate_user_id('')
        assert is_valid is False
        assert 'User ID is required' in error
    
    def test_none_user_id(self):
        """Test validation fails for None user ID."""
        is_valid, error = validate_user_id(None)
        assert is_valid is False
        assert 'User ID is required' in error
    
    def test_user_id_too_long(self):
        """Test validation fails for user ID > 128 characters."""
        is_valid, error = validate_user_id('x' * 129)
        assert is_valid is False
        assert 'too long' in error
    
    def test_non_string_user_id(self):
        """Test validation fails for non-string user ID."""
        is_valid, error = validate_user_id(12345)
        assert is_valid is False
        assert 'must be a string' in error
