import requests
import os
from datetime import datetime, timedelta
import logging
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SAMgovFetcher:
    """Fetch real federal cleaning contracts from SAM.gov API with Data.gov fallback"""
    
    def __init__(self):
        self.api_key = os.environ.get('SAM_GOV_API_KEY', '').strip()
        self.base_url = 'https://api.sam.gov/opportunities/v2/search'
        self.retry_attempts = 0
        self.max_retries = 3
        
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
        
        # Default to all 50 US states for nationwide coverage (override with SAM_TARGET_STATES env as CSV)
        default_states = [
            'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
            'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
            'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
            'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
            'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
        ]
        env_states = os.environ.get('SAM_TARGET_STATES', '')
        if env_states.strip():
            self.target_states = [s.strip().upper() for s in env_states.split(',') if s.strip()]
        else:
            self.target_states = default_states
    
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
        Backward-compatible method for legacy callers. Now delegates to nationwide
        search but prioritizes DMV behavior when SAM_TARGET_STATES isn't set.
        """
        return self.fetch_us_cleaning_contracts(days_back=days_back)

    def fetch_us_cleaning_contracts(self, days_back=90, states=None):
        """
        Fetch real cleaning contracts across the United States.

        - Iterates states (env-configurable via SAM_TARGET_STATES)
        - Applies NAICS filtering for cleaning-related opportunities
        - Handles pagination with throttling and backoff
        - Falls back to Data.gov after repeated failures

        Args:
            days_back: Lookback window in days
            states: Optional list of state codes to search; defaults to configured target_states

        Returns:
            List[dict]: Contracts ready for DB insertion
        """
        if not self.api_key:
            logger.error("SAM_GOV_API_KEY not set. Get free key from https://open.gsa.gov/api/sam-gov-entity-api/")
            logger.info("🔄 Falling back to Data.gov...")
            return self._fallback_to_datagov(days_back)
        
        all_contracts = []
        seen_notice_ids = set()
        states_to_search = states or self.target_states
        # Allow limiting states per run to reduce rate limits if needed
        max_states = int(os.environ.get('SAM_MAX_STATES_PER_RUN', len(states_to_search)))
        states_to_search = states_to_search[:max_states]
        
        try:
            self.retry_attempts += 1
            
            # Search each state
            for state in states_to_search:
                logger.info(f"🔍 Searching {state} contracts...")
                
                # Search for each NAICS code in this state
                for idx, naics in enumerate(self.naics_codes):
                    logger.info(f"  NAICS {naics} in {state}...")
                    contracts = self._search_contracts(naics, days_back, state)
                    for c in contracts:
                        nid = c.get('notice_id')
                        if nid and nid in seen_notice_ids:
                            continue
                        if nid:
                            seen_notice_ids.add(nid)
                        all_contracts.append(c)
                    
                    # Stagger requests to minimize rate limiting
                    if idx < len(self.naics_codes) - 1 or state != states_to_search[-1]:
                        # Slightly higher sleep for nationwide runs
                        base = 1.5 if len(states_to_search) <= 3 else 2.5
                        jitter = 1.5 if len(states_to_search) <= 3 else 2.0
                        sleep_s = base + random.random() * jitter
                        logger.info(f"  Sleeping {sleep_s:.1f}s to avoid rate limits...")
                        time.sleep(sleep_s)
            
            if all_contracts:
                logger.info(f"✅ Fetched {len(all_contracts)} real contracts across {len(states_to_search)} state(s)")
                self.retry_attempts = 0  # Reset on success
                return all_contracts
            else:
                logger.warning(f"⚠️  No contracts found from SAM.gov (attempt {self.retry_attempts}/{self.max_retries})")
                if self.retry_attempts >= self.max_retries:
                    logger.info("🔄 Max retries reached. Falling back to Data.gov...")
                    return self._fallback_to_datagov(days_back)
                return []
                
        except Exception as e:
            logger.error(f"❌ SAM.gov API error (attempt {self.retry_attempts}/{self.max_retries}): {e}")
            if self.retry_attempts >= self.max_retries:
                logger.info("🔄 Max retries reached. Falling back to Data.gov...")
                return self._fallback_to_datagov(days_back)
            return []
    
    def _search_contracts(self, naics_code, days_back, state='VA'):
        """Search SAM.gov for contracts with specific NAICS code with pagination"""
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'DMV-Contracts-Fetcher/1.0 (+https://example.com)'
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
                    'placeOfPerformanceState': state,  # DMV region: VA, MD, or DC
                    # Try fully-qualified filter key as well (API accepts dotted keys)
                    'placeOfPerformance.state': state,
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
    
    def _fallback_to_datagov(self, days_back=90):
        """
        Fallback to Data.gov (USAspending.gov) when SAM.gov fails
        
        Args:
            days_back: How many days back to search
            
        Returns:
            List of contract dictionaries from Data.gov
        """
        logger.info("=" * 60)
        logger.info("🔄 FALLBACK ACTIVATED: Switching to Data.gov (USAspending.gov)")
        logger.info("=" * 60)
        
        try:
            # Import Data.gov fetcher
            from datagov_bulk_fetcher import DataGovBulkFetcher
            
            fetcher = DataGovBulkFetcher()
            logger.info(f"📦 Fetching DMV cleaning contracts from USAspending.gov...")
            logger.info(f"   States: VA, MD, DC")
            logger.info(f"   Lookback: {days_back} days")
            logger.info(f"   NAICS codes: 561720 (Janitorial), 561730 (Landscaping), etc.")
            
            contracts = fetcher.fetch_usaspending_contracts(days_back=days_back)
            
            if contracts:
                logger.info(f"✅ Data.gov fallback successful! Retrieved {len(contracts)} contracts")
                logger.info("💡 Tip: SAM.gov may have rate limits. Data.gov is more reliable for bulk fetching.")
                self.retry_attempts = 0  # Reset retry counter
                return contracts
            else:
                logger.warning("⚠️  No contracts found from Data.gov either")
                return []
                
        except ImportError as e:
            logger.error(f"❌ Cannot import Data.gov fetcher: {e}")
            logger.error("   Make sure datagov_bulk_fetcher.py exists in the same directory")
            return []
        except Exception as e:
            logger.error(f"❌ Data.gov fallback failed: {e}")
            return []
    
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
