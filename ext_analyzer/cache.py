"""
Cache management for Chrome Extension Analyzer
"""

import json
import os
import time
from config import CACHE_FILE, CACHE_EXPIRY_HOURS

def load_cache():
    """
    Load cached blog data if it exists and is fresh.

    Returns:
        dict or None: Cache data if fresh, None otherwise
    """
    if not os.path.exists(CACHE_FILE):
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)

        # Check if cache is still fresh
        cache_time = cache_data.get('timestamp', 0)
        current_time = time.time()
        if current_time - cache_time > CACHE_EXPIRY_HOURS * 3600:
            return None

        return cache_data
    except (json.JSONDecodeError, KeyError):
        return None

def save_cache(extension_sources):
    """
    Save extension sources to cache file.

    Args:
        extension_sources (dict): Extension sources data to cache
    """
    cache_data = {
        'timestamp': time.time(),
        'extension_sources': extension_sources
    }

    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except IOError:
        pass  # Silently fail if we can't write cache

def is_cache_fresh():
    """
    Check if cache file exists and is fresh.

    Returns:
        bool: True if cache is fresh, False otherwise
    """
    if not os.path.exists(CACHE_FILE):
        return False

    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)

        cache_time = cache_data.get('timestamp', 0)
        current_time = time.time()
        return current_time - cache_time <= CACHE_EXPIRY_HOURS * 3600
    except (json.JSONDecodeError, KeyError):
        return False
