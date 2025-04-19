# FetchAnything

A command-line tool to fetch files from websites recursively.

## Installation

You can install FetchAnything using pip:

```bash
pip install fetchanything
```

Or from source:

```bash
git clone https://github.com/yourusername/fetchanything.git
cd fetchanything
pip install -e .
```

## Usage

Basic usage:

```bash
fetchanything <URL> [options]
```

### Options

- `-l, --level LEVEL`: Maximum crawl depth (default: 2)
- `-f, --filter PATTERN`: File pattern to match (e.g., "*.pdf", "*.jpg")
- `-u, --url-pattern PATTERN`: Regex pattern to match URLs for crawling (e.g., ".*/blog/.*")
- `-o, --out DIRECTORY`: Output directory (default: downloads)
- `-v, --verbose`: Enable verbose output

### Examples

1. Download all PDF files from a website up to depth 2:
```bash
fetchanything https://example.com --level 2 --filter "*.pdf" --out download_pdf
```

2. Download all files from a website up to depth 1:
```bash
fetchanything https://example.com --level 1 --out downloads
```

3. Download all images with verbose output:
```bash
fetchanything https://example.com --filter "*.jpg" -v
```

4. Download PDFs only from blog pages:
```bash
fetchanything https://example.com --filter "*.pdf" --url-pattern ".*/blog/.*"
```

5. Download files only from specific subdomain:
```bash
fetchanything https://example.com --url-pattern "https://docs\\.example\\.com/.*"
```

## Features

- Recursive website crawling with depth control
- File pattern matching
- URL pattern filtering
- Progress tracking with tqdm
- Verbose logging option
- Persistent HTTP sessions
- Error handling and graceful interruption

## Requirements

- Python 3.7 or higher
- requests
- beautifulsoup4
- tqdm
- urllib3

## License

MIT License
