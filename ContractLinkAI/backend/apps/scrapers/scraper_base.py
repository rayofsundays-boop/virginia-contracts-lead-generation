"""
Base scraper utilities for ContractLink AI.
Provides common functionality for state and city portal scrapers.
"""
import httpx
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.conf import settings

logger = logging.getLogger('scrapers')


class BaseScraper:
    """
    Base class for all scrapers with common functionality.
    """
    
    def __init__(self, timeout: int = None, max_retries: int = None):
        self.timeout = timeout or settings.SCRAPER_TIMEOUT
        self.max_retries = max_retries or settings.SCRAPER_MAX_RETRIES
        self.user_agent = settings.SCRAPER_USER_AGENT
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a web page with retry logic.
        
        Args:
            url: The URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=self.headers)
                    response.raise_for_status()
                    logger.info(f"Successfully fetched {url}")
                    return response.text
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
            except httpx.RequestError as e:
                logger.warning(f"Request error fetching {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {str(e)}")
                return None
        
        return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.
        
        Args:
            html: HTML content string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'html.parser')
    
    def extract_text(self, element, selector: str) -> str:
        """
        Extract text from an element using CSS selector.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector string
            
        Returns:
            Extracted text or empty string
        """
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else ""
        except Exception as e:
            logger.warning(f"Error extracting text with selector {selector}: {str(e)}")
            return ""
    
    def extract_attribute(self, element, selector: str, attribute: str) -> str:
        """
        Extract an attribute from an element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector string
            attribute: Attribute name
            
        Returns:
            Attribute value or empty string
        """
        try:
            found = element.select_one(selector)
            return found.get(attribute, "") if found else ""
        except Exception as e:
            logger.warning(f"Error extracting attribute {attribute}: {str(e)}")
            return ""
    
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse a date string into datetime object.
        Handles multiple common date formats.
        
        Args:
            date_string: Date string to parse
            
        Returns:
            datetime object or None
        """
        if not date_string:
            return None
        
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %I:%M %p',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return None
    
    def clean_rfp_number(self, rfp_number: str) -> str:
        """
        Clean and normalize RFP number.
        
        Args:
            rfp_number: Raw RFP number string
            
        Returns:
            Cleaned RFP number
        """
        if not rfp_number:
            return ""
        
        # Remove common prefixes and clean
        rfp_number = rfp_number.strip()
        rfp_number = rfp_number.replace('#', '').replace('No.', '').replace('Number:', '').strip()
        
        return rfp_number
    
    def build_absolute_url(self, base_url: str, relative_url: str) -> str:
        """
        Build absolute URL from base and relative URLs.
        
        Args:
            base_url: Base URL
            relative_url: Relative URL
            
        Returns:
            Absolute URL
        """
        from urllib.parse import urljoin
        return urljoin(base_url, relative_url)


class StateScraperTemplate(BaseScraper):
    """
    Template for state-specific scrapers.
    Each state can inherit from this and implement parse_rfp_listing.
    """
    
    def __init__(self, state_code: str, portal_url: str, **kwargs):
        super().__init__(**kwargs)
        self.state_code = state_code
        self.portal_url = portal_url
    
    async def scrape(self) -> List[Dict]:
        """
        Main scraping method. Override in subclasses if needed.
        
        Returns:
            List of RFP dictionaries
        """
        html = await self.fetch_page(self.portal_url)
        if not html:
            logger.error(f"Failed to fetch portal for {self.state_code}")
            return []
        
        soup = self.parse_html(html)
        return self.parse_rfp_listing(soup)
    
    def parse_rfp_listing(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse RFP listings from HTML.
        MUST be implemented by subclasses.
        
        Args:
            soup: BeautifulSoup object of the portal page
            
        Returns:
            List of RFP dictionaries with keys:
            - rfp_number
            - title
            - description
            - source_url
            - posted_date
            - due_date
            - etc.
        """
        raise NotImplementedError("Subclasses must implement parse_rfp_listing")


class VirginiaScraper(StateScraperTemplate):
    """
    Virginia eVA portal scraper example.
    """
    
    def __init__(self):
        super().__init__(
            state_code='VA',
            portal_url='https://eva.virginia.gov/pages/solicitations-search'
        )
    
    def parse_rfp_listing(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse Virginia eVA portal listings.
        """
        rfps = []
        
        # Example: Find all RFP rows (adjust selectors based on actual HTML)
        rfp_rows = soup.select('table.solicitations tbody tr')
        
        for row in rfp_rows:
            try:
                rfp = {
                    'rfp_number': self.extract_text(row, 'td:nth-child(1)'),
                    'title': self.extract_text(row, 'td:nth-child(2)'),
                    'description': self.extract_text(row, 'td:nth-child(3)'),
                    'source_url': self.build_absolute_url(
                        self.portal_url,
                        self.extract_attribute(row, 'td:nth-child(2) a', 'href')
                    ),
                    'source_state': self.state_code,
                    'source_type': 'state_portal',
                    'issuing_agency': self.extract_text(row, 'td:nth-child(4)'),
                    'posted_date': self.parse_date(self.extract_text(row, 'td:nth-child(5)')),
                    'due_date': self.parse_date(self.extract_text(row, 'td:nth-child(6)')),
                    'status': 'active',
                }
                
                if rfp['rfp_number'] and rfp['title']:
                    rfps.append(rfp)
            except Exception as e:
                logger.warning(f"Error parsing row in {self.state_code}: {str(e)}")
                continue
        
        logger.info(f"Found {len(rfps)} RFPs for {self.state_code}")
        return rfps


# Map of state codes to scraper classes
STATE_SCRAPERS = {
    'VA': VirginiaScraper,
    # Add more state scrapers here
    # 'CA': CaliforniaScraper,
    # 'NY': NewYorkScraper,
    # etc.
}


def get_scraper_for_state(state_code: str) -> Optional[StateScraperTemplate]:
    """
    Get the appropriate scraper class for a state.
    
    Args:
        state_code: Two-letter state code
        
    Returns:
        Scraper instance or None
    """
    scraper_class = STATE_SCRAPERS.get(state_code)
    if scraper_class:
        return scraper_class()
    
    logger.warning(f"No scraper available for state: {state_code}")
    return None
