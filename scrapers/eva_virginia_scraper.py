"""
EVA Virginia State Scraper
Scrapes eVA.virginia.gov for janitorial/cleaning RFPs
"""

from .base_scraper import BaseScraper, logger
from typing import List, Dict
import re


class EVAVirginiaScraper(BaseScraper):
    """
    Scraper for Virginia's eVA procurement portal
    https://eva.virginia.gov/
    """
    
    def __init__(self):
        super().__init__(
            name='EVA Virginia',
            base_url='https://eva.virginia.gov',
            rate_limit=3.0  # Be respectful to state servers
        )
        
        # EVA search parameters for janitorial services
        self.search_params = {
            'keywords': ['janitorial', 'custodial', 'cleaning', 'housekeeping'],
            'naics_codes': ['561720'],  # Janitorial Services NAICS
        }
    
    def scrape(self) -> List[Dict]:
        """
        Scrape EVA for cleaning contracts
        
        Returns:
            List of contract dictionaries
        """
        logger.info(f"[{self.name}] Starting scrape...")
        contracts = []
        
        try:
            # EVA uses a search interface
            # Note: This is a simplified implementation
            # Real implementation would need to handle:
            # - Login/authentication if required
            # - Pagination
            # - Search filters
            # - JavaScript-rendered content (may need Selenium)
            
            search_url = f"{self.base_url}/page.aspx/public/purchasing/search"
            
            for keyword in self.search_params['keywords']:
                logger.info(f"[{self.name}] Searching for: {keyword}")
                
                # Construct search URL with parameters
                params = {
                    'keyword': keyword,
                    'status': 'open',
                    'sort': 'deadline'
                }
                
                response = self.fetch_page(search_url)
                
                if not response:
                    logger.warning(f"[{self.name}] Failed to fetch search results for: {keyword}")
                    continue
                
                # Parse search results
                soup = self.parse_html(response.text)
                
                # Find contract listings (CSS selectors may need adjustment)
                listings = soup.select('.procurement-listing, .bid-listing, tr.bid-row')
                
                logger.info(f"[{self.name}] Found {len(listings)} potential listings")
                
                for listing in listings:
                    try:
                        contract = self._parse_listing(listing)
                        
                        if contract and self._is_valid_contract(contract):
                            contracts.append(contract)
                            logger.info(f"[{self.name}] ✅ Extracted: {contract.get('title', 'Untitled')}")
                    
                    except Exception as e:
                        logger.error(f"[{self.name}] Error parsing listing: {e}")
                        continue
            
            logger.info(f"[{self.name}] ✅ Scrape complete. Found {len(contracts)} contracts")
            return contracts
        
        except Exception as e:
            logger.error(f"[{self.name}] ❌ Scrape failed: {e}")
            return []
    
    def _parse_listing(self, listing) -> Dict:
        """
        Parse individual contract listing
        
        Args:
            listing: BeautifulSoup element for listing
            
        Returns:
            Contract dictionary
        """
        # Extract basic information
        # Note: Selectors are examples and may need adjustment based on actual HTML
        
        title = self.extract_text(listing, '.title, .solicitation-title, td:nth-child(2)')
        agency = self.extract_text(listing, '.agency, .organization, td:nth-child(1)')
        
        # Extract deadline
        deadline_text = self.extract_text(listing, '.deadline, .due-date, td:nth-child(4)')
        deadline = self.parse_date(deadline_text)
        
        # Extract solicitation number
        solicitation_num = self.extract_text(listing, '.solicitation-number, .rfp-number')
        
        # Build URL to detail page
        detail_link = self.extract_attribute(listing, 'a', 'href')
        if detail_link and not detail_link.startswith('http'):
            detail_link = f"{self.base_url}{detail_link}"
        
        # Extract value if visible
        value_text = self.extract_text(listing, '.value, .amount, .estimated-value')
        
        contract = {
            'title': title,
            'agency': agency or 'Virginia State Government',
            'location': 'Virginia',
            'value': value_text,
            'deadline': deadline,
            'description': f"Solicitation {solicitation_num}: {title}" if solicitation_num else title,
            'naics_code': '561720',
            'url': detail_link,
            'solicitation_number': solicitation_num
        }
        
        # Fetch detail page for more information
        if detail_link:
            details = self._fetch_details(detail_link)
            if details:
                contract.update(details)
        
        return contract
    
    def _fetch_details(self, url: str) -> Dict:
        """
        Fetch additional details from contract detail page
        
        Args:
            url: Detail page URL
            
        Returns:
            Dictionary with additional details
        """
        try:
            response = self.fetch_page(url)
            if not response:
                return {}
            
            soup = self.parse_html(response.text)
            
            details = {}
            
            # Extract full description
            description = self.extract_text(soup, '.description, .scope-of-work, #description')
            if description:
                details['description'] = description
            
            # Extract contact information
            contact_section = soup.select_one('.contact-info, .buyer-info')
            if contact_section:
                contact_text = contact_section.get_text()
                
                details['contact_email'] = self.extract_email(contact_text)
                details['contact_phone'] = self.extract_phone(contact_text)
                
                # Try to extract contact name
                name_elem = contact_section.select_one('.name, .contact-name')
                if name_elem:
                    details['contact_name'] = name_elem.get_text(strip=True)
            
            # Extract estimated value
            value_text = self.extract_text(soup, '.estimated-value, .contract-value')
            if value_text:
                details['value'] = value_text
            
            return details
        
        except Exception as e:
            logger.warning(f"[{self.name}] Error fetching details from {url}: {e}")
            return {}
    
    def _is_valid_contract(self, contract: Dict) -> bool:
        """
        Validate if contract is relevant and complete
        
        Args:
            contract: Contract dictionary
            
        Returns:
            True if valid
        """
        # Must have title
        if not contract.get('title'):
            return False
        
        # Must be cleaning-related
        title_and_desc = f"{contract.get('title', '')} {contract.get('description', '')}"
        if not self.is_cleaning_related(title_and_desc):
            logger.debug(f"[{self.name}] Skipping non-cleaning contract: {contract.get('title')}")
            return False
        
        # Should have a deadline (preferably in the future)
        if not contract.get('deadline'):
            logger.debug(f"[{self.name}] Skipping contract without deadline: {contract.get('title')}")
            return False
        
        return True
    
    def scrape_alternative_method(self) -> List[Dict]:
        """
        Alternative scraping method using direct URLs or API if available
        
        This method can be used if the main scrape() method encounters issues
        """
        logger.info(f"[{self.name}] Trying alternative scraping method...")
        
        # Example: Direct URLs to known procurement pages
        known_urls = [
            f"{self.base_url}/page.aspx/public/purchasing/opportunity/open",
            f"{self.base_url}/page.aspx/public/purchasing/search"
        ]
        
        contracts = []
        
        for url in known_urls:
            try:
                response = self.fetch_page(url)
                if response:
                    soup = self.parse_html(response.text)
                    # Parse page-specific format
                    # Implementation would depend on actual page structure
                    pass
            except Exception as e:
                logger.error(f"[{self.name}] Error with alternative method: {e}")
        
        return contracts
