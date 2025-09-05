"""
Web scraping functions for Chrome Extension Analyzer
"""

import random
import re
import requests
from bs4 import BeautifulSoup
from config import USER_AGENTS, REQUEST_TIMEOUT, MAX_RETRIES

def get_random_user_agent():
    """
    Get a random user agent from the configured list.

    Returns:
        str: Random user agent string
    """
    return random.choice(USER_AGENTS)

def make_request(url, max_retries=MAX_RETRIES):
    """
    Make HTTP request with user agent rotation and retry logic.

    Args:
        url (str): URL to request
        max_retries (int): Maximum number of retries

    Returns:
        requests.Response: Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    headers = {'User-Agent': get_random_user_agent()}

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            # Rotate user agent for next attempt
            headers['User-Agent'] = get_random_user_agent()

def fetch_extension_report(extension_id):
    """
    Fetch the extension report, following redirects to latest version.

    Args:
        extension_id (str): Chrome extension ID

    Returns:
        tuple: (html_content, final_url)

    Raises:
        SystemExit: If 404 error or request fails
    """
    base_url = "https://dex.koi.security/reports/chrome/"
    url = f"{base_url}{extension_id}"

    try:
        response = make_request(url)

        # Check for 404 error in HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        error_404 = soup.find('h1', class_='text-4xl font-bold mb-4', string='404')
        if error_404:
            print("404")
            print("Oops! Page not found")
            raise SystemExit(1)

        return response.text, response.url
    except requests.RequestException as e:
        print(f"Error fetching report: {e}")
        raise SystemExit(1)

def parse_blog_for_extension_ids(blog_url):
    """
    Parse a blog URL to extract Chrome extension IDs.

    Args:
        blog_url (str): URL of the blog to parse

    Returns:
        list: List of found extension IDs
    """
    try:
        response = make_request(blog_url)

        # Regex patterns for Chrome extension IDs
        # Pattern 1: Direct 32-character extension ID
        id_pattern = r'\b[a-z0-9]{32}\b'

        # Pattern 2: chrome-extension://[id]
        chrome_ext_pattern = r'chrome-extension://([a-z0-9]{32})'

        # Pattern 3: chrome://extensions/?id=[id]
        chrome_settings_pattern = r'chrome://extensions/\?id=([a-z0-9]{32})'

        text = response.text
        found_ids = set()

        # Find all matches
        found_ids.update(re.findall(id_pattern, text))
        found_ids.update(re.findall(chrome_ext_pattern, text))
        found_ids.update(re.findall(chrome_settings_pattern, text))

        return list(found_ids)

    except requests.RequestException as e:
        print(f"Error fetching blog {blog_url}: {e}")
        return []

def check_chrome_store_status(extension_id):
    """
    Check if extension is listed in Chrome Web Store.

    Args:
        extension_id (str): Chrome extension ID

    Returns:
        tuple: (is_listed, store_url)
    """
    store_url = f"https://chromewebstore.google.com/detail/{extension_id}"

    try:
        response = make_request(store_url)

        # Check if the final URL indicates an error page
        if 'error' in response.url.lower() or 'empty-title' in response.url.lower():
            return False, "https://chromewebstore.google.com/detail/error"

        # Check if the page indicates the extension is not found
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for indicators of a real extension page
        has_install_button = 'install' in response.text.lower() or 'add to chrome' in response.text.lower()
        has_rating = 'rating' in response.text.lower() or 'stars' in response.text.lower()
        has_reviews = 'review' in response.text.lower()

        # If the page lacks basic extension page elements, it's likely not a real extension
        if not (has_install_button or has_rating or has_reviews):
            return False, "https://chromewebstore.google.com/detail/error"

        # Look for the specific error message in the HTML
        if 'this item is not available' in response.text.lower():
            return False, "https://chromewebstore.google.com/detail/error"

        # Additional check: look for other error indicators
        if 'item not found' in response.text.lower() or 'not available' in response.text.lower():
            return False, "https://chromewebstore.google.com/detail/error"

        # If none of the error conditions are met, assume it's listed
        return True, store_url

    except requests.RequestException:
        # On network errors, treat as not listed
        return False, "https://chromewebstore.google.com/detail/error"
