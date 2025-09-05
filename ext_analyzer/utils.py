"""
Utility functions for Chrome Extension Analyzer
"""

import re
import sys
from config import EXTENSION_ID_PATTERN

def validate_extension_id(extension_id):
    """
    Validate and sanitize extension ID.

    Args:
        extension_id (str): The extension ID to validate

    Returns:
        str: Sanitized extension ID

    Raises:
        ValueError: If extension ID is invalid
    """
    if not extension_id:
        raise ValueError("Extension ID cannot be empty")

    # Sanitize: strip whitespace and convert to lowercase
    sanitized = extension_id.strip().lower()

    # Validate format
    if not re.match(EXTENSION_ID_PATTERN, sanitized):
        raise ValueError(
            f"Invalid extension ID format: '{extension_id}'. "
            "Must be exactly 32 alphanumeric characters (a-z, 0-9)"
        )

    return sanitized

def validate_extension_ids(extension_ids):
    """
    Validate multiple extension IDs.

    Args:
        extension_ids (list): List of extension IDs to validate

    Returns:
        list: List of validated and sanitized extension IDs

    Raises:
        ValueError: If any extension ID is invalid
    """
    validated_ids = []
    errors = []

    for i, ext_id in enumerate(extension_ids):
        try:
            validated_ids.append(validate_extension_id(ext_id))
        except ValueError as e:
            errors.append(f"Extension ID {i+1}: {str(e)}")

    if errors:
        error_msg = "Validation errors:\n" + "\n".join(errors)
        raise ValueError(error_msg)

    return validated_ids

def sanitize_url(url):
    """
    Basic URL sanitization.

    Args:
        url (str): URL to sanitize

    Returns:
        str: Sanitized URL
    """
    if not url:
        return url

    # Strip whitespace
    url = url.strip()

    # Basic validation - should start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL format: '{url}'. Must start with http:// or https://")

    return url
