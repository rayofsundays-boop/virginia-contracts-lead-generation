"""
New Hampshire Scraper
New Hampshire state procurement portal
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NewHampshireScraper(BaseScraper):
    """
    Scraper for New Hampshire state procurement portal.
    """
    
    BASE_URL = 'https://apps.das.nh.gov'
    SEARCH_URL = 'https://apps.das.nh.gov/bidscontracts/'
    
    def __init__(self):
        super().__init__(source_name='newhampshire')
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape New Hampshire opportunities.
        
        Returns:
            List of standardized contracts
        """
        logger.info("Scraping New Hampshire procurement")
        
        response = self.fetch_page(self.SEARCH_URL)
        if not response:
            logger.error("Failed to fetch New Hampshire page")
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # Find opportunity listings
        listings = soup.find_all(['div', 'tr'], class_=['bid-listing', 'opportunity-row', 'solicitation-item'])
        
        if not listings:
            # Try table rows in main content
            main_table = soup.find('table', {'id': 'bids-table'})
            if main_table:
                listings = main_table.find_all('tr')[1:]  # Skip header
        
        if not listings:
            logger.warning("No listings found on New Hampshire page")
            return []
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing)
                if contract and self.is_cleaning_related(contract.get('title', '')):
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing New Hampshire listing: {e}")
                continue
        
        logger.info(f"New Hampshire scraper found {len(contracts)} cleaning-related contracts")
        return contracts
    
    def _parse_listing(self, listing) -> Dict[str, Any]:
        """
        Parse individual New Hampshire listing.
        
        Args:
            listing: BeautifulSoup element
            
        Returns:
            Standardized contract dict
        """
        # Extract title
        title_elem = listing.find(['a', 'h3', 'span'], class_=['title', 'bid-title'])
        if not title_elem:
            title_elem = listing.find('a')
        title = title_elem.get_text(strip=True) if title_elem else 'No Title'
        
        # Extract link
        link = ''
        if title_elem and title_elem.name == 'a':
            link = title_elem.get('href', '')
            if link and not link.startswith('http'):
                link = f"{self.BASE_URL}{link}"
        
        # Extract bid number
        cells = listing.find_all('td')
        bid_number = 'N/A'
        if cells:
            bid_number = cells[0].get_text(strip=True)
        else:
            bid_elem = listing.find(['span'], class_=['bid-number', 'sol-number'])
            if bid_elem:
                bid_number = bid_elem.get_text(strip=True)
        
        # Extract due date
        due_date = ''
        if cells and len(cells) > 2:
            due_date = cells[-1].get_text(strip=True)
        else:
            due_elem = listing.find(['span', 'time'], class_=['due-date', 'closing-date'])
            if due_elem:
                due_date = due_elem.get_text(strip=True)
        
        # Extract agency
        agency = 'New Hampshire'
        if cells and len(cells) > 1:
            agency = cells[1].get_text(strip=True)
        else:
            agency_elem = listing.find(['span'], class_=['agency', 'department'])
            if agency_elem:
                agency = agency_elem.get_text(strip=True)
        
        return self.standardize_contract(
            state='NH',
            title=title,
            solicitation_number=bid_number,
            due_date=due_date,
            link=link,
            agency=agency
        )
