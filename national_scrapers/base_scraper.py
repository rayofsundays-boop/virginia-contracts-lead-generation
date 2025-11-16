"""
Enhanced BaseScraper for National Procurement System
Supports JSON, RSS, XML, HTML parsing with robust error handling
"""

import requests
import logging
import time
import socket
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import feedparser
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseScraper:
    """
    Foundation class for all national procurement scrapers.
    Handles HTTP requests, retries, parsing, and error handling.
    """
    
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    CLEANING_KEYWORDS = [
        'janitorial', 'custodial', 'cleaning', 'housekeeping', 
        'sanitation', 'facilities maintenance', 'building maintenance',
        'floor care', 'carpet cleaning', 'window cleaning',
        'disinfection', 'environmental services', 'porter'
    ]
    
    NAICS_CODES = {
        '561720': 'Janitorial Services',
        '561210': 'Facilities Support Services',
        '561790': 'Other Services to Buildings and Dwellings',
        '238990': 'All Other Specialty Trade Contractors'
    }
    
    def __init__(self, source_name: str):
        """
        Initialize scraper with source identification.
        
        Args:
            source_name: Identifier for this scraper (e.g., 'symphony', 'demandstar')
        """
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        logger.info(f"Initialized {source_name} scraper")
    
    def fetch_page(self, url: str, method: str = 'GET', data: Optional[Dict] = None,
                   headers: Optional[Dict] = None, timeout: int = 30,
                   max_retries: int = 3) -> Optional[requests.Response]:
        """
        Fetch a page with retry logic and comprehensive error handling.
        
        Args:
            url: Target URL
            method: HTTP method (GET or POST)
            data: POST data if applicable
            headers: Additional headers
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts
            
        Returns:
            Response object or None if failed
        """
        if headers:
            request_headers = {**self.session.headers, **headers}
        else:
            request_headers = self.session.headers
        
        for attempt in range(max_retries):
            try:
                if method.upper() == 'POST':
                    response = self.session.post(url, data=data, headers=request_headers, timeout=timeout)
                else:
                    response = self.session.get(url, headers=request_headers, timeout=timeout)
                
                # Handle various HTTP status codes
                if response.status_code == 200:
                    return response
                
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden for {url}, retrying with enhanced headers (attempt {attempt + 1}/{max_retries})")
                    # Add additional headers for retry
                    request_headers['Referer'] = urljoin(url, '/')
                    request_headers['Origin'] = urljoin(url, '/')
                    time.sleep(5)
                    continue
                
                elif response.status_code == 404:
                    logger.error(f"404 Not Found: {url} - URL may have changed")
                    return None
                
                elif response.status_code == 429:
                    logger.warning(f"429 Rate Limited for {url}, waiting 30 seconds...")
                    time.sleep(30)
                    continue
                
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    return None
                    
            except socket.gaierror as e:
                logger.error(f"DNS failure for {url}: {e}")
                return None
            
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {url} (attempt {attempt + 1}/{max_retries})")
                time.sleep(10 * (attempt + 1))  # Exponential backoff
                continue
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                return None
        
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    def parse_html(self, response: requests.Response) -> Optional[BeautifulSoup]:
        """
        Parse HTML response into BeautifulSoup object.
        
        Args:
            response: HTTP response object
            
        Returns:
            BeautifulSoup object or None
        """
        try:
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return None
    
    def parse_json(self, response: requests.Response) -> Optional[Dict]:
        """
        Parse JSON response.
        
        Args:
            response: HTTP response object
            
        Returns:
            Dict or None
        """
        try:
            return response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return None
    
    def parse_rss(self, url: str) -> Optional[feedparser.FeedParserDict]:
        """
        Parse RSS/Atom feed.
        
        Args:
            url: RSS feed URL
            
        Returns:
            Feedparser dict or None
        """
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                logger.warning(f"RSS feed has issues: {feed.bozo_exception}")
            return feed
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {url}: {e}")
            return None
    
    def is_cleaning_related(self, text: str) -> bool:
        """
        Check if text contains cleaning-related keywords.
        
        Args:
            text: Text to search
            
        Returns:
            True if cleaning-related
        """
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.CLEANING_KEYWORDS)
    
    def get_naics_description(self, naics_code: str) -> Optional[str]:
        """
        Get description for NAICS code.
        
        Args:
            naics_code: NAICS code string
            
        Returns:
            Description or None
        """
        return self.NAICS_CODES.get(naics_code)
    
    def standardize_contract(self, state: str, title: str, solicitation_number: str,
                            due_date: str, link: str, agency: str = "",
                            **kwargs) -> Dict[str, Any]:
        """
        Create standardized contract object.
        
        Args:
            state: State abbreviation (2 letters)
            title: Contract title
            solicitation_number: Solicitation/bid number
            due_date: Due date (ISO format preferred)
            link: URL to opportunity
            agency: Issuing agency
            **kwargs: Additional fields
            
        Returns:
            Standardized dict
        """
        contract = {
            'state': state.upper() if state else 'US',
            'title': title.strip() if title else 'No Title',
            'solicitation_number': solicitation_number.strip() if solicitation_number else 'N/A',
            'due_date': self.normalize_date(due_date),
            'link': link.strip() if link else '',
            'agency': agency.strip() if agency else 'N/A',
            'source': self.source_name,
            'scraped_at': datetime.utcnow().isoformat()
        }
        
        # Add any additional fields
        contract.update(kwargs)
        
        return contract
    
    def normalize_date(self, date_str: str) -> str:
        """
        Normalize date to ISO format (YYYY-MM-DD).
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            ISO date string or original if parsing fails
        """
        if not date_str:
            return ""
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%m-%d-%Y',
            '%Y/%m/%d',
            '%b %d, %Y',
            '%B %d, %Y',
            '%d-%b-%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return date_str
    
    def normalize_state(self, state: str) -> str:
        """
        Normalize state name to 2-letter abbreviation.
        
        Args:
            state: State name or abbreviation
            
        Returns:
            2-letter state code
        """
        if not state:
            return 'US'
        
        state = state.strip().upper()
        
        # Already 2-letter code
        if len(state) == 2:
            return state
        
        # State name to abbreviation mapping
        state_map = {
            'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
            'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
            'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
            'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
            'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
            'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
            'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
            'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
            'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
            'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
            'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
            'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
            'WISCONSIN': 'WI', 'WYOMING': 'WY', 'WASHINGTON DC': 'DC', 'DISTRICT OF COLUMBIA': 'DC'
        }
        
        return state_map.get(state, state[:2])
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method - must be implemented by subclasses.
        
        Returns:
            List of standardized contract dicts
        """
        raise NotImplementedError("Subclasses must implement scrape() method")
