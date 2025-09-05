# Chrome Extension Analyzer

A Python command-line tool that fetches and analyzes Chrome extension reports from dex.koi.security.

## Features

- **Blog Analysis**: Parses security blogs to collect extension IDs and their sources
- **Chrome Web Store Status**: Checks if extensions are currently listed in the Chrome Web Store
- **Report Analysis**: Fetches extension reports by ID from https://dex.koi.security/reports/chrome/
- **Automatic Redirects**: Follows redirects to get the latest version
- **Comprehensive Information Extraction**:
  - Analysis Summary
  - Malware version (if present)
  - All Findings
  - Key Insights (when available)
- **Caching System**: Stores blog data for 24 hours to improve performance
- **Batch Processing**: Analyze multiple extensions in a single command

## Installation

1. Ensure you have Python 3.6+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script with one or more Chrome Extension IDs:

```bash
python chrome_extension_analyzer.py <extension_id> [extension_id ...]
```

### Examples

Analyze a single extension:
```bash
python chrome_extension_analyzer.py jghecgabfgfdldnmbfkhmffcabddioke
```

Analyze multiple extensions:
```bash
python chrome_extension_analyzer.py jghecgabfgfdldnmbfkhmffcabddioke kgmeffmlnkfnjpgmdndccklfigfhajen
```

For each extension, the script will:
1. **Check blog sources**: Parse security blogs to find extension references
2. **Verify Chrome Web Store status**: Check if the extension is currently listed
3. **Fetch security report**: Get analysis from https://dex.koi.security/reports/chrome/{extension_id}
4. **Follow redirects**: Automatically handle version-specific URLs
5. **Extract information**: Parse and display comprehensive security analysis

## Output

For each extension, the tool provides comprehensive analysis including:

- **Blog Sources**: Lists which security blogs referenced the extension
- **Chrome Web Store Status**: Shows if the extension is currently listed ("Listed" or "Not Listed")
- **Security Report URL**: The final URL from dex.koi.security after redirects
- **Extracted Information**: Structured analysis including:
  - Extension name
  - Analysis Summary
  - Key Insights
  - Malware version (if applicable)
  - All security findings

### Sample Output

```
=== Extension: jghecgabfgfdldnmbfkhmffcabddioke ===
Source Blog: Extension not found in any analyzed blogs
Chrome Web Store: Listed (https://chromewebstore.google.com/detail/jghecgabfgfdldnmbfkhmffcabddioke)
Fetching report for extension ID: jghecgabfgfdldnmbfkhmffcabddioke
Final URL: https://dex.koi.security/reports/chrome/jghecgabfgfdldnmbfkhmffcabddioke/2.4.0

=== Extracted Information ===

Volume Master

Analysis Summary:
  [Detailed security analysis...]

Findings:
  - [Individual findings...]
```

## Dependencies

- requests: For HTTP requests and redirect handling
- beautifulsoup4: For HTML parsing
- json: For caching blog data (built-in Python module)
- os: For file system operations (built-in Python module)
- time: For cache expiry handling (built-in Python module)
- re: For regex pattern matching (built-in Python module)
- concurrent.futures: For parallel blog processing (built-in Python module)

## Notes

- **Blog Caching**: Extension sources are cached for 24 hours to improve performance
- **Chrome Web Store Integration**: Checks real-time listing status using multiple detection methods
- **Concurrent Processing**: Blogs are parsed in parallel for faster analysis
- **HTML Structure**: Assumes standard HTML structure on target websites
- **Error Handling**: Comprehensive error handling for network issues and parsing failures
- **Updates Required**: If website structures change, parsing logic may need updates

## License

This project is for educational and research purposes.
