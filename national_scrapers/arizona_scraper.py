"""
Arizona State Procurement Scraper
Direct scraper for Arizona state procurement portal (more reliable than Symphony)
"""

import logging
from typing import List, Dict, Any
from national_scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ArizonaScraper(BaseScraper):
    """
    Scraper for Arizona state procurement portal.
    More reliable than Symphony/SciQuest which blocks requests.
    """
    
    BASE_URL = 'https://app.az.gov'
    SEARCH_URL = 'https://app.az.gov/page.aspx/en/rfp/request_browse_public'
    
    def __init__(self):
        super().__init__(source_name='arizona_state')
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape Arizona state procurement opportunities.
        
        Returns:
            List of standardized contracts
        """
        logger.info("Scraping Arizona state procurement portal")
        
        # Add specific headers for Arizona portal
        headers = {
            **self.DEFAULT_HEADERS,
            'Referer': 'https://procurement.az.gov/',
            'Origin': 'https://procurement.az.gov'
        }
        
        response = self.fetch_page(self.SEARCH_URL, headers=headers)
        if not response:
            logger.error("Failed to fetch Arizona procurement page")
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # Find solicitation listings
        # Arizona uses various structures, try multiple selectors
        listings = soup.find_all(['div', 'tr', 'article'], class_=[
            'solicitation', 'bid-item', 'opportunity-row', 
            'procurement-listing', 'rfp-item'
        ])
        
        if not listings:
            # Try table rows
            main_table = soup.find('table', {'id': 'solicitations'})
            if main_table:
                listings = main_table.find_all('tr')[1:]  # Skip header
        
        if not listings:
            # Try all links in main content
            main_content = soup.find('div', {'id': 'main-content'})
            if main_content:
                listings = main_content.find_all('div', class_=['item', 'listing'])
        
        if not listings:
            logger.warning("No listings found on Arizona page")
            return []
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing)
                if contract and self.is_cleaning_related(contract.get('title', '')):
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing Arizona listing: {e}")
                continue
        
        logger.info(f"Arizona scraper found {len(contracts)} cleaning-related contracts")
        return contracts
    
    def _parse_listing(self, listing) -> Dict[str, Any]:
        """
        Parse individual Arizona listing.
        
        Args:
            listing: BeautifulSoup element
            
        Returns:
            Standardized contract dict
        """
        # Extract title
        title_elem = listing.find(['a', 'h2', 'h3', 'span'], class_=['title', 'solicitation-title', 'name'])
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
        
        if cells and len(cells) > 0:
            sol_number = cells[0].get_text(strip=True)
        else:
            sol_elem = listing.find(['span', 'div'], class_=['sol-number', 'rfp-number', 'number'])
            if sol_elem:
                sol_number = sol_elem.get_text(strip=True)
        
        # Extract due date
        due_date = ''
        if cells and len(cells) > 2:
            due_date = cells[-1].get_text(strip=True)
        else:
            due_elem = listing.find(['span', 'time', 'div'], class_=['due-date', 'closing-date', 'deadline'])
            if due_elem:
                due_date = due_elem.get_text(strip=True)
        
        # Extract agency
        agency = 'Arizona State'
        if cells and len(cells) > 1:
            agency = cells[1].get_text(strip=True)
        else:
            agency_elem = listing.find(['span', 'div'], class_=['agency', 'department', 'organization'])
            if agency_elem:
                agency = agency_elem.get_text(strip=True)
        
        return self.standardize_contract(
            state='AZ',
            title=title,
            solicitation_number=sol_number,
            due_date=due_date,
            link=link,
            agency=agency
        )
