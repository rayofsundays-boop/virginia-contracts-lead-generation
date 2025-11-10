"""
Industry Days & Events Scraper
Extracts government industry days, networking events, and procurement opportunities
Supports all 50 states and major cities
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import time
import re
import json

class IndustryDaysEventsScraper:
    """
    Universal scraper for government industry days and events
    Covers federal, state, and local opportunities across all 50 states
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # State abbreviations
        self.states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
        }
        
        # Major cities by state
        self.major_cities = {
            'VA': ['Richmond', 'Virginia Beach', 'Norfolk', 'Chesapeake', 'Newport News', 
                   'Hampton', 'Alexandria', 'Arlington', 'Roanoke', 'Portsmouth', 'Suffolk'],
            'CA': ['Los Angeles', 'San Diego', 'San Jose', 'San Francisco', 'Fresno', 'Sacramento'],
            'TX': ['Houston', 'San Antonio', 'Dallas', 'Austin', 'Fort Worth', 'El Paso'],
            'NY': ['New York City', 'Buffalo', 'Rochester', 'Yonkers', 'Syracuse', 'Albany'],
            'FL': ['Jacksonville', 'Miami', 'Tampa', 'Orlando', 'St. Petersburg', 'Hialeah'],
            'IL': ['Chicago', 'Aurora', 'Rockford', 'Joliet', 'Naperville', 'Springfield'],
            'PA': ['Philadelphia', 'Pittsburgh', 'Allentown', 'Erie', 'Reading', 'Scranton'],
            'OH': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo', 'Akron', 'Dayton'],
            'GA': ['Atlanta', 'Augusta', 'Columbus', 'Macon', 'Savannah', 'Athens'],
            'NC': ['Charlotte', 'Raleigh', 'Greensboro', 'Durham', 'Winston-Salem', 'Fayetteville'],
            'MI': ['Detroit', 'Grand Rapids', 'Warren', 'Sterling Heights', 'Ann Arbor', 'Lansing'],
            'AZ': ['Phoenix', 'Tucson', 'Mesa', 'Chandler', 'Scottsdale', 'Glendale'],
            'MA': ['Boston', 'Worcester', 'Springfield', 'Cambridge', 'Lowell', 'Brockton'],
            'TN': ['Nashville', 'Memphis', 'Knoxville', 'Chattanooga', 'Clarksville', 'Murfreesboro'],
            'WA': ['Seattle', 'Spokane', 'Tacoma', 'Vancouver', 'Bellevue', 'Kent'],
            'MD': ['Baltimore', 'Frederick', 'Rockville', 'Gaithersburg', 'Bowie', 'Annapolis'],
            'CO': ['Denver', 'Colorado Springs', 'Aurora', 'Fort Collins', 'Lakewood', 'Thornton'],
            # Add more as needed
        }
    
    def scrape_sam_gov_events(self, state_filter=None):
        """
        Scrape industry days from SAM.gov Interact platform
        https://sam.gov/content/opportunities
        """
        events = []
        
        try:
            # SAM.gov API endpoint for opportunities
            base_url = "https://sam.gov/api/prod/opportunities/v2/search"
            
            params = {
                "limit": 100,
                "postedFrom": (datetime.now() - timedelta(days=90)).strftime('%m/%d/%Y'),
                "postedTo": (datetime.now() + timedelta(days=365)).strftime('%m/%d/%Y'),
                "opportunityType": "s",  # Special notices (includes industry days)
                "ptype": "p"  # Procurement type
            }
            
            if state_filter:
                params['state'] = state_filter
            
            response = self.session.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                for opp in data.get('opportunities', []):
                    # Check if it's an industry day or event
                    title = opp.get('title', '').lower()
                    description = opp.get('description', '').lower()
                    
                    event_keywords = ['industry day', 'networking event', 'vendor fair', 
                                     'matchmaking', 'meet the buyer', 'procurement event',
                                     'small business', 'outreach event']
                    
                    is_event = any(keyword in title or keyword in description 
                                  for keyword in event_keywords)
                    
                    if is_event:
                        events.append({
                            'title': opp.get('title'),
                            'description': opp.get('description', '')[:1000],
                            'agency': opp.get('departmentName', 'Federal Agency'),
                            'location': opp.get('placeOfPerformance', {}).get('cityName', 'Multiple Locations'),
                            'state': opp.get('placeOfPerformance', {}).get('state', state_filter or 'N/A'),
                            'date': opp.get('postedDate'),
                            'deadline': opp.get('responseDeadLine'),
                            'url': f"https://sam.gov/opp/{opp.get('noticeId')}/view",
                            'notice_id': opp.get('noticeId'),
                            'source': 'SAM.gov Industry Days',
                            'event_type': 'Industry Day'
                        })
            
            print(f"✅ Found {len(events)} industry days on SAM.gov")
            
        except Exception as e:
            print(f"❌ Error scraping SAM.gov: {e}")
        
        return events
    
    def scrape_virginia_events(self):
        """Scrape Virginia-specific procurement events"""
        events = []
        
        # Virginia eVA system
        try:
            urls = [
                "https://eva.virginia.gov/pages/eva-upcoming-events.html",
                "https://eva.virginia.gov/pages/eva-vendor-outreach.html"
            ]
            
            for url in urls:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find event listings
                    event_divs = soup.find_all(['div', 'article'], 
                                               class_=re.compile(r'event|calendar|listing', re.I))
                    
                    for event in event_divs[:20]:  # Limit to 20 events
                        title_elem = event.find(['h2', 'h3', 'h4', 'strong'])
                        if title_elem:
                            events.append({
                                'title': title_elem.get_text(strip=True),
                                'description': event.get_text(strip=True)[:500],
                                'agency': 'Virginia eVA',
                                'location': 'Virginia',
                                'state': 'VA',
                                'url': url,
                                'source': 'Virginia eVA Events',
                                'event_type': 'Procurement Event'
                            })
            
            print(f"✅ Found {len(events)} Virginia eVA events")
            
        except Exception as e:
            print(f"⚠️ Virginia eVA scraping: {e}")
        
        return events
    
    def scrape_sba_events(self, state_filter=None):
        """Scrape Small Business Administration events"""
        events = []
        
        try:
            # SBA Events Calendar API
            url = "https://www.sba.gov/events"
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                event_cards = soup.find_all(['div', 'article'], 
                                           class_=re.compile(r'event|card', re.I))
                
                for card in event_cards[:30]:
                    title_elem = card.find(['h2', 'h3', 'a'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        # Extract location
                        location_text = card.get_text()
                        location = 'Online'
                        state_match = re.search(r'\b(' + '|'.join(self.states.values()) + r')\b', 
                                               location_text, re.I)
                        if state_match:
                            location = state_match.group(1)
                            state_abbr = [k for k, v in self.states.items() 
                                         if v.lower() == location.lower()]
                            state = state_abbr[0] if state_abbr else 'N/A'
                        else:
                            state = 'N/A'
                        
                        # Apply state filter
                        if state_filter and state != state_filter:
                            continue
                        
                        link = card.find('a', href=True)
                        event_url = urljoin(url, link['href']) if link else url
                        
                        events.append({
                            'title': title,
                            'description': card.get_text(strip=True)[:500],
                            'agency': 'U.S. Small Business Administration',
                            'location': location,
                            'state': state,
                            'url': event_url,
                            'source': 'SBA Events Calendar',
                            'event_type': 'Small Business Event'
                        })
                
                print(f"✅ Found {len(events)} SBA events")
                
        except Exception as e:
            print(f"⚠️ SBA scraping: {e}")
        
        return events
    
    def scrape_state_procurement_events(self, state_code):
        """
        Scrape state-specific procurement portals
        Template for expanding to all 50 states
        """
        events = []
        state_name = self.states.get(state_code, state_code)
        
        # State procurement portal URLs (expandable)
        state_portals = {
            'VA': 'https://eva.virginia.gov',
            'MD': 'https://emma.maryland.gov',
            'TX': 'https://www.txsmartbuy.com',
            'CA': 'https://www.caleprocure.ca.gov',
            'NY': 'https://online.ogs.ny.gov',
            'FL': 'https://www.myflorida.com/apps/vbs',
            'PA': 'https://www.emarketplace.state.pa.us',
            'OH': 'https://procure.ohio.gov',
            'NC': 'https://www.ips.state.nc.us',
            'GA': 'https://ssl.doas.state.ga.us',
            # Add more states...
        }
        
        portal_url = state_portals.get(state_code)
        
        if portal_url:
            try:
                # Try to find events page
                event_paths = ['/events', '/calendar', '/outreach', '/vendors', '/opportunities']
                
                for path in event_paths:
                    try:
                        response = self.session.get(portal_url + path, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Generic event extraction
                            event_elements = soup.find_all(['div', 'article', 'li'], 
                                                          class_=re.compile(r'event|calendar|listing', re.I))
                            
                            for elem in event_elements[:15]:
                                title_elem = elem.find(['h2', 'h3', 'h4', 'strong', 'a'])
                                if title_elem and len(title_elem.get_text(strip=True)) > 10:
                                    events.append({
                                        'title': title_elem.get_text(strip=True),
                                        'description': elem.get_text(strip=True)[:500],
                                        'agency': f'{state_name} State Procurement',
                                        'location': state_name,
                                        'state': state_code,
                                        'url': portal_url + path,
                                        'source': f'{state_name} Procurement Portal',
                                        'event_type': 'State Procurement Event'
                                    })
                            
                            if events:
                                break  # Found events, stop trying other paths
                                
                    except Exception:
                        continue
                
                if events:
                    print(f"✅ Found {len(events)} {state_name} procurement events")
                
            except Exception as e:
                print(f"⚠️ {state_name} scraping: {e}")
        
        return events
    
    def scrape_all_states(self, limit_per_state=5):
        """Scrape events from all 50 states"""
        all_events = []
        
        print(f"\n🚀 Starting 50-state event scraper...")
        
        for state_code, state_name in self.states.items():
            print(f"\n📍 Scraping {state_name} ({state_code})...")
            
            # Try multiple sources
            events = []
            
            # 1. SAM.gov federal events in this state
            events.extend(self.scrape_sam_gov_events(state_code))
            
            # 2. SBA events in this state
            events.extend(self.scrape_sba_events(state_code))
            
            # 3. State procurement portal
            events.extend(self.scrape_state_procurement_events(state_code))
            
            # Limit per state to avoid overwhelming database
            events = events[:limit_per_state]
            
            all_events.extend(events)
            
            print(f"   ✅ {len(events)} events found in {state_name}")
            
            # Be respectful - delay between states
            time.sleep(2)
        
        print(f"\n✅ Total events scraped: {len(all_events)} across {len(self.states)} states")
        
        return all_events
    
    def save_to_database(self, events, db_session):
        """Save scraped events to database"""
        from sqlalchemy import text
        
        saved_count = 0
        
        for event in events:
            try:
                # Check for duplicates
                existing = db_session.execute(text('''
                    SELECT id FROM government_contracts 
                    WHERE url = :url OR (title = :title AND agency = :agency)
                '''), {
                    'url': event.get('url', ''),
                    'title': event['title'],
                    'agency': event.get('agency', 'Unknown')
                }).fetchone()
                
                if existing:
                    continue
                
                # Insert event
                db_session.execute(text('''
                    INSERT INTO government_contracts 
                    (title, agency, location, url, description, posted_date, deadline, 
                     contract_type, naics_code, data_source, notice_id, state)
                    VALUES 
                    (:title, :agency, :location, :url, :description, :posted_date, :deadline,
                     :contract_type, :naics_code, :data_source, :notice_id, :state)
                '''), {
                    'title': event['title'],
                    'agency': event.get('agency', 'Government Agency'),
                    'location': event.get('location', 'N/A'),
                    'url': event.get('url', ''),
                    'description': event.get('description', ''),
                    'posted_date': event.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'deadline': event.get('deadline'),
                    'contract_type': event.get('event_type', 'Industry Day'),
                    'naics_code': '561720',
                    'data_source': event.get('source', 'Industry Days Scraper'),
                    'notice_id': event.get('notice_id'),
                    'state': event.get('state', 'N/A')
                })
                
                saved_count += 1
                print(f"✅ Saved: {event['title'][:60]}")
                
            except Exception as e:
                print(f"❌ Error saving {event['title'][:50]}: {e}")
                continue
        
        db_session.commit()
        return saved_count


# CLI usage
if __name__ == "__main__":
    scraper = IndustryDaysEventsScraper()
    
    print("=" * 70)
    print("INDUSTRY DAYS & EVENTS SCRAPER - ALL 50 STATES")
    print("=" * 70)
    
    # Option 1: Scrape specific state
    state_code = "VA"  # Change this to test other states
    print(f"\n📍 Scraping {scraper.states[state_code]} events...")
    events = scraper.scrape_state_procurement_events(state_code)
    events.extend(scraper.scrape_sba_events(state_code))
    
    print(f"\n✅ Found {len(events)} events in {scraper.states[state_code]}")
    
    # Option 2: Scrape all 50 states (uncomment to use)
    # all_events = scraper.scrape_all_states(limit_per_state=3)
    # print(f"\n📊 Total: {len(all_events)} events across all states")
