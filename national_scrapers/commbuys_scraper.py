"""
COMMBUYS Scraper (Massachusetts)
Massachusetts state procurement portal
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class COMBUYSScraper(BaseScraper):
    """
    Scraper for Massachusetts COMMBUYS procurement portal.
    """
    
    BASE_URL = 'https://www.commbuys.com'
    SEARCH_URL = 'https://www.commbuys.com/bso/external/publicBids.sdo'
    
    def __init__(self):
        super().__init__(source_name='commbuys')
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape COMMBUYS opportunities.
        
        Returns:
            List of standardized contracts
        """
        logger.info("Scraping COMMBUYS (Massachusetts)")
        
        # Try to fetch the public bids page
        response = self.fetch_page(self.SEARCH_URL)
        if not response:
            logger.error("Failed to fetch COMMBUYS page")
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # COMMBUYS typically uses tables for bid listings
        listings = soup.find_all(['tr'], class_=['bid-row', 'solicitation-row'])
        
        if not listings:
            # Try alternative: find all table rows in main content
            main_table = soup.find('table', {'id': 'bids-table'})
            if main_table:
                listings = main_table.find_all('tr')[1:]  # Skip header row
        
        if not listings:
            logger.warning("No listings found on COMMBUYS page")
            return []
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing)
                if contract and self.is_cleaning_related(contract.get('title', '')):
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing COMMBUYS listing: {e}")
                continue
        
        logger.info(f"COMMBUYS scraper found {len(contracts)} cleaning-related contracts")
        return contracts
    
    def _parse_listing(self, listing) -> Dict[str, Any]:
        """
        Parse individual COMMBUYS listing.
        
        Args:
            listing: BeautifulSoup tr element
            
        Returns:
            Standardized contract dict
        """
        cells = listing.find_all('td')
        
        if len(cells) < 4:
            return None
        
        # Typical COMMBUYS structure: [Bid #, Title, Agency, Due Date]
        # Extract bid number (usually first column)
        bid_num = cells[0].get_text(strip=True)
        
        # Extract title (usually second column with link)
        title_cell = cells[1]
        title_link = title_cell.find('a')
        title = title_link.get_text(strip=True) if title_link else title_cell.get_text(strip=True)
        
        # Extract link
        link = ''
        if title_link:
            link = title_link.get('href', '')
            if link and not link.startswith('http'):
                link = f"{self.BASE_URL}{link}"
        
        # Extract agency (usually third column)
        agency = cells[2].get_text(strip=True) if len(cells) > 2 else 'Massachusetts'
        
        # Extract due date (usually fourth column)
        due_date = cells[3].get_text(strip=True) if len(cells) > 3 else ''
        
        return self.standardize_contract(
            state='MA',
            title=title,
            solicitation_number=bid_num,
            due_date=due_date,
            link=link,
            agency=agency
        )
