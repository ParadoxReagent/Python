#!/usr/bin/env python3
"""
Chrome Extension Analyzer
Fetches and analyzes Chrome extension reports from dex.koi.security and blogs
"""

import argparse
import requests
from bs4 import BeautifulSoup
import sys
import re
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Hardcoded list of blog URLs to parse for extension IDs
BLOG_URLS = [
    "https://www.koi.security/blog/google-and-microsoft-trusted-them-2-3-million-users-installed-them-they-were-malware",
    "https://www.malwarebytes.com/blog/news/2025/07/millions-of-people-spied-on-by-malicious-browser-extensions-in-chrome-and-edge",
    "https://www.esentire.com/security-advisories/reddirection-browser-extension-campaign"
]

# Cache settings
CACHE_FILE = "blog_cache.json"
CACHE_EXPIRY_HOURS = 24

def fetch_extension_report(extension_id):
    """Fetch the extension report, following redirects to latest version."""
    base_url = "https://dex.koi.security/reports/chrome/"
    url = f"{base_url}{extension_id}"

    try:
        # Follow redirects to get to the latest version
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()

        # Check for 404 error in HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        error_404 = soup.find('h1', class_='text-4xl font-bold mb-4', string='404')
        if error_404:
            print("404")
            print("Oops! Page not found")
            sys.exit(1)

        return response.text, response.url
    except requests.RequestException as e:
        print(f"Error fetching report: {e}")
        sys.exit(1)

def extract_information(html_content):
    """Extract required information from the HTML content using generic HTML structure."""
    soup = BeautifulSoup(html_content, 'html.parser')

    extracted_data = {}

    # Extract extension name from the main h1 header
    extension_name_h1 = soup.find('h1', class_=lambda x: x and 'text-2xl' in x and 'font-medium' in x)
    if extension_name_h1:
        extracted_data['Extension Name'] = extension_name_h1.get_text(strip=True)
    else:
        # Fallback: find any h1 that might contain the extension name
        main_h1 = soup.find('h1')
        if main_h1:
            extracted_data['Extension Name'] = main_h1.get_text(strip=True)

    # Find Analysis Summary section
    analysis_header = soup.find(['h2', 'h3'], string=lambda text: text and 'analysis summary' in text.lower())
    if analysis_header:
        # Get all content until next h2/h3 header
        content_parts = []
        current = analysis_header.find_next()
        while current and current.name not in ['h2', 'h3']:
            if current.name in ['p', 'div'] and current.get_text(strip=True):
                text = current.get_text(strip=True)
                content_parts.append(text)
            current = current.find_next()

        if content_parts:
            full_content = ' '.join(content_parts)
            # Split Analysis Summary and Key Insights
            if 'key insights:' in full_content.lower():
                parts = full_content.split('Key insights:', 1)
                extracted_data['Analysis Summary'] = parts[0].strip()

                # Extract Key Insights - clean up duplicates and extra content
                insights_text = parts[1].strip()
                # Remove any content after "Malware versions" or similar section markers
                insights_text = insights_text.split('Malware versions')[0].strip()
                insights_text = insights_text.split('This extension')[0].strip()

                # Split by periods and filter
                raw_insights = insights_text.split('.')
                insights = []
                for insight in raw_insights:
                    insight = insight.strip()
                    if insight and len(insight) > 10 and not insight.startswith('Key insights:'):
                        insights.append(insight)

                if insights:
                    extracted_data['Key Insights'] = insights
            else:
                extracted_data['Analysis Summary'] = full_content

    # Find Malware Version section
    malware_header = soup.find(['h2', 'h3'], string=lambda text: text and 'malware version' in text.lower())
    if malware_header:
        # Get the next content element
        next_elem = malware_header.find_next()
        if next_elem and next_elem.get_text(strip=True):
            content = next_elem.get_text(strip=True)
            # Extract version number (e.g., "0.1.6.6" from "0.1.6.6Now Viewingmalware")
            import re
            version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', content)
            if version_match:
                extracted_data['Malware version'] = version_match.group(1)
            else:
                extracted_data['Malware version'] = content

    # Extract Findings section
    findings = []
    findings_header = soup.find(['h2', 'h3'], string=lambda text: text and 'findings' in text.lower())
    if findings_header:
        current = findings_header.find_next()
        while current and current.name not in ['h2', 'h3']:
            if current.name in ['p', 'div'] and current.get_text(strip=True):
                text = current.get_text(strip=True)
                if text and not 'enterprise' in text.lower() and not 'get started' in text.lower():
                    # Parse individual findings - look for h3 headers within findings
                    finding_headers = current.find_all('h3')
                    if finding_headers:
                        for header in finding_headers:
                            finding_title = header.get_text(strip=True)
                            if finding_title and len(finding_title) > 3:
                                # Get the description paragraph that follows this h3
                                next_elem = header.find_next('p')
                                if next_elem:
                                    description = next_elem.get_text(strip=True)
                                    findings.append(f"{finding_title}: {description}")
                                else:
                                    findings.append(finding_title)
                    else:
                        # Fallback: parse from concatenated text
                        import re
                        # Split on capital letters followed by lowercase (finding titles)
                        parts = re.split(r'([A-Z][a-zA-Z\s]+?)(?=[A-Z][a-zA-Z\s]|$)', text)
                        for part in parts:
                            part = part.strip()
                            if part and len(part) > 3 and not part.startswith('Flags'):
                                findings.append(part)

            current = current.find_next()

    if findings:
        # Remove duplicates while preserving order
        seen = set()
        unique_findings = []
        for finding in findings:
            if finding not in seen:
                seen.add(finding)
                unique_findings.append(finding)
        extracted_data['Findings'] = unique_findings

    return extracted_data

