"""
HTML parsing functions for Chrome Extension Analyzer
"""

import re
from bs4 import BeautifulSoup

def extract_information(html_content):
    """
    Extract required information from the HTML content using generic HTML structure.

    Args:
        html_content (str): HTML content to parse

    Returns:
        dict: Extracted data dictionary
    """
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
                        # Split on capital letters followed by lowercase (finding titles)
                        parts = re.split(r'([A-Z][a-zA-Z\s]+?)(?=[A-Z][a-zA-Z]|$)', text)
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
