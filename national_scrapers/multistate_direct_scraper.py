"""
Multi-State Direct Portal Scraper
Covers Symphony-blocked states with direct state portal access
No proxies needed - uses official public procurement portals
"""

import logging
from typing import List, Dict, Any
from national_scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class MultiStateDirectScraper(BaseScraper):
    """
    Scraper for states that Symphony blocks.
    Uses each state's official procurement portal directly.
    """
    
    # Direct state portal URLs (official government sites)
    STATE_PORTALS = {
        'CA': {
            'name': 'California',
            'url': 'https://caleprocure.ca.gov/pages/index.aspx',
            'type': 'html'
        },
        'TX': {
            'name': 'Texas',
            'url': 'https://www.txsmartbuy.com/esbd',
            'type': 'html'
        },
        'CO': {
            'name': 'Colorado',
            'url': 'https://www.colorado.gov/bidops',
            'type': 'html'
        },
        'GA': {
            'name': 'Georgia',
            'url': 'https://doas.ga.gov/state-purchasing/solicitations',
            'type': 'html'
        },
        'IL': {
            'name': 'Illinois',
            'url': 'https://www.illinois.gov/sites/procurement/Pages/default.aspx',
            'type': 'html'
        },
        'OH': {
            'name': 'Ohio',
            'url': 'https://procure.ohio.gov/Vendor',
            'type': 'html'
        },
        'MI': {
            'name': 'Michigan',
            'url': 'https://sigma.michigan.gov',
            'type': 'html'
        },
        'WA': {
            'name': 'Washington',
            'url': 'https://fortress.wa.gov/ga/webs/index.aspx',
            'type': 'html'
        },
        'TN': {
            'name': 'Tennessee',
            'url': 'https://www.tn.gov/generalservices/procurement/central-procurement-office--cpo-/vendor-information.html',
            'type': 'html'
        },
        'OR': {
            'name': 'Oregon',
            'url': 'https://oregonbuys.gov/bso/',
            'type': 'html'
        },
        'NV': {
            'name': 'Nevada',
            'url': 'https://nevadaepro.com/bso/',
            'type': 'html'
        },
        'NM': {
            'name': 'New Mexico',
            'url': 'https://www.generalservices.state.nm.us/state-purchasing/',
            'type': 'html'
        },
        'MO': {
            'name': 'Missouri',
            'url': 'https://oa.mo.gov/purchasing/vendor-resources',
            'type': 'html'
        },
        'MN': {
            'name': 'Minnesota',
            'url': 'https://mn.gov/admin/osp/businesses/',
            'type': 'html'
        },
        'WI': {
            'name': 'Wisconsin',
            'url': 'https://vendornet.state.wi.us/vendornet/asp/welcome.asp',
            'type': 'html'
        },
        'SC': {
            'name': 'South Carolina',
            'url': 'https://procurement.sc.gov/node/1542',
            'type': 'html'
        },
        'KY': {
            'name': 'Kentucky',
            'url': 'https://emars.ky.gov/webapp/vssonline/AltSelfService',
            'type': 'html'
        },
        'OK': {
            'name': 'Oklahoma',
            'url': 'https://www.ok.gov/dcs/State_Purchasing/',
            'type': 'html'
        },
        'UT': {
            'name': 'Utah',
            'url': 'https://purchasing.utah.gov/bids/',
            'type': 'html'
        },
        'ID': {
            'name': 'Idaho',
            'url': 'https://adm.idaho.gov/purchasing/',
            'type': 'html'
        },
        'HI': {
            'name': 'Hawaii',
            'url': 'https://hands.ehawaii.gov/hands/opportunities',
            'type': 'html'
        },
        'ME': {
            'name': 'Maine',
            'url': 'https://www.maine.gov/dafs/bbm/procurement/vendors',
            'type': 'html'
        },
        'MS': {
            'name': 'Mississippi',
            'url': 'https://www.dfa.ms.gov/office-of-purchasing-travel-and-fleet-management/office-of-purchasing/',
            'type': 'html'
        },
        'MT': {
            'name': 'Montana',
            'url': 'https://gsd.mt.gov/Procurement-and-Contracts/Procurement',
            'type': 'html'
        },
        'ND': {
            'name': 'North Dakota',
            'url': 'https://www.nd.gov/omb/public/procurement',
            'type': 'html'
        },
        'KS': {
            'name': 'Kansas',
            'url': 'https://admin.ks.gov/offices/procurement-and-contracts',
            'type': 'html'
        },
        'CT': {
            'name': 'Connecticut',
            'url': 'https://portal.ct.gov/DAS/Procurement/Bidders-Guide',
            'type': 'html'
        },
        'AK': {
            'name': 'Alaska',
            'url': 'https://aws.state.ak.us/OASysContracts/Contracts/search.aspx',
            'type': 'html'
        },
        'AL': {
            'name': 'Alabama',
            'url': 'https://www.alabamabids.alabama.gov/',
            'type': 'html'
        },
        'AR': {
            'name': 'Arkansas',
            'url': 'https://www.dfa.arkansas.gov/offices/procurement/procurement-services/',
            'type': 'html'
        },
        'DE': {
            'name': 'Delaware',
            'url': 'https://bids.delaware.gov/',
            'type': 'html'
        },
        'FL': {
            'name': 'Florida',
            'url': 'https://vendor.myfloridamarketplace.com/search/bids',
            'type': 'html'
        },
        'IN': {
            'name': 'Indiana',
            'url': 'https://www.in.gov/idoa/procurement/',
            'type': 'html'
        },
        'IA': {
            'name': 'Iowa',
            'url': 'https://das.iowa.gov/procurement',
            'type': 'html'
        },
        'LA': {
            'name': 'Louisiana',
            'url': 'https://wwwcfprd.doa.louisiana.gov/osp/lapac/vendor/vsspBidList.cfm',
            'type': 'html'
        },
        'NE': {
            'name': 'Nebraska',
            'url': 'https://das.nebraska.gov/materiel/purchasing.html',
            'type': 'html'
        },
        'NJ': {
            'name': 'New Jersey',
            'url': 'https://www.njstart.gov/bso/',
            'type': 'html'
        },
        'NC': {
            'name': 'North Carolina',
            'url': 'https://www.ips.state.nc.us/ips/',
            'type': 'html'
        },
        'PA': {
            'name': 'Pennsylvania',
            'url': 'https://www.emarketplace.state.pa.us/EP_Default.aspx',
            'type': 'html'
        },
        'SD': {
            'name': 'South Dakota',
            'url': 'https://boa.sd.gov/procurement-management/',
            'type': 'html'
        },
        'VT': {
            'name': 'Vermont',
            'url': 'https://bgs.vermont.gov/purchasing-contracting/forms',
            'type': 'html'
        },
        'WV': {
            'name': 'West Virginia',
            'url': 'https://purchasing.wv.gov/vendor/Pages/default.aspx',
            'type': 'html'
        },
        'WY': {
            'name': 'Wyoming',
            'url': 'https://ai.wyo.gov/divisions/procurement-and-property',
            'type': 'html'
        },
        'NY': {
            'name': 'New York',
            'url': 'https://www.ogs.ny.gov/procurement/',
            'type': 'html'
        },
        'VA': {
            'name': 'Virginia',
            'url': 'https://eva.virginia.gov/',
            'type': 'html'
        }
    }
    
    def __init__(self):
        super().__init__(source_name='state_direct')
    
    def scrape(self, states: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape direct state portals.
        
        Args:
            states: List of state codes to scrape
            
        Returns:
            List of standardized contracts
        """
        if states is None:
            states = list(self.STATE_PORTALS.keys())
        
        all_contracts = []
        
        for state_code in states:
            if state_code not in self.STATE_PORTALS:
                logger.warning(f"State {state_code} not configured for direct scraping")
                continue
            
            logger.info(f"Scraping {state_code} direct portal")
            contracts = self._scrape_state(state_code)
            all_contracts.extend(contracts)
        
        logger.info(f"Direct portal scraper found {len(all_contracts)} total opportunities")
        return all_contracts
    
    def _scrape_state(self, state_code: str) -> List[Dict[str, Any]]:
        """
        Scrape a single state's direct portal.
        
        Args:
            state_code: 2-letter state code
            
        Returns:
            List of contracts
        """
        portal = self.STATE_PORTALS[state_code]
        state_name = portal['name']
        url = portal['url']
        
        # Add state-specific headers
        headers = {
            **self.DEFAULT_HEADERS,
            'Referer': url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = self.fetch_page(url, headers=headers)
        if not response:
            logger.error(f"Failed to fetch {state_name} portal")
            return []
        
        soup = self.parse_html(response)
        if not soup:
            return []
        
        contracts = []
        
        # Try multiple common selectors used by state portals
        selectors = [
            {'class': ['solicitation', 'bid-item', 'opportunity-row', 'rfp-item', 'procurement-listing']},
            {'class': ['item', 'listing', 'row', 'entry']},
            {'id': ['solicitations', 'bids', 'opportunities']}
        ]
        
        listings = []
        for selector in selectors:
            if 'class' in selector:
                listings = soup.find_all(['div', 'tr', 'article', 'li'], class_=selector['class'])
            elif 'id' in selector:
                for id_val in selector['id']:
                    container = soup.find('div', {'id': id_val})
                    if container:
                        listings = container.find_all(['div', 'tr', 'li'])
                        break
            
            if listings:
                break
        
        # If no listings found, try table rows as fallback
        if not listings:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                if rows:
                    listings = rows
                    break
        
        if not listings:
            logger.warning(f"No listings found on {state_name} portal")
            return []
        
        for listing in listings:
            try:
                contract = self._parse_listing(listing, state_code, state_name)
                if contract and self.is_cleaning_related(contract.get('title', '')):
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing {state_name} listing: {e}")
                continue
        
        logger.info(f"{state_name} found {len(contracts)} cleaning-related contracts")
        return contracts
    
    def _parse_listing(self, listing, state_code: str, state_name: str) -> Dict[str, Any]:
        """
        Parse individual listing from state portal.
        
        Args:
            listing: BeautifulSoup element
            state_code: State code
            state_name: State name
            
        Returns:
            Standardized contract dict
        """
        # Extract title - try multiple selectors
        title_elem = listing.find(['a', 'h2', 'h3', 'h4', 'span', 'td'], 
                                  class_=['title', 'solicitation-title', 'name', 'subject'])
        if not title_elem:
            title_elem = listing.find('a')
        
        title = title_elem.get_text(strip=True) if title_elem else 'No Title'
        
        # Extract link
        link = ''
        if title_elem and title_elem.name == 'a':
            link = title_elem.get('href', '')
            if link and not link.startswith('http'):
                base_url = self.STATE_PORTALS[state_code]['url']
                if link.startswith('/'):
                    # Absolute path
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    link = f"{parsed.scheme}://{parsed.netloc}{link}"
                else:
                    # Relative path
                    link = f"{base_url.rsplit('/', 1)[0]}/{link}"
        
        # Extract solicitation number
        cells = listing.find_all('td')
        sol_number = 'N/A'
        
        if cells and len(cells) > 0:
            sol_number = cells[0].get_text(strip=True)
        else:
            sol_elem = listing.find(['span', 'div'], class_=['sol-number', 'rfp-number', 'bid-number', 'number', 'id'])
            if sol_elem:
                sol_number = sol_elem.get_text(strip=True)
        
        # Extract due date
        due_date = ''
        if cells and len(cells) > 2:
            # Usually last column
            due_date = cells[-1].get_text(strip=True)
        else:
            due_elem = listing.find(['span', 'time', 'div'], class_=['due-date', 'closing-date', 'deadline', 'due', 'close-date'])
            if due_elem:
                due_date = due_elem.get_text(strip=True)
        
        # Extract agency
        agency = state_name
        if cells and len(cells) > 1:
            agency = cells[1].get_text(strip=True) or state_name
        else:
            agency_elem = listing.find(['span', 'div'], class_=['agency', 'department', 'organization', 'buyer'])
            if agency_elem:
                agency = agency_elem.get_text(strip=True) or state_name
        
        return self.standardize_contract(
            state=state_code,
            title=title,
            solicitation_number=sol_number,
            due_date=due_date,
            link=link,
            agency=agency
        )