def parse_blog_for_extension_ids(blog_url):
    """Parse a blog URL to extract Chrome extension IDs."""
    try:
        response = requests.get(blog_url)
        response.raise_for_status()

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

def load_cache():
    """Load cached blog data if it exists and is fresh."""
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
    """Save extension sources to cache file."""
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
    """Check if cache file exists and is fresh."""
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

def check_chrome_store_status(extension_id):
    """Check if extension is listed in Chrome Web Store."""
    store_url = f"https://chromewebstore.google.com/detail/{extension_id}"

    try:
        response = requests.get(store_url, timeout=10, allow_redirects=True)
        response.raise_for_status()

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

        # If no error indicators and we got a 200 response, assume it's listed
        return True, store_url

    except requests.RequestException:
        # On network errors, treat as not listed
        return False, "https://chromewebstore.google.com/detail/error"

def main():
    parser = argparse.ArgumentParser(description='Analyze Chrome Extension reports from dex.koi.security')
    parser.add_argument('extension_ids', nargs='+', help='Chrome Extension ID(s) - accepts one or more IDs')
    args = parser.parse_args()

    # Try to load from cache first
    extension_sources = {}
    cache_loaded = False

    if is_cache_fresh():
        cache_data = load_cache()
        if cache_data:
            extension_sources = cache_data.get('extension_sources', {})
            print(f"Loaded {len(extension_sources)} extension IDs from cache.")
            cache_loaded = True

    if not cache_loaded:
        # Parse blogs concurrently to collect extension IDs and their source URLs
        print("Parsing blogs for extension IDs...")
        extension_sources = {}

        with ThreadPoolExecutor(max_workers=len(BLOG_URLS)) as executor:
            # Submit all blog parsing tasks
            future_to_url = {executor.submit(parse_blog_for_extension_ids, url): url for url in BLOG_URLS}

            # Process results as they complete
            for future in as_completed(future_to_url):
                blog_url = future_to_url[future]
                try:
                    found_ids = future.result()
                    print(f"  Processed: {blog_url} ({len(found_ids)} IDs found)")
                    for ext_id in found_ids:
                        if ext_id not in extension_sources:
                            extension_sources[ext_id] = []
                        extension_sources[ext_id].append(blog_url)
                except Exception as e:
                    print(f"  Error processing {blog_url}: {e}")

        # Save to cache
        save_cache(extension_sources)
        print(f"Found {len(extension_sources)} unique extension IDs across all blogs.\n")
    else:
        print()

    for extension_id in args.extension_ids:
        print(f"\n=== Extension: {extension_id} ===")

        # Check if extension was found in blogs
        if extension_id in extension_sources:
            blogs = extension_sources[extension_id]
            if len(blogs) == 1:
                print(f"Source Blog: {blogs[0]}")
            else:
                print("Source Blogs:")
                for blog in blogs:
                    print(f"  - {blog}")
        else:
            print("Source Blog: Extension not found in any analyzed blogs")

        # Check Chrome Web Store status
        is_listed, store_url = check_chrome_store_status(extension_id)
        if is_listed:
            print(f"Chrome Web Store: Listed ({store_url})")
        else:
            print(f"Chrome Web Store: Not Listed ({store_url})")

        print(f"Fetching report for extension ID: {extension_id}")

        html_content, final_url = fetch_extension_report(extension_id)
        print(f"Final URL: {final_url}")

        extracted_data = extract_information(html_content)

        print("\n=== Extracted Information ===")

        # Print extension name first if available
        if 'Extension Name' in extracted_data:
            print(f"\n{extracted_data['Extension Name']}")

        for key, value in extracted_data.items():
            if key != 'Extension Name':  # Skip extension name as it's already printed
                print(f"\n{key}:")
                if isinstance(value, list):
                    for item in value:
                        print(f"  - {item}")
                else:
                    print(f"  {value}")
        print()  # Add blank line between extensions

if __name__ == "__main__":
    main()
