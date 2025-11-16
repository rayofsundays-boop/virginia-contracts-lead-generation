"""
Virginia eVA Scraper - COMPLETELY REBUILT 2025
NEW CGI Portal with POST-only search endpoint
OLD URL: https://eva.virginia.gov (DEAD/404)
NEW URL: https://mvendor.epro.cgipdc.com/webapp/VSSAPPX/Advantage
"""

import re
from typing import List, Dict, Optional
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class EVAVirginiaScraperV2(BaseScraper):
    """
    Virginia eVA Procurement Portal Scraper - REBUILT FOR NEW PLATFORM
    
    Critical Changes:
    - NEW BASE URL: https://mvendor.epro.cgipdc.com/webapp/VSSAPPX/Advantage
    - POST-only search endpoint (GET not supported)
    - Form data required: keyword, searchType, status
    - New HTML structure and selectors
    - Enhanced headers (Referer, Origin required)
    """
    
    def __init__(self, rate_limit: float = 3.0):
        super().__init__(
            name='EVA_Virginia_V2',
            base_url='https://mvendor.epro.cgipdc.com/webapp/VSSAPPX/Advantage',
            rate_limit=rate_limit
        )
        
        # NEW search endpoint (POST only)
        self.search_url = 'https://mvendor.epro.cgipdc.com/webapp/VSSAPPX/Advantage/SolicitationSearch'
        
        # Keywords for janitorial/cleaning contracts
        self.keywords = ['janitorial', 'custodial', 'cleaning', 'housekeeping']
    
    def scrape(self) -> List[Dict]:
        """
        Scrape Virginia eVA portal using NEW POST endpoint
        
        Returns:
            List of standardized contract dictionaries
        """
        all_contracts = []
        
        for keyword in self.keywords:
            logger.info(f"\n🔍 Searching eVA for: {keyword}")
            
            # POST form data
            post_data = {
                'keyword': keyword,
                'searchType': 'all',
                'status': 'open',
                'nigpCode': '',  # Optional: 961 for janitorial services
                'dateFrom': '',
                'dateTo': ''
            }
            
            # Required headers for eVA POST
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self.base_url,
                'Origin': 'https://mvendor.epro.cgipdc.com',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Fetch search results
            html = self.fetch_page(
                url=self.search_url,
                method='POST',
                data=post_data,
                headers=headers
            )
            
            if not html:
                logger.warning(f"No HTML returned for keyword: {keyword}")
                continue
            
            # Parse listings
            soup = self.parse_html(html)
            if not soup:
                continue
            
            contracts = self._parse_search_results(soup)
            all_contracts.extend(contracts)
            
            logger.info(f"✅ Found {len(contracts)} contracts for '{keyword}'")
        
        # Remove duplicates by solicitation number
        unique_contracts = self._deduplicate(all_contracts)
        
        logger.info(f"\n📊 Total unique contracts: {len(unique_contracts)}")
        return unique_contracts
    
    def _parse_search_results(self, soup) -> List[Dict]:
        """
        Parse search results HTML from NEW eVA platform
        
        Updated selectors for CGI portal:
        - Listings: .solicitation-row, tr.sol-item, table tbody tr
        - Title: .sol-title, td:nth-child(2)
        - Number: .sol-number, td:nth-child(1)
        - Agency: .agency-name, td:nth-child(3)
        - Due date: .due-date, td:nth-child(5)
        """
        contracts = []
        
        # Try multiple selector patterns for listings
        listings = (
            soup.select('.solicitation-row') or
            soup.select('tr.sol-item') or
            soup.select('table.solicitations tbody tr') or
            soup.select('.opportunity-item') or
            soup.select('tbody tr')  # Fallback to generic table rows
        )
        
        logger.info(f"Found {len(listings)} potential listings")
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.debug(f"Failed to parse listing: {e}")
                continue
        
        return contracts
    
    def _parse_listing(self, listing) -> Optional[Dict]:
        """
        Parse individual solicitation listing
        
        Args:
            listing: BeautifulSoup element (table row or div)
            
        Returns:
            Standardized contract dictionary or None
        """
        try:
            # Extract text from cells
            cells = listing.find_all('td')
            
            if len(cells) >= 4:
                # Table format
                number = cells[0].get_text(strip=True) if cells else ''
                title = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                agency = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                due_date = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                
                # Extract link
                link_elem = cells[1].find('a') if len(cells) > 1 else listing.find('a')
                link = link_elem.get('href', '') if link_elem else ''
            else:
                # Div format (fallback)
                title = self.extract_text(listing, '.sol-title, .title, h3, strong')
                number = self.extract_text(listing, '.sol-number, .number')
                agency = self.extract_text(listing, '.agency-name, .agency')
                due_date = self.extract_text(listing, '.due-date, .close-date')
                
                link_elem = listing.find('a')
                link = link_elem.get('href', '') if link_elem else ''
            
            # Validate required fields
            if not title or not number:
                return None
            
            # Standardize output
            return self.standardize_contract(
                state='VA',
                title=title,
                solicitation_number=number,
                due_date=due_date,
                link=link,
                agency=agency,
                naics_code='561720',  # Janitorial Services
                data_source='EVA Virginia'
            )
        
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
    
    def _deduplicate(self, contracts: List[Dict]) -> List[Dict]:
        """Remove duplicate contracts by solicitation number"""
        seen = set()
        unique = []
        
        for contract in contracts:
            sol_num = contract.get('solicitation_number', '')
            if sol_num and sol_num not in seen:
                seen.add(sol_num)
                unique.append(contract)
        
        return unique
    
    def fetch_detail_page(self, sol_number: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific solicitation
        
        Args:
            sol_number: Solicitation number
            
        Returns:
            Detailed contract information
        """
        detail_url = f"{self.base_url}/SolicitationDetail?solNum={sol_number}"
        
        html = self.fetch_page(detail_url, method='GET')
        
        if not html:
            return None
        
        soup = self.parse_html(html)
        if not soup:
            return None
        
        # Extract additional details
        details = {
            'description': self.extract_text(soup, '.description, #description'),
            'contact_name': self.extract_text(soup, '.contact-name, #contactName'),
            'contact_email': self.extract_text(soup, '.contact-email, #contactEmail'),
            'contact_phone': self.extract_text(soup, '.contact-phone, #contactPhone'),
            'estimated_value': self.extract_text(soup, '.estimated-value, #estValue'),
            'issue_date': self.extract_text(soup, '.issue-date, #issueDate'),
            'questions_due': self.extract_text(soup, '.questions-due, #questionsDue')
        }
        
        return details


def test_eva_scraper():
    """Test Virginia eVA scraper with NEW POST endpoint"""
    scraper = EVAVirginiaScraperV2(rate_limit=3.0)
    
    logger.info("\n🧪 TESTING VIRGINIA eVA SCRAPER (NEW POST ENDPOINT)\n")
    logger.info("="*70)
    
    contracts = scraper.scrape()
    
    logger.info(f"\n📊 RESULTS: {len(contracts)} contracts found\n")
    
    # Show first 10 results
    for i, contract in enumerate(contracts[:10], 1):
        logger.info(f"\n{i}. {contract['title']}")
        logger.info(f"   Number: {contract['solicitation_number']}")
        logger.info(f"   Agency: {contract['agency']}")
        logger.info(f"   Due: {contract['due_date']}")
        logger.info(f"   Link: {contract['link']}")
    
    return contracts


if __name__ == '__main__':
    test_eva_scraper()
