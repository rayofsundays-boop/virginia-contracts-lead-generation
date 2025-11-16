"""
Base Scraper Class - MODERNIZED 2025
Foundation for all procurement portal scrapers with robust error handling
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import socket
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Custom exception for scraper errors"""
    pass


class BaseScraper:
    """Base class for all government procurement scrapers - MODERNIZED"""
    
    # Standard headers for all requests
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    def __init__(self, name: str, base_url: str, rate_limit: float = 2.0, max_retries: int = 3):
        """
        Initialize base scraper with modern error handling
        
        Args:
            name: Scraper identifier
            base_url: Base URL for portal
            rate_limit: Seconds between requests
            max_retries: Maximum retry attempts for failed requests
        """
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self._last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
    
    def _rate_limit_delay(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()
    
    def fetch_page(self, url: str, method: str = 'GET', data: Dict = None, 
                   headers: Dict = None, max_retries: int = None) -> Optional[str]:
        """
        Fetch a web page with robust error handling - MODERNIZED 2025
        
        Handles:
        - 403 Forbidden (retries with different headers)
        - 404 Not Found (logs and returns None)
        - DNS failures (catches socket errors)
        - Timeouts (30s default)
        - JS-rendered sites (detects and warns)
        
        Args:
            url: URL to fetch
            method: HTTP method ('GET' or 'POST')
            data: POST data (form or JSON)
            headers: Additional headers to merge
            max_retries: Override default retry count
            
        Returns:
            HTML content string or None if failed
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        # Merge custom headers with defaults
        request_headers = self.DEFAULT_HEADERS.copy()
        if headers:
            request_headers.update(headers)
        
        for attempt in range(max_retries):
            try:
                self._rate_limit_delay()
                
                logger.info(f"[{self.name}] {method} {url} (attempt {attempt + 1}/{max_retries})")
                
                if method.upper() == 'POST':
                    response = self.session.post(url, data=data, headers=request_headers, 
                                                timeout=30, allow_redirects=True)
                else:
                    response = self.session.get(url, headers=request_headers, 
                                               timeout=30, allow_redirects=True)
                
                # Handle specific status codes
                if response.status_code == 403:
                    logger.warning(f"[{self.name}] ⚠️  403 Forbidden - may need authentication or different headers")
                    if attempt < max_retries - 1:
                        # Try with more aggressive headers
                        request_headers["Referer"] = self.base_url
                        request_headers["Origin"] = self.base_url
                        wait_time = (attempt + 1) * 5
                        logger.info(f"[{self.name}] Retrying in {wait_time}s with enhanced headers...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                elif response.status_code == 404:
                    logger.error(f"[{self.name}] ❌ 404 Not Found - URL may have changed: {url}")
                    return None
                
                elif response.status_code == 429:
                    logger.warning(f"[{self.name}] ⚠️  429 Rate Limited")
                    if attempt < max_retries - 1:
                        wait_time = 30  # Wait longer for rate limits
                        logger.info(f"[{self.name}] Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                response.raise_for_status()
                
                html = response.text
                
                # Detect JS-rendered sites
                if self._is_js_rendered(html):
                    logger.warning(f"[{self.name}] ⚠️  JS-RENDERED SITE DETECTED - May need Playwright/Selenium")
                
                logger.info(f"[{self.name}] ✅ Success ({len(html)} chars, {response.status_code})")
                return html
                
            except socket.gaierror as e:
                logger.error(f"[{self.name}] ❌ DNS_ERROR: {e} - Domain may be dead")
                return None
                
            except requests.Timeout:
                logger.warning(f"[{self.name}] ⚠️  Timeout after 30s")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    time.sleep(wait_time)
                    continue
                return None
                
            except requests.ConnectionError as e:
                logger.warning(f"[{self.name}] ⚠️  Connection error: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    time.sleep(wait_time)
                    continue
                return None
                
            except requests.RequestException as e:
                logger.warning(f"[{self.name}] ⚠️  Request failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    time.sleep(wait_time)
                    continue
                return None
        
        logger.error(f"[{self.name}] ❌ Failed after {max_retries} attempts")
        return None
    
    def _is_js_rendered(self, html: str) -> bool:
        """Detect if site requires JavaScript rendering"""
        js_indicators = [
            'ng-app',  # Angular
            'react-root',  # React
            'vue-app',  # Vue
            '__NEXT_DATA__',  # Next.js
            'Please enable JavaScript',
            'This site requires JavaScript'
        ]
        return any(indicator in html for indicator in js_indicators)
    
    def parse_html(self, html: str) -> Optional[BeautifulSoup]:
        """
        Parse HTML content with BeautifulSoup
        
        Args:
            html: HTML content string
            
        Returns:
            BeautifulSoup object or None if parsing fails
        """
        if not html:
            return None
        try:
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"[{self.name}] Failed to parse HTML: {e}")
            return None
    
    def standardize_contract(self, state: str, title: str, solicitation_number: str = '',
                            due_date: str = '', link: str = '', agency: str = '',
                            **kwargs) -> Dict[str, Any]:
        """
        Standardize contract data format for all scrapers
        
        Required format:
        {
            "state": "XX",
            "title": "...",
            "solicitation_number": "...",
            "due_date": "...",
            "link": "...",
            "agency": "..."
        }
        
        Args:
            state: Two-letter state code
            title: Contract title
            solicitation_number: Unique identifier
            due_date: Deadline (any format, will be normalized)
            link: Full URL to opportunity
            agency: Agency name
            **kwargs: Additional fields (description, value, etc.)
            
        Returns:
            Standardized contract dictionary
        """
        contract = {
            "state": state.upper() if state else '',
            "title": title.strip() if title else '',
            "solicitation_number": solicitation_number.strip() if solicitation_number else '',
            "due_date": self.parse_date(due_date) if due_date else '',
            "link": urljoin(self.base_url, link) if link else '',
            "agency": agency.strip() if agency else ''
        }
        
        # Add optional fields
        if kwargs:
            contract.update(kwargs)
        
        return contract
    
    def extract_text(self, element, selector: str, default: str = '') -> str:
        """
        Extract text from element using CSS selector
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
            default: Default value if not found
            
        Returns:
            Extracted text or default
        """
        try:
            found = element.select_one(selector)
            if found:
                return found.get_text(strip=True)
            return default
        except Exception as e:
            logger.warning(f"[{self.name}] Error extracting text with selector '{selector}': {e}")
            return default
    
    def extract_attribute(self, element, selector: str, attr: str, default: str = '') -> str:
        """
        Extract attribute value from element
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
            attr: Attribute name
            default: Default value if not found
            
        Returns:
            Attribute value or default
        """
        try:
            found = element.select_one(selector)
            if found:
                return found.get(attr, default)
            return default
        except Exception as e:
            logger.warning(f"[{self.name}] Error extracting attribute '{attr}': {e}")
            return default
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse various date formats to YYYY-MM-DD
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Date in YYYY-MM-DD format or None
        """
        if not date_str:
            return None
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Common date formats
        formats = [
            '%m/%d/%Y',      # 12/31/2025
            '%m-%d-%Y',      # 12-31-2025
            '%Y-%m-%d',      # 2025-12-31
            '%B %d, %Y',     # December 31, 2025
            '%b %d, %Y',     # Dec 31, 2025
            '%d %B %Y',      # 31 December 2025
            '%d %b %Y',      # 31 Dec 2025
            '%m/%d/%y',      # 12/31/25
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"[{self.name}] Could not parse date: {date_str}")
        return None
    
    def extract_email(self, text: str) -> Optional[str]:
        """
        Extract email address from text
        
        Args:
            text: Text containing potential email
            
        Returns:
            Email address or None
        """
        if not text:
            return None
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        
        if match:
            return match.group(0)
        return None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """
        Extract phone number from text
        
        Args:
            text: Text containing potential phone
            
        Returns:
            Phone number or None
        """
        if not text:
            return None
        
        # Various phone formats
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',           # 123-456-7890
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Normalize format
                phone = re.sub(r'[^\d]', '', match.group(0))
                if len(phone) == 10:
                    return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
                return match.group(0)
        
        return None
    
    def is_cleaning_related(self, text: str) -> bool:
        """
        Check if text is related to cleaning/janitorial services
        
        Args:
            text: Text to analyze
            
        Returns:
            True if cleaning-related
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        keywords = [
            'janitorial', 'custodial', 'cleaning', 'housekeeping',
            'sanitation', 'maintenance', 'porter', 'floor care',
            'carpet cleaning', 'window cleaning', 'disinfection',
            'facility maintenance', 'building maintenance'
        ]
        
        return any(keyword in text_lower for keyword in keywords)
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method - must be implemented by subclasses
        
        Returns:
            List of contract dictionaries
        """
        raise NotImplementedError("Subclasses must implement scrape() method")
    
    def format_contract(self, raw_data: Dict) -> Dict:
        """
        Format raw scraped data into standard contract format
        
        Args:
            raw_data: Raw scraped data
            
        Returns:
            Formatted contract dictionary
        """
        return {
            'title': raw_data.get('title', ''),
            'agency': raw_data.get('agency', ''),
            'location': raw_data.get('location', ''),
            'value': self._parse_value(raw_data.get('value', 0)),
            'deadline': raw_data.get('deadline'),
            'description': raw_data.get('description', ''),
            'naics_code': raw_data.get('naics_code', ''),
            'website_url': raw_data.get('url', ''),
            'contact_name': raw_data.get('contact_name', ''),
            'contact_email': raw_data.get('contact_email', ''),
            'contact_phone': raw_data.get('contact_phone', ''),
            'data_source': self.name,
            'scraped_at': datetime.now().isoformat()
        }
    
    def _parse_value(self, value_str) -> Optional[float]:
        """Parse contract value from string"""
        if isinstance(value_str, (int, float)):
            return float(value_str)
        
        if not value_str or not isinstance(value_str, str):
            return None
        
        # Remove currency symbols and commas
        value_str = re.sub(r'[$,]', '', value_str)
        
        try:
            return float(value_str)
        except ValueError:
            return None
    
    def save_contracts(self, contracts: List[Dict], db_connection) -> int:
        """
        Save contracts to database
        
        Args:
            contracts: List of contract dictionaries
            db_connection: Database connection object
            
        Returns:
            Number of contracts saved
        """
        saved_count = 0
        
        for contract in contracts:
            try:
                # Check for duplicates based on title and agency
                cursor = db_connection.cursor()
                cursor.execute("""
                    SELECT id FROM contracts 
                    WHERE title = ? AND agency = ?
                """, (contract['title'], contract['agency']))
                
                if cursor.fetchone():
                    logger.info(f"[{self.name}] Skipping duplicate: {contract['title']}")
                    continue
                
                # Insert new contract
                cursor.execute("""
                    INSERT INTO contracts 
                    (title, agency, location, value, deadline, description, 
                     naics_code, website_url, data_source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    contract['title'],
                    contract['agency'],
                    contract['location'],
                    contract['value'],
                    contract['deadline'],
                    contract['description'],
                    contract['naics_code'],
                    contract['website_url'],
                    contract.get('data_source', self.name)
                ))
                
                db_connection.commit()
                saved_count += 1
                logger.info(f"[{self.name}] ✅ Saved: {contract['title']}")
                
            except Exception as e:
                logger.error(f"[{self.name}] ❌ Error saving contract: {e}")
                db_connection.rollback()
        
        return saved_count
