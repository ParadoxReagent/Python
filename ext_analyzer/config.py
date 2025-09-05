"""
Configuration constants for Chrome Extension Analyzer
"""

import os

# Blog URLs to parse for extension IDs
BLOG_URLS = [
    "https://www.koi.security/blog/google-and-microsoft-trusted-them-2-3-million-users-installed-them-they-were-malware",
    "https://www.malwarebytes.com/blog/news/2025/07/millions-of-people-spied-on-by-malicious-browser-extensions-in-chrome-and-edge",
    "https://www.esentire.com/security-advisories/reddirection-browser-extension-campaign"
]

# Cache settings
CACHE_FILE = "blog_cache.json"
CACHE_EXPIRY_HOURS = 24

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

# Request settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# Extension ID validation
EXTENSION_ID_PATTERN = r'^[a-z0-9]{32}$'
