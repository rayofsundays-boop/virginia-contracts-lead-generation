"""
SAM.gov API Integration for Real Federal Contract Data
Fetches actual cleaning contracts from Virginia government agencies
"""
import requests
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SAMgovFetcher:
    """Fetch real federal cleaning contracts from SAM.gov API"""
    
    def __init__(self):
        self.api_key = os.environ.get('SAM_GOV_API_KEY', '')
        self.base_url = 'https://api.sam.gov/opportunities/v2/search'
        
        # Cleaning-related NAICS codes
        self.naics_codes = [
            '561720',  # Janitorial Services
            '561730',  # Landscaping Services
            '561790',  # Other Services to Buildings and Dwellings
        ]
    
    def fetch_va_cleaning_contracts(self, days_back=30):
        """
        Fetch real cleaning contracts from Virginia
        
        Args:
            days_back: How many days back to search (default 30)
        
        Returns:
            List of contract dictionaries ready for database insertion
        """
        if not self.api_key:
            logger.error("SAM_GOV_API_KEY not set. Get free key from https://open.gsa.gov/api/sam-gov-entity-api/")
            return []
        
        all_contracts = []
        
        # Search for each NAICS code
        for naics in self.naics_codes:
            logger.info(f"Fetching contracts for NAICS {naics}...")
            contracts = self._search_contracts(naics, days_back)
            all_contracts.extend(contracts)
        
        logger.info(f"✅ Fetched {len(all_contracts)} real contracts from SAM.gov")
        return all_contracts
    
    def _search_contracts(self, naics_code, days_back):
        """Search SAM.gov for contracts with specific NAICS code"""
        params = {
            'api_key': self.api_key,
            'postedFrom': str(days_back),  # Last N days
            'postedTo': '0',
            'ptype': 'o,s',  # Opportunities and sources sought
            'ncode': naics_code,
            'placeOfPerformanceState': 'VA',  # Virginia only
            'limit': 100,
            'offset': 0
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            
            return [self._parse_opportunity(opp) for opp in opportunities]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from SAM.gov: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing SAM.gov response: {e}")
            return []
    
    def _parse_opportunity(self, opp):
        """Convert SAM.gov opportunity to our database format"""
        
        # Extract location
        pop = opp.get('placeOfPerformance', {})
        city = pop.get('city', {}).get('name', 'Virginia')
        state = pop.get('state', {}).get('code', 'VA')
        location = f"{city}, {state}"
        
        # Extract value
        value = self._extract_value(opp)
        
        # Extract deadline
        deadline = opp.get('responseDeadLine', '')
        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                deadline = deadline_dt.strftime('%Y-%m-%d')
            except:
                deadline = ''
        
        # Build SAM.gov URL
        notice_id = opp.get('noticeId', '')
        sam_gov_url = f"https://sam.gov/opp/{notice_id}" if notice_id else "https://sam.gov"
        
        # Extract set-aside type
        set_aside = opp.get('typeOfSetAside', 'Unrestricted')
        if set_aside == 'None':
            set_aside = 'Unrestricted'
        
        # Extract posted date
        posted_date = opp.get('postedDate', '')
        if posted_date:
            try:
                posted_dt = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
                posted_date = posted_dt.strftime('%Y-%m-%d')
            except:
                posted_date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'title': opp.get('title', 'Federal Cleaning Contract')[:200],
            'agency': opp.get('department', {}).get('name', 'Federal Agency')[:100],
            'department': opp.get('subTier', {}).get('name', '')[:100],
            'location': location,
            'value': value,
            'deadline': deadline or self._default_deadline(),
            'description': self._clean_description(opp.get('description', '')),
            'naics_code': str(opp.get('naics', [{}])[0].get('code', '561720')),
            'sam_gov_url': sam_gov_url,
            'notice_id': notice_id,
            'set_aside': set_aside,
            'posted_date': posted_date or datetime.now().strftime('%Y-%m-%d')
        }
    
    def _extract_value(self, opp):
        """Extract or estimate contract value"""
        # Try various value fields
        award_amount = opp.get('awardAmount')
        if award_amount:
            return f"${float(award_amount):,.0f}"
        
        # Check for estimated value in description
        description = opp.get('description', '').lower()
        
        # Look for dollar amounts
        import re
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        matches = re.findall(dollar_pattern, description)
        if matches:
            # Return the largest amount found
            amounts = [float(m.replace('$', '').replace(',', '')) for m in matches]
            if amounts:
                return f"${max(amounts):,.0f}"
        
        # Estimate based on contract type
        title_lower = opp.get('title', '').lower()
        if any(word in title_lower for word in ['hospital', 'medical center', 'va medical']):
            return "$2,000,000 - $5,000,000"
        elif any(word in title_lower for word in ['base', 'military', 'naval', 'fort']):
            return "$1,000,000 - $3,000,000"
        elif any(word in title_lower for word in ['building', 'facility', 'office']):
            return "$500,000 - $1,500,000"
        else:
            return "$250,000 - $1,000,000"
    
    def _clean_description(self, description):
        """Clean and truncate description"""
        if not description:
            return "Federal cleaning and facility maintenance services contract. See SAM.gov for full details."
        
        # Remove excessive whitespace
        description = ' '.join(description.split())
        
        # Truncate to 500 characters
        if len(description) > 500:
            description = description[:497] + "..."
        
        return description
    
    def _default_deadline(self):
        """Return default deadline (30 days from now)"""
        return (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')


if __name__ == '__main__':
    # Test the fetcher
    fetcher = SAMgovFetcher()
    contracts = fetcher.fetch_va_cleaning_contracts(days_back=90)
    
    print(f"\n✅ Found {len(contracts)} real contracts\n")
    
    for i, contract in enumerate(contracts[:5], 1):
        print(f"{i}. {contract['title']}")
        print(f"   Agency: {contract['agency']}")
        print(f"   Location: {contract['location']}")
        print(f"   Value: {contract['value']}")
        print(f"   Deadline: {contract['deadline']}")
        print(f"   URL: {contract['sam_gov_url']}\n")
