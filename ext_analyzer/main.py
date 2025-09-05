#!/usr/bin/env python3
"""
Chrome Extension Analyzer - Main Entry Point
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import BLOG_URLS
from utils import validate_extension_ids
from cache import load_cache, save_cache, is_cache_fresh
from scraper import parse_blog_for_extension_ids, fetch_extension_report, check_chrome_store_status
from parser import extract_information
from output import print_output, write_json_output, write_csv_output

def main():
    parser = argparse.ArgumentParser(description='Analyze Chrome Extension reports from dex.koi.security')
    parser.add_argument('extension_ids', nargs='+', help='Chrome Extension ID(s) - accepts one or more IDs')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--output', help='Output file for JSON/CSV formats (optional)')

    args = parser.parse_args()

    # Validate extension IDs
    try:
        validated_ids = validate_extension_ids(args.extension_ids)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

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

    # Process extensions
    results = []

    for extension_id in validated_ids:
        print(f"Fetching report for extension ID: {extension_id}")

        try:
            html_content, final_url = fetch_extension_report(extension_id)
            print(f"Final URL: {final_url}")

            extracted_data = extract_information(html_content)

            # Check Chrome Web Store status
            store_status = check_chrome_store_status(extension_id)

            # Output based on format
            print_output(args.format, extension_id, extension_sources, store_status,
                        extracted_data, final_url, results)

        except SystemExit as e:
            # Handle 404 or other fatal errors
            if e.code == 1:
                pass  # Error already printed by fetch_extension_report
            else:
                raise

    # Write to file if specified and format requires it
    if args.output:
        if args.format == 'json':
            write_json_output(results, args.output)
            print(f"\nResults saved to {args.output}")
        elif args.format == 'csv':
            write_csv_output(results, args.output)
            print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
