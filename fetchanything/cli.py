import argparse
import logging
import os
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path

def setup_logging(verbose=False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=level
    )

def is_valid_url(url):
    """Check if the URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_links(url, session):
    """Extract all links from a webpage."""
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return [urljoin(url, link.get('href')) for link in soup.find_all('a')]
    except Exception as e:
        logging.warning(f"Error processing {url}: {str(e)}")
        return []

def should_download(url, pattern):
    """Check if the URL matches the download pattern."""
    return re.match(pattern, url.split('/')[-1]) is not None

def download_file(url, output_dir, session):
    """Download a file from URL to the output directory."""
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        filename = url.split('/')[-1]
        filepath = os.path.join(output_dir, filename)
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                pbar.update(size)
        
        logging.info(f"Downloaded: {filename}")
        return True
    except Exception as e:
        logging.warning(f"Failed to download {url}: {str(e)}")
        return False

def crawl_website(start_url, max_depth, pattern, output_dir, session, visited=None, current_depth=0):
    """Recursively crawl the website and download matching files."""
    if visited is None:
        visited = set()
    
    if current_depth > max_depth or start_url in visited:
        return
    
    visited.add(start_url)
    logging.info(f"Crawling: {start_url} (depth: {current_depth})")
    
    if should_download(start_url, pattern):
        download_file(start_url, output_dir, session)
    
    links = get_links(start_url, session)
    for link in links:
        if is_valid_url(link) and link not in visited:
            crawl_website(link, max_depth, pattern, output_dir, session, visited, current_depth + 1)

def main():
    parser = argparse.ArgumentParser(description='Fetch files from websites recursively')
    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('--level', type=int, default=2, help='Maximum crawl depth (default: 2)')
    parser.add_argument('--filter', default='.*', help='File pattern to match (default: all files)')
    parser.add_argument('--out', default='downloads', help='Output directory (default: downloads)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if not is_valid_url(args.url):
        logging.error("Invalid URL provided")
        return 1
    
    setup_logging(args.verbose)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.out, exist_ok=True)
    
    # Convert filter pattern to regex
    pattern = args.filter.replace('*', '.*')
    if not pattern.startswith('.*'):
        pattern = '.*' + pattern
    
    # Create session for persistent connections
    session = requests.Session()
    
    try:
        crawl_website(args.url, args.level, pattern, args.out, session)
        logging.info("Crawling completed successfully")
        return 0
    except KeyboardInterrupt:
        logging.info("Crawling interrupted by user")
        return 1
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main()) 