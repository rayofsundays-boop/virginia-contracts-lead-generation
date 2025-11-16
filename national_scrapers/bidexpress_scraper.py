"""
BidExpress Scraper
Used by many states and cities for construction/facilities bids
"""

import logging
from typing import List, Dict, Any
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BidExpressScraper(BaseScraper):
    """
    Scraper for BidExpress platform.
    Many states and cities use this for bidding.
    """
    
    BASE_URL = 'https://www.bidexpress.com'
    RSS_TEMPLATE = 'https://www.bidexpress.com/businesses/{business_id}/rss'
    
    # Common business IDs for major states/regions
    BUSINESS_IDS = {
        'FL': '303803',  # Florida DOT
        'TX': '303801',  # Texas DOT
        'CA': '303802',  # California DOT
        'NY': '303804',  # New York DOT
        'PA': '303805',  # Pennsylvania DOT
        'OH': '303806',  # Ohio DOT
        'NC': '303807',  # North Carolina DOT
        'VA': '303808',  # Virginia DOT
    }
    
    def __init__(self):
        super().__init__(source_name='bidexpress')
    
    def scrape(self, business_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape BidExpress RSS feeds.
        
        Args:
            business_ids: List of business IDs to scrape
            
        Returns:
            List of standardized contracts
        """
        if business_ids is None:
            business_ids = list(self.BUSINESS_IDS.values())
        
        logger.info(f"Scraping BidExpress ({len(business_ids)} feeds)")
        
        all_contracts = []
        
        for business_id in business_ids:
            try:
                url = self.RSS_TEMPLATE.format(business_id=business_id)
                contracts = self._scrape_rss_feed(url)
                all_contracts.extend(contracts)
            except Exception as e:
                logger.error(f"Error scraping BidExpress feed {business_id}: {e}")
                continue
        
        logger.info(f"BidExpress scraper found {len(all_contracts)} opportunities")
        return all_contracts
    
    def _scrape_rss_feed(self, rss_url: str) -> List[Dict[str, Any]]:
        """
        Scrape a single RSS feed.
        
        Args:
            rss_url: RSS feed URL
            
        Returns:
            List of contracts
        """
        feed = self.parse_rss(rss_url)
        if not feed or not feed.entries:
            logger.warning(f"No entries in RSS feed: {rss_url}")
            return []
        
        contracts = []
        
        for entry in feed.entries:
            try:
                title = entry.get('title', 'No Title')
                
                # Filter for cleaning/facilities
                if not self.is_cleaning_related(title):
                    continue
                
                # Extract link
                link = entry.get('link', '')
                
                # Extract published date
                published = entry.get('published', '')
                
                # Extract description for more context
                description = entry.get('summary', '')
                
                # Try to extract state from title or description
                state = 'US'
                combined = f"{title} {description}"
                for state_code, business_id in self.BUSINESS_IDS.items():
                    if business_id in rss_url or state_code in combined:
                        state = state_code
                        break
                
                # Generate solicitation number from entry ID or link
                sol_num = entry.get('id', 'N/A')
                if sol_num == 'N/A' and link:
                    # Extract from URL
                    parts = link.split('/')
                    sol_num = parts[-1] if parts else 'N/A'
                
                contract = self.standardize_contract(
                    state=state,
                    title=title,
                    solicitation_number=sol_num,
                    due_date=published,
                    link=link,
                    agency='BidExpress',
                    description=description[:200]
                )
                
                contracts.append(contract)
                
            except Exception as e:
                logger.error(f"Error parsing BidExpress RSS entry: {e}")
                continue
        
        return contracts
