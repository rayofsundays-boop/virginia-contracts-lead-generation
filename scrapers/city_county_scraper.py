"""
City/County Bid Board Scraper
Scrapes local government procurement sites in Virginia
"""

from .base_scraper import BaseScraper, logger
from typing import List, Dict
import re


class CityCountyScraper(BaseScraper):
    """
    Scraper for city and county bid boards in Virginia
    Focus: Hampton, Suffolk, Virginia Beach, Newport News, Williamsburg
    """
    
    # City procurement portal configurations
    CITY_PORTALS = {
        'hampton': {
            'name': 'Hampton, VA',
            'url': 'https://www.hampton.gov/bids',
            'alt_urls': [
                'https://www.hampton.gov/procurement',
                'https://hamptonnewports/bids'
            ]
        },
        'suffolk': {
            'name': 'Suffolk, VA',
            'url': 'https://www.suffolkva.us/bids',
            'alt_urls': [
                'https://www.suffolkva.us/government/departments-offices/procurement',
            ]
        },
        'virginia_beach': {
            'name': 'Virginia Beach, VA',
            'url': 'https://www.vbgov.com/government/departments/purchasing/Pages/solicitations.aspx',
            'alt_urls': [
                'https://www.vbgov.com/government/departments/purchasing',
            ]
        },
        'newport_news': {
            'name': 'Newport News, VA',
            'url': 'https://www.nnva.gov/bids',
            'alt_urls': [
                'https://www.nnva.gov/2182/Current-Solicitations',
            ]
        },
        'williamsburg': {
            'name': 'Williamsburg, VA',
            'url': 'https://www.williamsburgva.gov/bids',
            'alt_urls': [
                'https://www.williamsburgva.gov/government/city-departments/purchasing',
            ]
        },
        'norfolk': {
            'name': 'Norfolk, VA',
            'url': 'https://www.norfolk.gov/bids',
            'alt_urls': [
                'https://www.norfolk.gov/index.aspx?NID=2076',
            ]
        },
        'chesapeake': {
            'name': 'Chesapeake, VA',
            'url': 'https://www.cityofchesapeake.net/bids',
            'alt_urls': [
                'https://www.cityofchesapeake.net/government/city-departments/departments/procurement-services',
            ]
        },
        'richmond': {
            'name': 'Richmond, VA',
            'url': 'https://www.rva.gov/procurement/bids',
            'alt_urls': [
                'https://www.rva.gov/procurement',
            ]
        },
        'arlington': {
            'name': 'Arlington County, VA',
            'url': 'https://www.arlingtonva.us/bids',
            'alt_urls': [
                'https://procurement.arlingtonva.us',
            ]
        },
        'alexandria': {
            'name': 'Alexandria, VA',
            'url': 'https://www.alexandriava.gov/Procurement',
            'alt_urls': [
                'https://www.alexandriava.gov/purchasing/bidopportunities',
            ]
        },
        'fairfax': {
            'name': 'Fairfax County, VA',
            'url': 'https://www.fairfaxcounty.gov/procure',
            'alt_urls': [
                'https://www.fairfaxcounty.gov/procurement-contracts',
            ]
        }
    }
    
    def __init__(self, cities: List[str] = None):
        """
        Initialize city/county scraper
        
        Args:
            cities: List of city keys to scrape (default: all cities)
        """
        super().__init__(
            name='City/County Bids',
            base_url='',  # Multiple URLs
            rate_limit=4.0  # Respectful rate limiting for local government
        )
        
        self.cities = cities if cities else list(self.CITY_PORTALS.keys())
    
    def scrape(self) -> List[Dict]:
        """
        Scrape all configured city/county portals
        
        Returns:
            List of contract dictionaries
        """
        logger.info(f"[{self.name}] Starting scrape for {len(self.cities)} cities...")
        all_contracts = []
        
        for city_key in self.cities:
            try:
                city_config = self.CITY_PORTALS.get(city_key)
                
                if not city_config:
                    logger.warning(f"[{self.name}] Unknown city: {city_key}")
                    continue
                
                logger.info(f"[{self.name}] Scraping {city_config['name']}...")
                
                contracts = self._scrape_city(city_key, city_config)
                all_contracts.extend(contracts)
                
                logger.info(f"[{self.name}] {city_config['name']}: Found {len(contracts)} contracts")
            
            except Exception as e:
                logger.error(f"[{self.name}] Error scraping {city_key}: {e}")
                continue
        
        logger.info(f"[{self.name}] ✅ Total contracts found: {len(all_contracts)}")
        return all_contracts
    
    def _scrape_city(self, city_key: str, config: Dict) -> List[Dict]:
        """
        Scrape a single city/county portal
        
        Args:
            city_key: City identifier key
            config: City configuration dictionary
            
        Returns:
            List of contracts for that city
        """
        contracts = []
        
        # Try main URL first
        urls_to_try = [config['url']] + config.get('alt_urls', [])
        
        for url in urls_to_try:
            try:
                logger.info(f"[{self.name}] Trying {url}...")
                
                response = self.fetch_page(url)
                
                if not response:
                    continue
                
                soup = self.parse_html(response.text)
                
                # Find bid/solicitation listings
                listings = self._find_listings(soup)
                
                if not listings:
                    logger.info(f"[{self.name}] No listings found at {url}")
                    continue
                
                logger.info(f"[{self.name}] Found {len(listings)} listings at {url}")
                
                for listing in listings:
                    try:
                        contract = self._parse_city_listing(listing, config['name'])
                        
                        if contract and self._is_valid_city_contract(contract):
                            contracts.append(contract)
                    
                    except Exception as e:
                        logger.debug(f"[{self.name}] Error parsing listing: {e}")
                        continue
                
                # If we found contracts, no need to try alternate URLs
                if contracts:
                    break
            
            except Exception as e:
                logger.warning(f"[{self.name}] Error with {url}: {e}")
                continue
        
        return contracts
    
    def _find_listings(self, soup) -> List:
        """
        Find bid/solicitation listings on page
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of listing elements
        """
        # Try various common selectors used by city websites
        selectors = [
            'tr.bid-row',
            'div.solicitation',
            'div.bid-listing',
            'tr[class*="bid"]',
            'div[class*="procurement"]',
            'li.opportunity',
            'div.rfp-listing',
            'table.bids tr',
            'div.contract-opportunity'
        ]
        
        for selector in selectors:
            listings = soup.select(selector)
            if listings and len(listings) > 1:  # More than just header row
                return listings
        
        # Fallback: Look for tables with bid-like content
        tables = soup.find_all('table')
        for table in tables:
            text = table.get_text().lower()
            if any(word in text for word in ['solicitation', 'bid', 'rfp', 'rfq']):
                rows = table.find_all('tr')[1:]  # Skip header
                if rows:
                    return rows
        
        # Last resort: Find all links with bid/solicitation in text or href
        links = soup.find_all('a', text=re.compile(r'(bid|solicitation|rfp|rfq|procurement)', re.I))
        if not links:
            links = soup.find_all('a', href=re.compile(r'(bid|solicitation|rfp|rfq)', re.I))
        
        return links
    
    def _parse_city_listing(self, listing, city_name: str) -> Dict:
        """
        Parse a procurement listing from city portal
        
        Args:
            listing: BeautifulSoup element
            city_name: City name
            
        Returns:
            Contract dictionary
        """
        # Extract title
        title_elem = (listing.find('a') or 
                     listing.select_one('.title, .solicitation-title, td:nth-child(2)') or
                     listing)
        
        title = title_elem.get_text(strip=True) if title_elem else ''
        
        # Clean up title
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Extract URL
        url = None
        link = listing.find('a')
        if link and link.get('href'):
            url = link['href']
            # Make absolute URL if relative
            if url and not url.startswith('http'):
                # Try to construct full URL
                if url.startswith('/'):
                    # Extract domain from city name or use generic
                    base = self._get_city_base_url(city_name)
                    url = f"{base}{url}" if base else url
        
        # Extract text for parsing
        text = listing.get_text()
        
        # Try to find deadline
        deadline = None
        deadline_patterns = [
            r'(?:due|deadline|closing|closes)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Any date
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                deadline = self.parse_date(match.group(1))
                if deadline:
                    break
        
        # Extract solicitation number
        sol_match = re.search(r'(?:RFP|IFB|RFQ)[#\s-]*([A-Z0-9-]+)', text, re.I)
        sol_number = sol_match.group(0) if sol_match else None
        
        # Extract department/agency if visible
        dept_match = re.search(r'(?:Department|Dept)[:\s]+([^\n]{3,50})', text, re.I)
        department = dept_match.group(1).strip() if dept_match else None
        
        agency = f"{city_name} - {department}" if department else city_name
        
        contract = {
            'title': title,
            'agency': agency,
            'location': city_name,
            'value': None,
            'deadline': deadline,
            'description': text[:500],  # First 500 chars
            'naics_code': '561720',
            'url': url,
            'solicitation_number': sol_number,
            'city': city_name
        }
        
        return contract
    
    def _get_city_base_url(self, city_name: str) -> str:
        """Get base URL for city website"""
        # Extract from city name or portal config
        city_key = city_name.lower().replace(' ', '_').replace(',', '').replace('va', '').strip()
        
        for key, config in self.CITY_PORTALS.items():
            if city_key in key or city_key in config['name'].lower():
                url = config['url']
                # Extract base URL (protocol + domain)
                match = re.match(r'(https?://[^/]+)', url)
                return match.group(1) if match else ''
        
        return ''
    
    def _is_valid_city_contract(self, contract: Dict) -> bool:
        """
        Validate city contract
        
        Args:
            contract: Contract dictionary
            
        Returns:
            True if valid
        """
        # Must have title
        if not contract.get('title') or len(contract['title']) < 10:
            return False
        
        # Must be cleaning-related
        text = f"{contract.get('title', '')} {contract.get('description', '')}"
        if not self.is_cleaning_related(text):
            return False
        
        return True
    
    def scrape_specific_city(self, city_key: str) -> List[Dict]:
        """
        Scrape a specific city
        
        Args:
            city_key: City identifier
            
        Returns:
            List of contracts for that city
        """
        config = self.CITY_PORTALS.get(city_key)
        
        if not config:
            logger.error(f"[{self.name}] Unknown city: {city_key}")
            return []
        
        logger.info(f"[{self.name}] Scraping {config['name']}...")
        return self._scrape_city(city_key, config)
