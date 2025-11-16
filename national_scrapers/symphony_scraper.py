"""
Symphony/Periscope Procurement Scraper
Covers 30-40 states using SciQuest platform
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SymphonyScraper(BaseScraper):
    """
    Scraper for Symphony/Periscope procurement platform.
    Covers AZ, CA, CO, CT, GA, HI, ID, IL, KS, KY, ME, MI, MN, MO, MS, MT,
    NV, NM, ND, OH, OK, OR, SC, TN, TX, UT, WA, WI, and others.
    """
    
    # States using Symphony/Periscope platform
    SYMPHONY_STATES = {
        'AZ': {'name': 'Arizona', 'org': 'Arizona'},
        'CA': {'name': 'California', 'org': 'California'},
        'CO': {'name': 'Colorado', 'org': 'Colorado'},
        'CT': {'name': 'Connecticut', 'org': 'Connecticut'},
        'GA': {'name': 'Georgia', 'org': 'Georgia'},
        'HI': {'name': 'Hawaii', 'org': 'Hawaii'},
        'ID': {'name': 'Idaho', 'org': 'Idaho'},
        'IL': {'name': 'Illinois', 'org': 'Illinois'},
        'KS': {'name': 'Kansas', 'org': 'Kansas'},
        'KY': {'name': 'Kentucky', 'org': 'Kentucky'},
        'ME': {'name': 'Maine', 'org': 'Maine'},
        'MI': {'name': 'Michigan', 'org': 'SIGMA'},  # Michigan uses SIGMA
        'MN': {'name': 'Minnesota', 'org': 'Minnesota'},
        'MO': {'name': 'Missouri', 'org': 'Missouri'},
        'MS': {'name': 'Mississippi', 'org': 'Mississippi'},
        'MT': {'name': 'Montana', 'org': 'Montana'},
        'NV': {'name': 'Nevada', 'org': 'Nevada'},
        'NM': {'name': 'New Mexico', 'org': 'NewMexico'},
        'ND': {'name': 'North Dakota', 'org': 'NorthDakota'},
        'OH': {'name': 'Ohio', 'org': 'Ohio'},
        'OK': {'name': 'Oklahoma', 'org': 'Oklahoma'},
        'OR': {'name': 'Oregon', 'org': 'Oregon'},
        'SC': {'name': 'South Carolina', 'org': 'SouthCarolina'},
        'TN': {'name': 'Tennessee', 'org': 'Tennessee'},
        'TX': {'name': 'Texas', 'org': 'ESBD'},  # Texas uses ESBD
        'UT': {'name': 'Utah', 'org': 'Utah'},
        'WA': {'name': 'Washington', 'org': 'Washington'},
        'WI': {'name': 'Wisconsin', 'org': 'Wisconsin'},
    }
    
    BASE_URL = 'https://solutions.sciquest.com'
    SEARCH_PATH = '/apps/Router/PublicEvent'
    
    def __init__(self):
        super().__init__(source_name='symphony')
    
    def scrape(self, states: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape all Symphony/Periscope states.
        
        Args:
            states: List of state codes to scrape (default: all)
            
        Returns:
            List of standardized contracts
        """
        if states is None:
            states = list(self.SYMPHONY_STATES.keys())
        
        all_contracts = []
        
        for state_code in states:
            if state_code not in self.SYMPHONY_STATES:
                logger.warning(f"State {state_code} not in Symphony platform")
                continue
            
            logger.info(f"Scraping Symphony for {state_code}")
            contracts = self._scrape_state(state_code)
            all_contracts.extend(contracts)
        
        logger.info(f"Symphony scraper found {len(all_contracts)} total opportunities")
        return all_contracts
    
    def _scrape_state(self, state_code: str) -> List[Dict[str, Any]]:
        """
        Scrape a single Symphony state.
        
        Args:
            state_code: 2-letter state code
            
        Returns:
            List of contracts for this state
        """
        state_info = self.SYMPHONY_STATES[state_code]
        org_name = state_info['org']
        
        # Symphony public event search URL
        url = f"{self.BASE_URL}/apps/Router/PublicEvent?OrgName={org_name}"
        
        response = self.fetch_page(url)
        if not response:
            logger.error(f"Failed to fetch Symphony page for {state_code}")
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # Try to find opportunities table or list
        # Symphony typically uses divs with class "event-item" or "solicitation-row"
        listings = soup.find_all(['div', 'tr'], class_=['event-item', 'solicitation-row', 'opportunity-item'])
        
        if not listings:
            # Try alternative selectors
            listings = soup.find_all('div', attrs={'data-event-id': True})
        
        if not listings:
            logger.warning(f"No listings found for {state_code} in Symphony")
            return []
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing, state_code)
                if contract and self.is_cleaning_related(contract.get('title', '')):
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing Symphony listing for {state_code}: {e}")
                continue
        
        logger.info(f"Found {len(contracts)} cleaning-related contracts for {state_code}")
        return contracts
    
    def _parse_listing(self, listing, state_code: str) -> Dict[str, Any]:
        """
        Parse individual listing from Symphony HTML.
        
        Args:
            listing: BeautifulSoup element
            state_code: State code
            
        Returns:
            Standardized contract dict
        """
        # Extract title
        title_elem = listing.find(['a', 'h3', 'h4'], class_=['title', 'event-title', 'solicitation-title'])
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
        sol_num_elem = listing.find(['span', 'td'], class_=['sol-number', 'event-id', 'solicitation-number'])
        solicitation_number = sol_num_elem.get_text(strip=True) if sol_num_elem else 'N/A'
        
        # Extract due date
        due_date_elem = listing.find(['span', 'td', 'time'], class_=['due-date', 'closing-date', 'end-date'])
        due_date = due_date_elem.get_text(strip=True) if due_date_elem else ''
        
        # Extract agency
        agency_elem = listing.find(['span', 'td'], class_=['agency', 'organization', 'buyer'])
        agency = agency_elem.get_text(strip=True) if agency_elem else self.SYMPHONY_STATES[state_code]['name']
        
        return self.standardize_contract(
            state=state_code,
            title=title,
            solicitation_number=solicitation_number,
            due_date=due_date,
            link=link,
            agency=agency
        )
