"""
eMaryland Marketplace Scraper
Maryland state procurement portal
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class EMarylandScraper(BaseScraper):
    """
    Scraper for Maryland eMaryland Marketplace (eMM) procurement portal.
    """
    
    BASE_URL = 'https://emma.maryland.gov'
    SEARCH_URL = 'https://emma.maryland.gov/page.aspx/en/bpm/process_list'
    
    def __init__(self):
        super().__init__(source_name='emaryland')
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape eMaryland Marketplace opportunities.
        
        Returns:
            List of standardized contracts
        """
        logger.info("Scraping eMaryland Marketplace")
        
        response = self.fetch_page(self.SEARCH_URL)
        if not response:
            logger.error("Failed to fetch eMaryland page")
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # eMaryland uses divs or table rows for opportunities
        listings = soup.find_all(['div', 'tr'], class_=['opportunity-item', 'solicitation-row', 'bid-row'])
        
        if not listings:
            # Try finding all links in main content area
            main_content = soup.find('div', {'id': 'main-content'})
            if main_content:
                listings = main_content.find_all('div', class_=['item', 'row'])
        
        if not listings:
            logger.warning("No listings found on eMaryland page")
            return []
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing)
                if contract and self.is_cleaning_related(contract.get('title', '')):
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing eMaryland listing: {e}")
                continue
        
        logger.info(f"eMaryland scraper found {len(contracts)} cleaning-related contracts")
        return contracts
    
    def _parse_listing(self, listing) -> Dict[str, Any]:
        """
        Parse individual eMaryland listing.
        
        Args:
            listing: BeautifulSoup element
            
        Returns:
            Standardized contract dict
        """
        # Extract title
        title_elem = listing.find(['a', 'h3', 'span'], class_=['title', 'solicitation-title', 'process-name'])
        if not title_elem:
            title_elem = listing.find('a')
        title = title_elem.get_text(strip=True) if title_elem else 'No Title'
        
        # Extract link
        link = ''
        if title_elem and title_elem.name == 'a':
            link = title_elem.get('href', '')
            if link and not link.startswith('http'):
                link = f"{self.BASE_URL}{link}"
        
        # Extract solicitation number
        sol_num_elem = listing.find(['span', 'td'], class_=['sol-number', 'bid-number', 'process-id'])
        solicitation_number = sol_num_elem.get_text(strip=True) if sol_num_elem else 'N/A'
        
        # Extract due date
        due_date_elem = listing.find(['span', 'td', 'time'], class_=['due-date', 'closing-date', 'end-date'])
        due_date = due_date_elem.get_text(strip=True) if due_date_elem else ''
        
        # Extract agency
        agency_elem = listing.find(['span', 'td'], class_=['agency', 'organization', 'buyer'])
        agency = agency_elem.get_text(strip=True) if agency_elem else 'Maryland'
        
        return self.standardize_contract(
            state='MD',
            title=title,
            solicitation_number=solicitation_number,
            due_date=due_date,
            link=link,
            agency=agency
        )
