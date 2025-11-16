"""
Nationwide State Portal Scraper
Scrapes procurement portals for all 50 US states
"""

from .base_scraper import BaseScraper, logger
from typing import List, Dict
import concurrent.futures


class StatePortalScraper(BaseScraper):
    """
    Scraper for state procurement portals across all 50 US states
    """
    
    # State procurement portal URLs
    STATE_PORTALS = {
        'AL': 'https://www.purchasing.alabama.gov',
        'AK': 'https://online.doa.alaska.gov/webapp/PRDSCMNT/AltSelfService',
        'AZ': 'https://app.az.gov/apps/pr/procurement/search',
        'AR': 'https://www.dfa.arkansas.gov/offices/procurement',
        'CA': 'https://caleprocure.ca.gov',
        'CO': 'https://www.bidnet.com/colorado',
        'CT': 'https://portal.ct.gov/DAS/Procurement/Procurement',
        'DE': 'https://bids.delaware.gov',
        'FL': 'https://www.myflorida.com/apps/vbs/vbs_www.main_menu',
        'GA': 'https://doas.ga.gov/state-purchasing',
        'HI': 'http://hands.ehawaii.gov/hands/opportunities',
        'ID': 'https://purchasing.idaho.gov/solicitation-search',
        'IL': 'https://www.illinois.gov/cms/business/sell/procurement',
        'IN': 'https://fs.gmis.in.gov/psp/guest/SUPPLIER/ERP/c/SCP_PUBLIC_MENU.SCP_PUB_BID.GBL',
        'IA': 'https://bidopportunities.iowa.gov',
        'KS': 'https://admin.ks.gov/offices/ofd/procurement',
        'KY': 'https://emars.ky.gov/webapp/vssonline/AltSelfService',
        'LA': 'https://wwwcfprd.doa.louisiana.gov/osp/lapac/pubMain.cfm',
        'ME': 'https://www.maine.gov/bids',
        'MD': 'https://emaryland.adp.com/psp/bnprd/SUPPLIER/ERP/c/BA_BA_MENU.BA_SOURCING_SS.GBL',
        'MA': 'https://www.commbuys.com',
        'MI': 'https://sigma.michigan.gov',
        'MN': 'https://mn.gov/admin/business/sell-to-state/bids',
        'MS': 'https://www.dfa.ms.gov/purchasing/bid-opportunities',
        'MO': 'https://oa.mo.gov/purchasing/standard-bid-opening-calendar',
        'MT': 'https://marketplace.mt.gov',
        'NE': 'https://ne.gov/das/materiel',
        'NV': 'https://purchasing.nv.gov',
        'NH': 'https://das.nh.gov/purchasing',
        'NJ': 'https://www.njstart.gov',
        'NM': 'https://www.generalservices.state.nm.us/state-purchasing',
        'NY': 'https://ogs.ny.gov/procurement',
        'NC': 'https://www.ips.state.nc.us/ips',
        'ND': 'https://www.nd.gov/cs/procurement',
        'OH': 'https://procure.ohio.gov/proc',
        'OK': 'https://www.ok.gov/dcs/Purchasing',
        'OR': 'https://orpin.oregon.gov/open.dll',
        'PA': 'https://www.emarketplace.state.pa.us',
        'RI': 'https://www.purchasing.ri.gov',
        'SC': 'https://procurement.sc.gov',
        'SD': 'https://bfm.sd.gov/procurement/bidding.aspx',
        'TN': 'https://www.tn.gov/generalservices/procurement.html',
        'TX': 'https://www.txsmartbuy.com/esbd',
        'UT': 'https://purchasing.utah.gov',
        'VT': 'https://bgs.vermont.gov/purchasing-contracting/forms',
        'VA': 'https://eva.virginia.gov',
        'WA': 'https://fortress.wa.gov/ga/webs/current',
        'WV': 'https://state.wv.us/admin/purchase/swc/default.html',
        'WI': 'https://vendornet.state.wi.us',
        'WY': 'https://ai.wyo.gov/divisions/procurement-program'
    }
    
    def __init__(self, states: List[str] = None):
        """
        Initialize state portal scraper
        
        Args:
            states: List of state codes to scrape (default: all 50 states)
        """
        super().__init__(
            name='State Portals',
            base_url='',  # Multiple URLs
            rate_limit=5.0  # Conservative rate limit for state servers
        )
        
        self.states = states if states else list(self.STATE_PORTALS.keys())
    
    def scrape(self) -> List[Dict]:
        """
        Scrape all configured state portals
        
        Returns:
            List of contract dictionaries from all states
        """
        logger.info(f"[{self.name}] Starting scrape for {len(self.states)} states...")
        all_contracts = []
        
        # Scrape states sequentially (can be parallelized if needed)
        for state_code in self.states:
            try:
                logger.info(f"[{self.name}] Scraping {state_code}...")
                
                contracts = self._scrape_state(state_code)
                all_contracts.extend(contracts)
                
                logger.info(f"[{self.name}] {state_code}: Found {len(contracts)} contracts")
            
            except Exception as e:
                logger.error(f"[{self.name}] Error scraping {state_code}: {e}")
                continue
        
        logger.info(f"[{self.name}] ✅ Total contracts found: {len(all_contracts)}")
        return all_contracts
    
    def _scrape_state(self, state_code: str) -> List[Dict]:
        """
        Scrape a single state portal
        
        Args:
            state_code: Two-letter state code
            
        Returns:
            List of contracts for that state
        """
        portal_url = self.STATE_PORTALS.get(state_code)
        
        if not portal_url:
            logger.warning(f"[{self.name}] No portal URL for {state_code}")
            return []
        
        contracts = []
        
        try:
            # Fetch the main procurement page
            response = self.fetch_page(portal_url)
            
            if not response:
                logger.warning(f"[{self.name}] Failed to fetch {state_code} portal")
                return []
            
            soup = self.parse_html(response.text)
            
            # Generic selectors for procurement listings
            # These work for many state portals
            potential_selectors = [
                '.bid-listing',
                '.procurement-listing',
                'tr.bid-row',
                '.opportunity',
                'div[class*="solicitation"]',
                'tr[class*="bid"]'
            ]
            
            listings = []
            for selector in potential_selectors:
                found = soup.select(selector)
                if found:
                    listings.extend(found)
                    break
            
            if not listings:
                # Try to find any links that might be bids/solicitations
                listings = soup.find_all('a', href=re.compile(r'(bid|solicitation|rfp|rfq)', re.I))
            
            logger.info(f"[{self.name}] {state_code}: Found {len(listings)} potential listings")
            
            for listing in listings[:20]:  # Limit to first 20 to avoid overload
                try:
                    contract = self._parse_state_listing(listing, state_code)
                    
                    if contract and self._is_cleaning_contract(contract):
                        contracts.append(contract)
                
                except Exception as e:
                    logger.debug(f"[{self.name}] {state_code}: Error parsing listing: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"[{self.name}] Error scraping {state_code}: {e}")
        
        return contracts
    
    def _parse_state_listing(self, listing, state_code: str) -> Dict:
        """
        Parse a procurement listing from any state portal
        
        Args:
            listing: BeautifulSoup element
            state_code: State code
            
        Returns:
            Contract dictionary
        """
        # Extract text content
        text = listing.get_text()
        
        # Try to extract title
        title_elem = (listing.find('a') or 
                     listing.select_one('.title, .solicitation-title') or
                     listing)
        title = title_elem.get_text(strip=True) if title_elem else text[:100]
        
        # Extract URL
        url = None
        link = listing.find('a')
        if link and link.get('href'):
            url = link['href']
            if not url.startswith('http'):
                base_url = self.STATE_PORTALS.get(state_code, '')
                url = f"{base_url}{url}" if base_url else url
        
        # Try to extract deadline
        deadline_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
        deadline = self.parse_date(deadline_match.group(1)) if deadline_match else None
        
        # Extract agency if visible
        agency_match = re.search(r'Agency[:\s]+([^\n]{3,50})', text, re.I)
        agency = agency_match.group(1).strip() if agency_match else f'{state_code} State Government'
        
        contract = {
            'title': title,
            'agency': agency,
            'location': state_code,
            'value': None,
            'deadline': deadline,
            'description': text[:500],  # First 500 chars as description
            'naics_code': '561720',
            'url': url,
            'state_code': state_code
        }
        
        return contract
    
    def _is_cleaning_contract(self, contract: Dict) -> bool:
        """
        Check if contract is cleaning-related
        
        Args:
            contract: Contract dictionary
            
        Returns:
            True if cleaning-related
        """
        text = f"{contract.get('title', '')} {contract.get('description', '')}"
        return self.is_cleaning_related(text)
    
    def scrape_parallel(self, max_workers: int = 5) -> List[Dict]:
        """
        Scrape multiple states in parallel
        
        Args:
            max_workers: Maximum concurrent workers
            
        Returns:
            List of all contracts
        """
        logger.info(f"[{self.name}] Starting parallel scrape with {max_workers} workers...")
        
        all_contracts = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping tasks for each state
            future_to_state = {
                executor.submit(self._scrape_state, state): state 
                for state in self.states
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_state):
                state = future_to_state[future]
                try:
                    contracts = future.result()
                    all_contracts.extend(contracts)
                    logger.info(f"[{self.name}] {state}: Completed with {len(contracts)} contracts")
                except Exception as e:
                    logger.error(f"[{self.name}] {state}: Failed with error: {e}")
        
        logger.info(f"[{self.name}] ✅ Parallel scrape complete. Total: {len(all_contracts)} contracts")
        return all_contracts
