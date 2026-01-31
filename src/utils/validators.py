"""
Validation utilities for image uploads and metadata.
"""
import base64
from typing import Dict, Any, Tuple, Optional
from config import ALLOWED_EXTENSIONS, MAX_IMAGE_SIZE_BYTES


def validate_image_file(image_data: str, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate the uploaded image file.
    
    Args:
        image_data: Base64 encoded image data
        filename: Original filename of the image
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not image_data:
        return False, "Image data is required"
    
    if not filename:
        return False, "Filename is required"
    
    # Check file extension
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension not in ALLOWED_EXTENSIONS:
        return False, f"File extension '{extension}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (base64 encoded)
    try:
        decoded_data = base64.b64decode(image_data)
        if len(decoded_data) > MAX_IMAGE_SIZE_BYTES:
            return False, f"Image size exceeds maximum allowed size of {MAX_IMAGE_SIZE_BYTES // (1024*1024)}MB"
    except Exception as e:
        return False, f"Invalid base64 image data: {str(e)}"
    
    return True, None


def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate image metadata.
    
    Args:
        metadata: Dictionary containing image metadata
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not metadata:
        return True, None  # Metadata is optional
    
    if not isinstance(metadata, dict):
        return False, "Metadata must be a dictionary"
    
    # Validate specific fields if present
    if 'title' in metadata and len(str(metadata['title'])) > 256:
        return False, "Title must be 256 characters or less"
    
    if 'description' in metadata and len(str(metadata['description'])) > 2048:
        return False, "Description must be 2048 characters or less"
    
    if 'tags' in metadata:
        if not isinstance(metadata['tags'], list):
            return False, "Tags must be a list"
        if len(metadata['tags']) > 20:
            return False, "Maximum 20 tags allowed"
        for tag in metadata['tags']:
            if not isinstance(tag, str) or len(tag) > 50:
                return False, "Each tag must be a string of 50 characters or less"
    
    return True, None


def validate_image_id(image_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate image ID format.
    
    Args:
        image_id: The image ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not image_id:
        return False, "Image ID is required"
    
    if not isinstance(image_id, str):
        return False, "Image ID must be a string"
    
    if len(image_id) > 128:
        return False, "Image ID is too long"
    
    return True, None


def validate_user_id(user_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user ID format.
    
    Args:
        user_id: The user ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not user_id:
        return False, "User ID is required"
    
    if not isinstance(user_id, str):
        return False, "User ID must be a string"
    
    if len(user_id) > 128:
        return False, "User ID is too long"
    
    return True, None
