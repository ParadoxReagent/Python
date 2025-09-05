"""
Output formatting functions for Chrome Extension Analyzer
"""

import csv
import json
import sys
from typing import Dict, List, Any

def format_text_output(extension_id: str, extension_sources: Dict[str, List[str]],
                      store_status: tuple, extracted_data: Dict[str, Any],
                      final_url: str) -> str:
    """
    Format output as human-readable text.

    Args:
        extension_id: Chrome extension ID
        extension_sources: Dictionary of extension sources
        store_status: Tuple of (is_listed, store_url)
        extracted_data: Extracted extension data
        final_url: Final URL of the report

    Returns:
        str: Formatted text output
    """
    output_lines = []

    output_lines.append(f"\n=== Extension: {extension_id} ===")

    # Source information
    if extension_id in extension_sources:
        blogs = extension_sources[extension_id]
        if len(blogs) == 1:
            output_lines.append(f"Source Blog: {blogs[0]}")
        else:
            output_lines.append("Source Blogs:")
            for blog in blogs:
                output_lines.append(f"  - {blog}")
    else:
        output_lines.append("Source Blog: Extension not found in any analyzed blogs")

    # Chrome Web Store status
    is_listed, store_url = store_status
    if is_listed:
        output_lines.append(f"Chrome Web Store: Listed ({store_url})")
    else:
        output_lines.append(f"Chrome Web Store: Not Listed ({store_url})")

    output_lines.append(f"Final URL: {final_url}")
    output_lines.append("\n=== Extracted Information ===")

    # Extension name
    if 'Extension Name' in extracted_data:
        output_lines.append(f"\n{extracted_data['Extension Name']}")

    # Other data
    for key, value in extracted_data.items():
        if key != 'Extension Name':
            output_lines.append(f"\n{key}:")
            if isinstance(value, list):
                for item in value:
                    output_lines.append(f"  - {item}")
            else:
                output_lines.append(f"  {value}")

    output_lines.append("")  # Add blank line between extensions

    return "\n".join(output_lines)

def format_json_output(extension_id: str, extension_sources: Dict[str, List[str]],
                      store_status: tuple, extracted_data: Dict[str, Any],
                      final_url: str) -> Dict[str, Any]:
    """
    Format output as JSON-compatible dictionary.

    Args:
        extension_id: Chrome extension ID
        extension_sources: Dictionary of extension sources
        store_status: Tuple of (is_listed, store_url)
        extracted_data: Extracted extension data
        final_url: Final URL of the report

    Returns:
        dict: JSON-compatible output data
    """
    is_listed, store_url = store_status

    return {
        "extension_id": extension_id,
        "source_blogs": extension_sources.get(extension_id, []),
        "chrome_web_store": {
            "listed": is_listed,
            "url": store_url
        },
        "report_url": final_url,
        "extracted_data": extracted_data
    }

def format_csv_header() -> List[str]:
    """
    Get CSV header row.

    Returns:
        list: CSV header fields
    """
    return [
        "extension_id",
        "source_blogs",
        "chrome_web_store_listed",
        "chrome_web_store_url",
        "report_url",
        "extension_name",
        "analysis_summary",
        "key_insights",
        "malware_version",
        "findings"
    ]

def format_csv_row(extension_id: str, extension_sources: Dict[str, List[str]],
                  store_status: tuple, extracted_data: Dict[str, Any],
                  final_url: str) -> List[str]:
    """
    Format a single row for CSV output.

    Args:
        extension_id: Chrome extension ID
        extension_sources: Dictionary of extension sources
        store_status: Tuple of (is_listed, store_url)
        extracted_data: Extracted extension data
        final_url: Final URL of the report

    Returns:
        list: CSV row data
    """
    is_listed, store_url = store_status

    return [
        extension_id,
        "; ".join(extension_sources.get(extension_id, [])),
        str(is_listed),
        store_url,
        final_url,
        extracted_data.get('Extension Name', ''),
        extracted_data.get('Analysis Summary', ''),
        "; ".join(extracted_data.get('Key Insights', [])) if isinstance(extracted_data.get('Key Insights'), list) else extracted_data.get('Key Insights', ''),
        extracted_data.get('Malware version', ''),
        "; ".join(extracted_data.get('Findings', [])) if isinstance(extracted_data.get('Findings'), list) else str(extracted_data.get('Findings', ''))
    ]

def write_csv_output(results: List[Dict[str, Any]], filename: str = "extensions_report.csv"):
    """
    Write results to CSV file.

    Args:
        results: List of result dictionaries from format_json_output
        filename: Output filename
    """
    if not results:
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(format_csv_header())

        for result in results:
            row = format_csv_row(
                result["extension_id"],
                {result["extension_id"]: result["source_blogs"]},
                (result["chrome_web_store"]["listed"], result["chrome_web_store"]["url"]),
                result["extracted_data"],
                result["report_url"]
            )
            writer.writerow(row)

def write_json_output(results: List[Dict[str, Any]], filename: str = "extensions_report.json"):
    """
    Write results to JSON file.

    Args:
        results: List of result dictionaries from format_json_output
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(results, jsonfile, indent=2, ensure_ascii=False)

def print_output(output_format: str, extension_id: str, extension_sources: Dict[str, List[str]],
                store_status: tuple, extracted_data: Dict[str, Any], final_url: str,
                results_list: List[Dict[str, Any]] = None):
    """
    Print or save output based on format.

    Args:
        output_format: Output format ('text', 'json', 'csv')
        extension_id: Chrome extension ID
        extension_sources: Dictionary of extension sources
        store_status: Tuple of (is_listed, store_url)
        extracted_data: Extracted extension data
        final_url: Final URL of the report
        results_list: List to append JSON results to (for batch processing)
    """
    if output_format == 'json':
        json_data = format_json_output(extension_id, extension_sources, store_status, extracted_data, final_url)
        if results_list is not None:
            results_list.append(json_data)
            # Print individual JSON results for immediate feedback
            print(json.dumps(json_data, indent=2))
        else:
            print(json.dumps(json_data, indent=2))
    elif output_format == 'csv':
        if results_list is not None:
            json_data = format_json_output(extension_id, extension_sources, store_status, extracted_data, final_url)
            results_list.append(json_data)
            # For CSV, we don't print individual results since they're saved to file
    else:  # text format
        text_output = format_text_output(extension_id, extension_sources, store_status, extracted_data, final_url)
        print(text_output)
