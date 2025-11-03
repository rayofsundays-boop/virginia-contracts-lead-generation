"""
Data.gov Bulk Data Integration for Federal Contracts
Downloads and processes bulk contract data from Data.gov and USAspending.gov
"""
import requests
import os
import csv
import json
import zipfile
import io
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataGovBulkFetcher:
    """Fetch federal contract data from Data.gov bulk files"""
    
    def __init__(self):
        # USAspending.gov bulk download API
        self.usaspending_url = 'https://api.usaspending.gov/api/v2/bulk_download/awards/'
        
        # Federal Procurement Data System (FPDS) data
        self.fpds_url = 'https://www.fpds.gov/ezsearch/FEEDS/ATOM'
        
        # Data.gov catalog API
        self.datagov_api = 'https://catalog.data.gov/api/3/action/package_search'
        
        # Cleaning-related NAICS codes
        self.naics_codes = [
            '561720',  # Janitorial Services
            '561730',  # Landscaping Services
            '561790',  # Other Services to Buildings and Dwellings
        ]
        
        # Virginia state codes
        self.va_state_codes = ['VA', 'Virginia']
    
    def fetch_usaspending_contracts(self, days_back=90):
        """
        Fetch contracts from USAspending.gov bulk download API
        
        Args:
            days_back: How many days back to search (default 90 for bulk data)
        
        Returns:
            List of contract dictionaries ready for database insertion
        """
        logger.info("📦 Fetching bulk contract data from USAspending.gov...")
        
        contracts = []
        
        try:
            # Calculate date range (search longer period for bulk data)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Use the award search API instead of bulk download for smaller datasets
            search_url = 'https://api.usaspending.gov/api/v2/search/spending_by_award/'
            
            payload = {
                "filters": {
                    "award_type_codes": ["A", "B", "C", "D"],  # IDV, Contract, Delivery Order, etc.
                    "place_of_performance_scope": "domestic",
                    "place_of_performance_locations": [{"state": "VA", "country": "USA"}],
                    "time_period": [
                        {
                            "start_date": start_date.strftime('%Y-%m-%d'),
                            "end_date": end_date.strftime('%Y-%m-%d'),
                            "date_type": "action_date"
                        }
                    ]
                },
                "fields": [
                    "Award ID", "Recipient Name", "Award Amount",
                    "Description", "Awarding Agency", "Awarding Sub Agency",
                    "Award Type", "Period of Performance Start Date",
                    "Period of Performance Current End Date", "Place of Performance City",
                    "Place of Performance State", "NAICS Code", "NAICS Description"
                ],
                "limit": 100,  # Max allowed by API
                "page": 1,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            logger.info(f"🔍 Requesting contracts from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Request award data
            response = requests.post(
                search_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                awards = result.get('results', [])
                
                logger.info(f"📥 Received {len(awards)} awards from USAspending.gov")
                
                # Debug: Log NAICS codes and descriptions
                for i, award in enumerate(awards[:5]):  # Check first 5 in detail
                    naics = award.get('NAICS Code')
                    naics_desc = award.get('NAICS Description')
                    agency = award.get('Awarding Agency', 'N/A')
                    amount = award.get('Award Amount', 0)
                    logger.info(f"Sample {i+1}: NAICS={naics}, Desc={naics_desc}, Agency={agency}, Amount=${amount:,.0f}" if isinstance(amount, (int, float)) else f"Sample {i+1}: NAICS={naics}, Agency={agency}")
                
                # Parse each award into our contract format
                # For bulk data, be more lenient - include contracts even without NAICS
                cleaning_contracts = []
                service_contracts = []
                all_contracts = []
                
                for award in awards:
                    naics = str(award.get('NAICS Code', ''))
                    naics_desc = str(award.get('NAICS Description', '')).lower()
                    
                    contract = self._parse_usaspending_award(award)
                    if not contract:
                        continue
                    
                    # Prioritize cleaning-related by NAICS code
                    if naics and any(naics.startswith(code) for code in self.naics_codes):
                        cleaning_contracts.append(contract)
                    # Or by description keywords
                    elif any(keyword in naics_desc for keyword in ['janitor', 'cleaning', 'custodial', 'landscaping', 'grounds']):
                        cleaning_contracts.append(contract)
                    # Include other service contracts (56xxxx)
                    elif naics.startswith('56'):
                        service_contracts.append(contract)
                    # Include all VA contracts as fallback
                    else:
                        all_contracts.append(contract)
                
                # Combine: prioritize cleaning, then services, then general
                contracts = cleaning_contracts + service_contracts[:30] + all_contracts[:50]
                            
                logger.info(f"✅ Filtered to {len(contracts)} service-related contracts (prioritizing cleaning)")
            else:
                logger.error(f"❌ Error from USAspending.gov: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching USAspending.gov data: {e}")
        
        logger.info(f"✅ Fetched {len(contracts)} contracts from bulk data")
        return contracts
    
    def fetch_fpds_atom_feed(self, days_back=7):
        """
        Fetch contracts from FPDS ATOM feed
        
        Args:
            days_back: How many days back to search (default 7)
        
        Returns:
            List of contract dictionaries
        """
        logger.info("📡 Fetching FPDS ATOM feed...")
        
        contracts = []
        
        try:
            # FPDS allows date-based queries
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            end_date = datetime.now().strftime('%Y/%m/%d')
            
            # Build FPDS query URL
            params = {
                'POSTING_DATE': f'[{start_date},{end_date}]',
                'PRINCIPAL_PLACE_STATE': 'VIRGINIA',
                'NAICS': ','.join(self.naics_codes),
                's': 'FPDS',
                'templateName': 'defaultFPDS'
            }
            
            response = requests.get(self.fpds_url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Parse ATOM/XML feed
                contracts = self._parse_atom_feed(response.content)
            else:
                logger.error(f"❌ Error from FPDS: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching FPDS data: {e}")
        
        return contracts
    
    def search_datagov_datasets(self, query="federal contracts virginia cleaning"):
        """
        Search Data.gov catalog for relevant datasets
        
        Args:
            query: Search query string
        
        Returns:
            List of dataset URLs
        """
        logger.info(f"🔍 Searching Data.gov catalog for: {query}")
        
        datasets = []
        
        try:
            params = {
                'q': query,
                'rows': 10,
                'sort': 'metadata_modified desc'
            }
            
            response = requests.get(self.datagov_api, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('result', {}).get('results', [])
                
                for dataset in results:
                    datasets.append({
                        'title': dataset.get('title'),
                        'url': dataset.get('url'),
                        'resources': dataset.get('resources', [])
                    })
                    
                logger.info(f"✅ Found {len(datasets)} datasets on Data.gov")
            else:
                logger.error(f"❌ Error from Data.gov: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error searching Data.gov: {e}")
        
        return datasets
    
    def _download_and_parse_csv(self, url):
        """Download and parse CSV file from URL"""
        contracts = []
        
        try:
            logger.info(f"📥 Downloading: {url[:100]}...")
            response = requests.get(url, timeout=120)
            
            if response.status_code == 200:
                # Handle potential zip files
                if url.endswith('.zip'):
                    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                    csv_filename = zip_file.namelist()[0]
                    csv_content = zip_file.read(csv_filename).decode('utf-8')
                else:
                    csv_content = response.text
                
                # Parse CSV
                reader = csv.DictReader(io.StringIO(csv_content))
                
                for row in reader:
                    contract = self._parse_usaspending_row(row)
                    if contract:
                        contracts.append(contract)
                        
                logger.info(f"✅ Parsed {len(contracts)} contracts from CSV")
            else:
                logger.error(f"❌ Error downloading file: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error parsing CSV: {e}")
        
        return contracts
    
    def _parse_usaspending_row(self, row):
        """Parse a row from USAspending.gov CSV into our contract format"""
        try:
            # Extract relevant fields (field names may vary)
            title = row.get('Award Description') or row.get('award_description', 'Federal Contract')
            agency = row.get('Awarding Agency Name') or row.get('awarding_agency_name', 'Federal Agency')
            department = row.get('Awarding Sub Agency Name') or row.get('awarding_sub_agency_name', '')
            
            # Location
            city = row.get('Place of Performance City Name') or row.get('pop_city_name', '')
            state = row.get('Place of Performance State Code') or row.get('pop_state_code', 'VA')
            location = f"{city}, {state}" if city else state
            
            # Value
            value_str = row.get('Award Amount') or row.get('total_obligation', '$0')
            if isinstance(value_str, (int, float)):
                value = f"${value_str:,.0f}"
            else:
                value = value_str
            
            # Dates
            deadline = row.get('Period of Performance End Date') or row.get('period_of_performance_end_date', '')
            posted_date = row.get('Action Date') or row.get('action_date', '')
            
            # Other fields
            naics_code = row.get('NAICS Code') or row.get('naics_code', '')
            notice_id = row.get('Award ID') or row.get('award_id', f"USA-{datetime.now().timestamp()}")
            set_aside = row.get('Type of Set Aside') or row.get('type_of_set_aside', 'Unrestricted')
            
            # SAM.gov URL (if available)
            sam_gov_url = f"https://sam.gov/opp/{notice_id}"
            
            return {
                'title': title[:200],  # Limit length
                'agency': agency[:200],
                'department': department[:200],
                'location': location[:100],
                'value': value[:50],
                'deadline': deadline,
                'description': f"{title}\n\nAgency: {agency}\nNAICS: {naics_code}",
                'naics_code': naics_code,
                'sam_gov_url': sam_gov_url,
                'notice_id': notice_id,
                'set_aside': set_aside[:100],
                'posted_date': posted_date
            }
        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            return None
    
    def _parse_usaspending_award(self, award):
        """Parse an award from USAspending.gov API into our contract format"""
        try:
            # Extract relevant fields from API response
            title = award.get('Description', 'Federal Contract')
            if not title or title == 'None':
                title = f"Contract from {award.get('Awarding Agency', 'Federal Agency')}"
            
            agency = award.get('Awarding Agency', 'Federal Agency')
            department = award.get('Awarding Sub Agency', '')
            
            # Location
            city = award.get('Place of Performance City', '')
            state = award.get('Place of Performance State', 'VA')
            location = f"{city}, {state}" if city else state
            
            # Value
            value_amount = award.get('Award Amount', 0)
            if isinstance(value_amount, (int, float)):
                value = f"${value_amount:,.0f}"
            else:
                value = str(value_amount)
            
            # Dates
            deadline = award.get('Period of Performance Current End Date', '')
            posted_date = award.get('Period of Performance Start Date', '')
            
            # Other fields
            naics_code = str(award.get('NAICS Code', ''))
            naics_desc = award.get('NAICS Description', '')
            award_id = award.get('Award ID', f"USA-{int(datetime.now().timestamp())}")
            award_type = award.get('Award Type', 'Unrestricted')
            recipient = award.get('Recipient Name', '')
            
            # Clean up award ID to make it URL-safe
            notice_id = str(award_id).replace(' ', '-').replace('/', '-')
            
            # SAM.gov URL
            sam_gov_url = f"https://www.usaspending.gov/award/{notice_id}"
            
            # Build description
            description = f"{title}\n\n"
            description += f"Agency: {agency}\n"
            if department:
                description += f"Department: {department}\n"
            if recipient:
                description += f"Recipient: {recipient}\n"
            description += f"NAICS: {naics_code} - {naics_desc}\n"
            description += f"Location: {location}"
            
            return {
                'title': title[:200],
                'agency': agency[:200],
                'department': department[:200],
                'location': location[:100],
                'value': value[:50],
                'deadline': deadline[:50] if deadline else '',
                'description': description[:1000],
                'naics_code': naics_code[:20],
                'sam_gov_url': sam_gov_url,
                'notice_id': notice_id[:100],
                'set_aside': award_type[:100],
                'posted_date': posted_date[:50] if posted_date else ''
            }
        except Exception as e:
            logger.error(f"Error parsing award: {e}")
            return None
    
    def _parse_atom_feed(self, xml_content):
        """Parse ATOM/XML feed from FPDS"""
        # This would require xml.etree or lxml
        # For now, return empty list - implement if needed
        logger.warning("⚠️  ATOM feed parsing not yet implemented")
        return []


if __name__ == '__main__':
    # Test the fetcher
    fetcher = DataGovBulkFetcher()
    
    # Try USAspending.gov bulk data
    contracts = fetcher.fetch_usaspending_contracts(days_back=30)
    print(f"\nFetched {len(contracts)} contracts from USAspending.gov")
    
    if contracts:
        print("\nSample contract:")
        print(json.dumps(contracts[0], indent=2))
    
    # Search Data.gov catalog
    datasets = fetcher.search_datagov_datasets()
    if datasets:
        print(f"\nFound {len(datasets)} datasets on Data.gov:")
        for ds in datasets[:3]:
            print(f"  - {ds['title']}")
