"""
DemandStar Scraper
Covers thousands of cities, counties, school districts, utilities, airports
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DemandStarScraper(BaseScraper):
    """
    Scraper for DemandStar platform.
    Covers thousands of local governments nationwide.
    """
    
    API_URL = 'https://api.demandstar.com/api/public/v1/open-opportunities'
    PUBLIC_URL = 'https://www.demandstar.com/procurement-opportunities/'
    
    def __init__(self):
        super().__init__(source_name='demandstar')
    
    def scrape(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Scrape DemandStar opportunities via API.
        
        Args:
            limit: Maximum opportunities to fetch
            
        Returns:
            List of standardized contracts
        """
        logger.info(f"Scraping DemandStar (limit: {limit})")
        
        # Try API first
        contracts = self._scrape_api(limit)
        
        # If API fails, try public page
        if not contracts:
            logger.warning("API failed, trying public page")
            contracts = self._scrape_public_page()
        
        logger.info(f"DemandStar scraper found {len(contracts)} opportunities")
        return contracts
    
    def _scrape_api(self, limit: int) -> List[Dict[str, Any]]:
        """
        Scrape via DemandStar API.
        
        Args:
            limit: Max opportunities
            
        Returns:
            List of contracts
        """
        params = {
            'limit': limit,
            'offset': 0,
            'keywords': 'janitorial,custodial,cleaning,facilities'
        }
        
        response = self.fetch_page(self.API_URL, timeout=60)
        if not response:
            return []
        
        data = self.parse_json(response)
        if not data:
            return []
        
        contracts = []
        opportunities = data.get('opportunities', [])
        
        for opp in opportunities:
            try:
                # Filter for cleaning-related
                title = opp.get('title', '')
                description = opp.get('description', '')
                combined_text = f"{title} {description}"
                
                if not self.is_cleaning_related(combined_text):
                    continue
                
                # Extract state from location
                location = opp.get('location', {})
                state = location.get('state', 'US')
                city = location.get('city', '')
                
                # Extract agency/organization
                org = opp.get('organization', {})
                agency = org.get('name', 'N/A')
                
                contract = self.standardize_contract(
                    state=self.normalize_state(state),
                    title=title,
                    solicitation_number=opp.get('id', 'N/A'),
                    due_date=opp.get('dueDate', ''),
                    link=opp.get('url', self.PUBLIC_URL),
                    agency=f"{agency} - {city}" if city else agency,
                    organization_type=org.get('type', ''),
                    description=description[:200]  # First 200 chars
                )
                
                contracts.append(contract)
                
            except Exception as e:
                logger.error(f"Error parsing DemandStar opportunity: {e}")
                continue
        
        return contracts
    
    def _scrape_public_page(self) -> List[Dict[str, Any]]:
        """
        Scrape public opportunities page as fallback.
        
        Returns:
            List of contracts
        """
        response = self.fetch_page(self.PUBLIC_URL)
        if not response:
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # Find opportunity cards
        listings = soup.find_all(['div', 'article'], class_=['opportunity-card', 'opp-item', 'bid-listing'])
        
        for listing in listings:
            try:
                # Extract title
                title_elem = listing.find(['h2', 'h3', 'a'], class_=['title', 'opp-title'])
                if not title_elem:
                    title_elem = listing.find('a')
                title = title_elem.get_text(strip=True) if title_elem else 'No Title'
                
                # Filter for cleaning
                if not self.is_cleaning_related(title):
                    continue
                
                # Extract link
                link = ''
                if title_elem and title_elem.name == 'a':
                    link = title_elem.get('href', '')
                    if link and not link.startswith('http'):
                        link = f"https://www.demandstar.com{link}"
                
                # Extract location/state
                location_elem = listing.find(['span', 'div'], class_=['location', 'state', 'city'])
                location = location_elem.get_text(strip=True) if location_elem else ''
                state = 'US'
                if location:
                    # Try to extract state from location string
                    parts = location.split(',')
                    if len(parts) > 1:
                        state = self.normalize_state(parts[-1].strip())
                
                # Extract agency
                agency_elem = listing.find(['span', 'div'], class_=['agency', 'organization', 'org-name'])
                agency = agency_elem.get_text(strip=True) if agency_elem else 'N/A'
                
                # Extract due date
                due_elem = listing.find(['span', 'time'], class_=['due-date', 'closing-date'])
                due_date = due_elem.get_text(strip=True) if due_elem else ''
                
                # Extract ID
                id_elem = listing.find(['span'], class_=['opp-id', 'bid-id'])
                opp_id = id_elem.get_text(strip=True) if id_elem else 'N/A'
                
                contract = self.standardize_contract(
                    state=state,
                    title=title,
                    solicitation_number=opp_id,
                    due_date=due_date,
                    link=link,
                    agency=agency
                )
                
                contracts.append(contract)
                
            except Exception as e:
                logger.error(f"Error parsing DemandStar listing: {e}")
                continue
        
        return contracts
