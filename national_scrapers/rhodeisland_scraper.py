"""
Rhode Island Scraper
Rhode Island state procurement portal (chosen over Alaska for easier maintenance)
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class RhodeIslandScraper(BaseScraper):
    """
    Scraper for Rhode Island Department of Procurement (RIDOP).
    Chosen over Alaska as it has more consistent HTML structure.
    """
    
    BASE_URL = 'https://www.ridop.ri.gov'
    SEARCH_URL = 'https://www.ridop.ri.gov/public-solicitations.php'
    
    def __init__(self):
        super().__init__(source_name='rhodeisland')
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape Rhode Island opportunities.
        
        Returns:
            List of standardized contracts
        """
        logger.info("Scraping Rhode Island procurement")
        
        response = self.fetch_page(self.SEARCH_URL)
        if not response:
            logger.error("Failed to fetch Rhode Island page")
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # Find opportunity listings
        listings = soup.find_all(['div', 'tr'], class_=['solicitation-row', 'bid-row', 'opportunity-item'])
        
        if not listings:
            # Try table in main content
            main_table = soup.find('table', class_=['solicitations', 'bids-table'])
            if main_table:
                listings = main_table.find_all('tr')[1:]  # Skip header
        
        if not listings:
            logger.warning("No listings found on Rhode Island page")
            return []
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing)
                if contract and self.is_cleaning_related(contract.get('title', '')):
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing Rhode Island listing: {e}")
                continue
        
        logger.info(f"Rhode Island scraper found {len(contracts)} cleaning-related contracts")
        return contracts
    
    def _parse_listing(self, listing) -> Dict[str, Any]:
        """
        Parse individual Rhode Island listing.
        
        Args:
            listing: BeautifulSoup element
            
        Returns:
            Standardized contract dict
        """
        # Extract title
        title_elem = listing.find(['a', 'h3', 'span'], class_=['title', 'solicitation-title'])
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
        cells = listing.find_all('td')
        sol_number = 'N/A'
        if cells:
            sol_number = cells[0].get_text(strip=True)
        else:
            sol_elem = listing.find(['span'], class_=['sol-number', 'rfp-number'])
            if sol_elem:
                sol_number = sol_elem.get_text(strip=True)
        
        # Extract due date
        due_date = ''
        if cells and len(cells) > 3:
            due_date = cells[3].get_text(strip=True)
        else:
            due_elem = listing.find(['span', 'time'], class_=['due-date', 'closing-date'])
            if due_elem:
                due_date = due_elem.get_text(strip=True)
        
        # Extract agency
        agency = 'Rhode Island'
        if cells and len(cells) > 1:
            agency = cells[1].get_text(strip=True)
        else:
            agency_elem = listing.find(['span'], class_=['agency', 'department'])
            if agency_elem:
                agency = agency_elem.get_text(strip=True)
        
        return self.standardize_contract(
            state='RI',
            title=title,
            solicitation_number=sol_number,
            due_date=due_date,
            link=link,
            agency=agency
        )
