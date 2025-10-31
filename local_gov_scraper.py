"""
Local Virginia Government Website Scraper
Fetches real cleaning contract opportunities from city/county procurement pages
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VirginiaLocalGovScraper:
    """Scrape cleaning contracts from Virginia local government websites"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Virginia cities and their procurement URLs
        self.government_sites = {
            'Hampton': {
                # Use the canonical bids.aspx listing page to avoid 404s on detail links
                'url': 'https://www.hampton.gov/bids.aspx',
                'name': 'City of Hampton',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'Norfolk': {
                # Update to the standard bids listing page (previous URL returned 404)
                'url': 'https://www.norfolk.gov/bids.aspx',
                'name': 'City of Norfolk',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'Virginia Beach': {
                'url': 'https://www.vbgov.com/departments/procurement',
                'name': 'City of Virginia Beach',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'Newport News': {
                'url': 'https://www.nngov.com/procurement',
                'name': 'City of Newport News',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'Chesapeake': {
                'url': 'https://www.cityofchesapeake.net/procurement',
                'name': 'City of Chesapeake',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'Portsmouth': {
                'url': 'https://www.portsmouthva.gov/procurement',
                'name': 'City of Portsmouth',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'Suffolk': {
                'url': 'https://www.suffolkva.us/departments/procurement',
                'name': 'City of Suffolk',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'Williamsburg': {
                'url': 'https://www.williamsburgva.gov/procurement',
                'name': 'City of Williamsburg',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'James City County': {
                'url': 'https://www.jamescitycountyva.gov/procurement',
                'name': 'James City County',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            },
            'York County': {
                'url': 'https://www.yorkcounty.gov/procurement',
                'name': 'York County',
                'keywords': ['cleaning', 'janitorial', 'custodial', 'maintenance', 'facility']
            }
        }
    
    def fetch_all_local_contracts(self):
        """Fetch contracts from all Virginia local government websites"""
        all_contracts = []
        
        for city, info in self.government_sites.items():
            logger.info(f"Fetching contracts from {city}...")
            try:
                contracts = self._scrape_city_contracts(city, info)
                all_contracts.extend(contracts)
                logger.info(f"✅ Found {len(contracts)} contracts in {city}")
            except Exception as e:
                logger.error(f"❌ Error scraping {city}: {e}")
                continue
        
        logger.info(f"✅ Total contracts found: {len(all_contracts)}")
        return all_contracts
    
    def _scrape_city_contracts(self, city, info):
        """Scrape a single city's procurement website"""
        contracts = []
        
        try:
            response = requests.get(info['url'], headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for contract listings (common patterns in government sites)
            contract_elements = self._find_contract_elements(soup)
            
            for element in contract_elements:
                contract = self._parse_contract_element(element, city, info)
                if contract and self._is_cleaning_related(contract, info['keywords']):
                    contracts.append(contract)
            
        except Exception as e:
            logger.error(f"Error scraping {city}: {e}")
        
        return contracts
    
    def _find_contract_elements(self, soup):
        """Find contract listing elements using common patterns"""
        elements = []
        
        # Pattern 1: Tables with bid/contract information
        tables = soup.find_all('table', class_=re.compile(r'(bid|contract|procurement)', re.I))
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            elements.extend(rows)
        
        # Pattern 2: Divs with contract/bid classes
        divs = soup.find_all('div', class_=re.compile(r'(bid|contract|procurement|opportunity)', re.I))
        elements.extend(divs)
        
        # Pattern 3: List items
        lists = soup.find_all(['ul', 'ol'], class_=re.compile(r'(bid|contract|procurement)', re.I))
        for list_elem in lists:
            items = list_elem.find_all('li')
            elements.extend(items)
        
        # Pattern 4: Article tags
        articles = soup.find_all('article', class_=re.compile(r'(bid|contract|procurement)', re.I))
        elements.extend(articles)
        
        return elements
    
    def _parse_contract_element(self, element, city, info):
        """Extract contract information from HTML element"""
        try:
            # Extract text content
            text = element.get_text(strip=True)
            
            # Try to find title
            title = self._extract_title(element, text)
            if not title:
                return None
            
            # Extract deadline
            deadline = self._extract_deadline(element, text)
            
            # Extract description
            description = self._extract_description(element, text)
            
            # Extract value if available
            value = self._extract_value(element, text)
            
            # Find link to full details
            link = self._extract_link(element, info['url'])
            
            return {
                'title': title[:200],
                'agency': info['name'],
                'location': f"{city}, VA",
                'value': value,
                'deadline': deadline,
                'description': description[:500],
                'naics_code': '561720',  # Janitorial Services
                'website_url': link
            }
            
        except Exception as e:
            logger.error(f"Error parsing element: {e}")
            return None
    
    def _extract_title(self, element, text):
        """Extract contract title"""
        # Try to find in heading tags
        heading = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if heading:
            return heading.get_text(strip=True)
        
        # Try to find in strong/bold tags
        strong = element.find(['strong', 'b'])
        if strong:
            title = strong.get_text(strip=True)
            if len(title) > 10:  # Reasonable title length
                return title
        
        # Try to find in link text
        link = element.find('a')
        if link:
            title = link.get_text(strip=True)
            if len(title) > 10:
                return title
        
        # Fallback: First line of text
        lines = text.split('\n')
        if lines:
            return lines[0][:100]
        
        return None
    
    def _extract_deadline(self, element, text):
        """Extract deadline date"""
        # Common deadline patterns
        date_patterns = [
            r'deadline[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'due[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'closes?[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        text_lower = text.lower()
        for pattern in date_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse the date
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            return date_obj.strftime('%Y-%m-%d')
                        except:
                            continue
                except:
                    pass
        
        # Default to 30 days from now if no deadline found
        return (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    def _extract_description(self, element, text):
        """Extract contract description"""
        # Try to find description in paragraph tags
        paragraphs = element.find_all('p')
        if paragraphs:
            desc = ' '.join([p.get_text(strip=True) for p in paragraphs[:2]])
            if len(desc) > 50:
                return desc
        
        # Fallback to full text, skip first line (title)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) > 1:
            return ' '.join(lines[1:3])
        
        return f"Government cleaning and facility maintenance services contract for {element.get_text(strip=True)[:100]}"
    
    def _extract_value(self, element, text):
        """Extract contract value"""
        # Look for dollar amounts
        dollar_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'value[:\s]+\$?([\d,]+)',
            r'amount[:\s]+\$?([\d,]+)',
        ]
        
        for pattern in dollar_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Default estimate
        return "$50,000 - $500,000"
    
    def _extract_link(self, element, base_url):
        """Extract link to full contract details"""
        link = element.find('a')
        if link and link.get('href'):
            href = link.get('href')
            # Build robust absolute URL using urljoin to avoid duplicating path segments
            # Ensure base_url ends with a slash for correct resolution of sibling paths
            normalized_base = base_url if base_url.endswith('/') else base_url + '/'
            return urljoin(normalized_base, href)
        
        return base_url
    
    def _is_cleaning_related(self, contract, keywords):
        """Check if contract is related to cleaning services"""
        title = contract.get('title', '').lower()
        description = contract.get('description', '').lower()
        
        combined_text = f"{title} {description}"
        
        # Check if any cleaning-related keyword is present
        for keyword in keywords:
            if keyword in combined_text:
                return True
        
        return False


if __name__ == '__main__':
    # Test the scraper
    scraper = VirginiaLocalGovScraper()
    contracts = scraper.fetch_all_local_contracts()
    
    print(f"\n✅ Found {len(contracts)} local government contracts\n")
    
    for i, contract in enumerate(contracts[:5], 1):
        print(f"{i}. {contract['title']}")
        print(f"   Agency: {contract['agency']}")
        print(f"   Location: {contract['location']}")
        print(f"   Value: {contract['value']}")
        print(f"   Deadline: {contract['deadline']}")
        print(f"   URL: {contract['website_url']}\n")
