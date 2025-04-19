import argparse
import logging
import os
import re
from urllib.parse import urljoin, urlparse, unquote
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path
import mimetypes

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

def matches_url_pattern(url, pattern):
    """Check if the URL matches the given pattern."""
    if not pattern:
        return True
    try:
        # Convert the pattern to a proper regex
        regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
        if not regex_pattern.startswith('.*'):
            regex_pattern = '.*' + regex_pattern
        if not regex_pattern.endswith('.*'):
            regex_pattern = regex_pattern + '.*'
        logging.debug(f"Checking URL {url} against pattern {regex_pattern}")
        return re.search(regex_pattern, url) is not None
    except re.error:
        logging.warning(f"Invalid URL pattern: {pattern}")
        return False

def get_links(url, session):
    """Extract all links from a webpage."""
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        logging.debug(f"Processing page: {url}")
        
        # Find all links (a tags)
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                links.append(full_url)
                logging.debug(f"Found link: {full_url}")
        
        # Find other potential file links
        for tag in ['img', 'video', 'audio', 'source', 'link']:
            for elem in soup.find_all(tag):
                src = elem.get('src') or elem.get('href')
                if src:
                    full_url = urljoin(url, src)
                    links.append(full_url)
                    logging.debug(f"Found {tag} link: {full_url}")
        
        unique_links = list(set(links))  # Remove duplicates
        logging.debug(f"Found {len(unique_links)} unique links on page {url}")
        return unique_links
    except Exception as e:
        logging.warning(f"Error processing {url}: {str(e)}")
        return []

def should_download(url, pattern):
    """Check if the URL matches the download pattern."""
    try:
        # Get filename from URL
        path = unquote(urlparse(url).path)
        filename = os.path.basename(path)
        
        logging.debug(f"Checking URL: {url}")
        logging.debug(f"Filename: {filename}")
        logging.debug(f"Pattern: {pattern}")
        
        # If filename matches pattern, return True
        if re.match(pattern, filename):
            logging.info(f"URL {url} matches filename pattern")
            return True
            
        # Check content type
        try:
            head = requests.head(url, allow_redirects=True)
            content_type = head.headers.get('content-type', '').lower()
            content_disp = head.headers.get('content-disposition', '').lower()
            
            logging.debug(f"Content-Type: {content_type}")
            logging.debug(f"Content-Disposition: {content_disp}")
            
            # If it's a file type we're looking for
            if pattern != '.*':
                ext = pattern.replace('.*\\', '').replace('*', '').replace('.', '')
                if ext and f'/{ext}' in content_type:
                    logging.info(f"URL {url} matches content type pattern")
                    return True
            
            # If it looks like a file download
            if 'attachment' in content_disp:
                logging.info(f"URL {url} has content-disposition: attachment")
                return True
                
        except Exception as e:
            logging.debug(f"Error checking content type for {url}: {str(e)}")
            
        logging.debug(f"URL {url} does not match any download criteria")
        return False
    except Exception as e:
        logging.debug(f"Error in should_download for {url}: {str(e)}")
        return False

def download_file(url, output_dir, session):
    """Download a file from URL to the output directory."""
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        # Try to get filename from content-disposition header
        content_disp = response.headers.get('content-disposition')
        if content_disp:
            fname = re.findall("filename=(.+)", content_disp)
            if fname:
                filename = unquote(fname[0].strip('"'))
            else:
                filename = unquote(os.path.basename(urlparse(url).path))
        else:
            filename = unquote(os.path.basename(urlparse(url).path))
        
        # If no extension in filename but we know the content-type, add extension
        if '.' not in filename:
            content_type = response.headers.get('content-type', '')
            ext = mimetypes.guess_extension(content_type)
            if ext:
                filename += ext
        
        # Ensure filename is valid
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        if not filename:
            filename = 'downloaded_file'
        
        filepath = os.path.join(output_dir, filename)
        
        # If file exists, add number to filename
        counter = 1
        while os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(output_dir, f"{name}_{counter}{ext}")
            counter += 1
        
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

def crawl_website(start_url, max_depth, pattern, output_dir, session, url_pattern=None, visited=None, current_depth=0):
    """Recursively crawl the website and download matching files."""
    if visited is None:
        visited = set()
    
    # Only check depth for non-file URLs
    is_file = should_download(start_url, pattern)
    if not is_file and current_depth > max_depth:
        logging.debug(f"Skipping {start_url} - exceeded max depth: {current_depth} > {max_depth}")
        return
    
    if start_url in visited:
        logging.debug(f"Skipping {start_url} - already visited")
        return
    
    visited.add(start_url)
    logging.info(f"Crawling: {start_url} (depth: {current_depth})")
    
    # Check if this URL is a file we should download
    if is_file:
        logging.info(f"Found matching file: {start_url}")
        download_file(start_url, output_dir, session)
        return  # Don't crawl further from file URLs
    
    # Get all links from the page
    links = get_links(start_url, session)
    for link in links:
        if is_valid_url(link) and link not in visited and matches_url_pattern(link, url_pattern):
            logging.debug(f"Following link: {link}")
            crawl_website(link, max_depth, pattern, output_dir, session, url_pattern, visited, current_depth + 1)
        else:
            logging.debug(f"Skipping link: {link} - valid: {is_valid_url(link)}, visited: {link in visited}, matches pattern: {matches_url_pattern(link, url_pattern)}")

def main():
    parser = argparse.ArgumentParser(description='Fetch files from websites recursively')
    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('-l', '--level', type=int, default=2, help='Maximum crawl depth (default: 2)')
    parser.add_argument('-f', '--filter', default='.*', help='File pattern to match (default: all files)')
    parser.add_argument('-u', '--url-pattern', help='Regex pattern to match URLs for crawling')
    parser.add_argument('-o', '--out', default='downloads', help='Output directory (default: downloads)')
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
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        crawl_website(args.url, args.level, pattern, args.out, session, args.url_pattern)
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