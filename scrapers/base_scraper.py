"""
Base Scraper Class
Foundation for all procurement portal scrapers
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Custom exception for scraper errors"""
    pass


class BaseScraper:
    """Base class for all government procurement scrapers"""
    
    def __init__(self, name: str, base_url: str, rate_limit: float = 2.0):
        """
        Initialize base scraper
        
        Args:
            name: Scraper name for logging
            base_url: Base URL of the portal
            rate_limit: Seconds to wait between requests (default 2.0)
        """
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ContractLink AI Bot/1.0 (Government Contract Aggregator; +https://contractlink.ai)'
        })
        self.last_request_time = 0
    
    def _rate_limit_delay(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def fetch_page(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Fetch a web page with retry logic
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object or None if failed
        """
        for attempt in range(max_retries):
            try:
                self._rate_limit_delay()
                
                logger.info(f"[{self.name}] Fetching: {url} (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                logger.info(f"[{self.name}] ✅ Success: {url} ({len(response.content)} bytes)")
                return response
                
            except requests.RequestException as e:
                logger.warning(f"[{self.name}] ⚠️  Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    logger.info(f"[{self.name}] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"[{self.name}] ❌ Failed after {max_retries} attempts")
                    return None
        
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup
        
        Args:
            html: HTML content string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'html.parser')
    
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
