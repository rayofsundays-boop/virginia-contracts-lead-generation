"""
SAM.gov API Integration for Real Federal Contract Data
Fetches actual cleaning contracts from Virginia government agencies
"""
import requests
import os
from datetime import datetime, timedelta
import logging
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SAMgovFetcher:
    """Fetch real federal cleaning contracts from SAM.gov API"""
    
    def __init__(self):
        self.api_key = os.environ.get('SAM_GOV_API_KEY', '').strip()
        self.base_url = 'https://api.sam.gov/opportunities/v2/search'
        
        # Expanded cleaning-related NAICS codes for comprehensive coverage
        self.naics_codes = [
            '561720',  # Janitorial Services (PRIMARY)
            '561730',  # Landscaping Services
            '561790',  # Other Services to Buildings and Dwellings
            '562111',  # Solid Waste Collection (trash removal)
            '561710',  # Exterminating and Pest Control Services
            '561740',  # Carpet and Upholstery Cleaning Services
            '238990',  # All Other Specialty Trade Contractors (facility maintenance)
            '562910',  # Remediation Services (deep cleaning, mold removal)
        ]
    
    def fetch_with_throttle(self, urls, delay=2):
        """
        Generic throttled fetch function with 429 handling
        
        Args:
            urls: List of URLs to fetch
            delay: Delay between requests in seconds (default 2)
        
        Returns:
            List of response objects
        """
        responses = []
        for url in urls:
            try:
                response = requests.get(url)
                if response.status_code == 429:
                    logger.warning("Rate limit hit (429) — sleeping for 60s...")
                    time.sleep(60)
                    # Retry after waiting
                    response = requests.get(url)
                else:
                    logger.info(f"Fetched: {url[:100]}...")
                    responses.append(response)
                time.sleep(delay)  # 1–2 seconds between requests
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
        return responses
    
    def fetch_va_cleaning_contracts(self, days_back=90):
        """
        Fetch real cleaning contracts from Virginia
        
        Args:
            days_back: How many days back to search (default 90 - expanded for more coverage)
        
        Returns:
            List of contract dictionaries ready for database insertion
        """
        if not self.api_key:
            logger.error("SAM_GOV_API_KEY not set. Get free key from https://open.gsa.gov/api/sam-gov-entity-api/")
            return []
        
        all_contracts = []
        
        # Search for each NAICS code
        for idx, naics in enumerate(self.naics_codes):
            logger.info(f"Fetching contracts for NAICS {naics}...")
            contracts = self._search_contracts(naics, days_back)
            all_contracts.extend(contracts)
            # Stagger requests to minimize rate limiting
            if idx < len(self.naics_codes) - 1:
                sleep_s = 1.5 + random.random() * 1.5
                logger.info(f"Sleeping {sleep_s:.1f}s to avoid rate limits...")
                time.sleep(sleep_s)
        
        logger.info(f"✅ Fetched {len(all_contracts)} real contracts from SAM.gov")
        return all_contracts
    
    def _search_contracts(self, naics_code, days_back):
        """Search SAM.gov for contracts with specific NAICS code with pagination"""
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'VA-Contracts-Fetcher/1.0 (+https://example.com)'
        }

        limit = 100
        offset = 0
        # Lower default max pages to reduce rate limit pressure; can be overridden via env
        max_pages = int(os.environ.get('SAM_MAX_PAGES_PER_NAICS', 2))
        all_items = []

        try:
            for page_idx in range(max_pages):
                # Build date window as YYYY-MM-DD strings (SAM.gov expects dates, not offsets)
                now = datetime.utcnow().date()
                from_date = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
                to_date = now.strftime('%Y-%m-%d')
                params = {
                    'api_key': self.api_key,
                    'postedFrom': from_date,
                    'postedTo': to_date,
                    # Prefer explicit notice types commonly used for open opportunities
                    'noticeType': 'PRESOLICITATION,SOURCES_SOUGHT,SOLICITATION,COMBINED_SYNOPSIS_SOLICITATION',
                    # Legacy/alternate param some integrations used; harmless if ignored
                    'ptype': 'o,s',
                    'ncode': naics_code,
                    'placeOfPerformanceState': 'VA',  # Virginia only
                    # Try fully-qualified filter key as well (API accepts dotted keys)
                    'placeOfPerformance.state': 'VA',
                    'limit': limit,
                    'offset': offset
                }

                response = self._request_with_retries(self.base_url, params=params, headers=headers)
                if response is None:
                    break

                data = response.json()
                opportunities = data.get('opportunitiesData', []) or []
                all_items.extend(opportunities)

                # Determine if there's another page
                total_records = data.get('totalRecords') or data.get('totalrecords') or data.get('total')
                if total_records is not None:
                    total_records = int(total_records)
                    if offset + limit >= total_records:
                        break

                # If fewer than limit returned, likely last page
                if len(opportunities) < limit:
                    break

                # Move to next page with a small jitter to avoid rate limits
                offset += limit
                sleep_s = 0.8 + random.random() * 1.2
                logger.info(f"Fetched page {page_idx+1} for NAICS {naics_code} (items: {len(opportunities)}). Sleeping {sleep_s:.1f}s before next page...")
                time.sleep(sleep_s)

            return [self._parse_opportunity(opp) for opp in all_items]

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from SAM.gov: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing SAM.gov response: {e}")
            return []

    def _request_with_retries(self, url, params, headers, max_retries=5, base_delay=2.0):
        """HTTP GET with exponential backoff and jitter for 429/5xx"""
        attempt = 0
        while attempt <= max_retries:
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=30)
                
                # Check for API key errors (403 or specific error messages)
                if resp.status_code == 403:
                    try:
                        error_data = resp.json()
                        error_msg = error_data.get('error', {}).get('message', '')
                        if 'API_KEY_INVALID' in error_msg or 'invalid API key' in error_msg.lower():
                            logger.error(f"❌ INVALID SAM.gov API KEY: {error_msg}")
                            logger.error(f"   Current key starts with: {params.get('api_key', '')[:20]}...")
                            logger.error(f"   Get a valid key from: https://open.gsa.gov/api/sam-gov-entity-api/")
                            return None
                    except:
                        pass
                    logger.error(f"SAM.gov access denied (403). Check API key validity.")
                    return None
                
                # Handle rate limiting
                if resp.status_code == 429:
                    retry_after = resp.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            delay = base_delay * (2 ** attempt) + random.random()
                    else:
                        delay = base_delay * (2 ** attempt) + random.random()
                    
                    # Cap wait time at 60 seconds maximum
                    delay = min(delay, 60)
                    
                    logger.warning(f"SAM.gov rate limit hit (429). Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    attempt += 1
                    continue

                # Retry on 5xx
                if 500 <= resp.status_code < 600:
                    delay = base_delay * (2 ** attempt) + random.random()
                    
                    # Cap wait time at 60 seconds maximum
                    delay = min(delay, 60)
                    
                    logger.warning(f"SAM.gov server error {resp.status_code}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    attempt += 1
                    continue

                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                delay = base_delay * (2 ** attempt) + random.random()
                logger.warning(f"Request error: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                attempt += 1

        logger.error("Exceeded maximum retries for SAM.gov request")
        return None
    
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
