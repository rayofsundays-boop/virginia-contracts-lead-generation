"""
Aviation Airline Scraper - Smart Approach
Targets airline career/pilot recruitment pages and facility information.
These pages are public, frequently updated, and contain base location data.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re

# ---------------------------------------
# AIRLINE CAREER & FACILITY PAGES
# ---------------------------------------

AIRLINE_TARGETS = {
    "Delta Airlines": {
        "careers_url": "https://careers.delta.com",
        "about_url": "https://www.delta.com/us/en/about-delta/corporate-information",
        "bases": ["ATL", "DTW", "MSP", "SLC", "SEA", "LAX", "JFK", "BOS"],
        "hubs": ["Atlanta", "Detroit", "Minneapolis", "Salt Lake City", "Seattle", "Los Angeles", "New York", "Boston"]
    },
    "American Airlines": {
        "careers_url": "https://aa.com/careers",
        "about_url": "https://www.aa.com/i18n/customer-service/about-us/about-us.jsp",
        "bases": ["DFW", "CLT", "PHX", "MIA", "ORD", "LAX", "DCA", "JFK"],
        "hubs": ["Dallas", "Charlotte", "Phoenix", "Miami", "Chicago", "Los Angeles", "Washington DC", "New York"]
    },
    "United Airlines": {
        "careers_url": "https://careers.united.com",
        "about_url": "https://www.united.com/ual/en/us/fly/company.html",
        "bases": ["EWR", "ORD", "IAH", "DEN", "SFO", "LAX", "IAD"],
        "hubs": ["Newark", "Chicago", "Houston", "Denver", "San Francisco", "Los Angeles", "Washington Dulles"]
    },
    "Southwest Airlines": {
        "careers_url": "https://careers.southwestair.com",
        "about_url": "https://www.southwest.com/html/about-southwest/index.html",
        "bases": ["DAL", "MDW", "PHX", "LAS", "DEN", "BWI", "OAK"],
        "hubs": ["Dallas", "Chicago Midway", "Phoenix", "Las Vegas", "Denver", "Baltimore", "Oakland"]
    },
    "JetBlue Airways": {
        "careers_url": "https://careers.jetblue.com",
        "about_url": "https://www.jetblue.com/about-us",
        "bases": ["JFK", "BOS", "FLL", "LAX", "MCO"],
        "hubs": ["New York JFK", "Boston", "Fort Lauderdale", "Los Angeles", "Orlando"]
    },
    "Spirit Airlines": {
        "careers_url": "https://careers.spirit.com",
        "about_url": "https://www.spirit.com/about-us",
        "bases": ["FLL", "DTW", "ORD", "LAS", "DFW"],
        "hubs": ["Fort Lauderdale", "Detroit", "Chicago", "Las Vegas", "Dallas"]
    },
    "Frontier Airlines": {
        "careers_url": "https://careers.flyfrontier.com",
        "about_url": "https://www.flyfrontier.com/about-us/",
        "bases": ["DEN", "LAS", "MIA", "ORD", "PHX"],
        "hubs": ["Denver", "Las Vegas", "Miami", "Chicago", "Phoenix"]
    },
    "Alaska Airlines": {
        "careers_url": "https://careers.alaskaair.com",
        "about_url": "https://www.alaskaair.com/content/about-us",
        "bases": ["SEA", "PDX", "ANC", "SFO", "LAX"],
        "hubs": ["Seattle", "Portland", "Anchorage", "San Francisco", "Los Angeles"]
    }
}

# ---------------------------------------
# SCRAPING FUNCTIONS
# ---------------------------------------

def scrape_airline_page(url, airline_name):
    """
    Scrape airline page for facility/contact information.
    Looks for: locations, phone numbers, emails, facility info
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        print(f"  📄 Scraping: {airline_name} - {url[:50]}...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"    ⚠️ HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all text
        page_text = soup.get_text(" ", strip=True)
        
        # Extract contact information
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_text)
        
        # Look for facility-related keywords
        facility_keywords = ['maintenance', 'hangar', 'base', 'facility', 'operations center', 
                           'hub', 'station', 'crew base', 'training center']
        
        facilities_found = []
        for keyword in facility_keywords:
            if keyword.lower() in page_text.lower():
                facilities_found.append(keyword)
        
        # Look for cleaning-related mentions
        cleaning_keywords = ['cleaning', 'janitorial', 'custodial', 'sanitation', 'facility services']
        cleaning_mentions = [k for k in cleaning_keywords if k.lower() in page_text.lower()]
        
        return {
            "emails": list(set(emails))[:5],  # First 5 unique emails
            "phones": list(set(phones))[:5],  # First 5 unique phones
            "facilities_mentioned": facilities_found,
            "cleaning_mentions": cleaning_mentions,
            "page_title": soup.title.string if soup.title else airline_name,
            "page_url": url
        }
        
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:60]}")
        return None


def scrape_airline_complete(airline_name, airline_info):
    """
    Scrape all information for one airline.
    Creates opportunities for each hub/base.
    """
    print(f"\n✈️ Processing: {airline_name}")
    
    opportunities = []
    
    # Scrape careers page
    careers_data = scrape_airline_page(airline_info['careers_url'], airline_name)
    time.sleep(2)
    
    # Scrape about page
    about_data = scrape_airline_page(airline_info['about_url'], airline_name)
    time.sleep(2)
    
    # Combine data
    all_emails = []
    all_phones = []
    all_facilities = []
    
    if careers_data:
        all_emails.extend(careers_data.get('emails', []))
        all_phones.extend(careers_data.get('phones', []))
        all_facilities.extend(careers_data.get('facilities_mentioned', []))
    
    if about_data:
        all_emails.extend(about_data.get('emails', []))
        all_phones.extend(about_data.get('phones', []))
        all_facilities.extend(about_data.get('facilities_mentioned', []))
    
    # Remove duplicates
    all_emails = list(set(all_emails))
    all_phones = list(set(all_phones))
    all_facilities = list(set(all_facilities))
    
    # Create opportunity for each hub/base
    for hub, base_code in zip(airline_info['hubs'], airline_info['bases']):
        
        # Determine state from hub city
        state_map = {
            "Atlanta": "GA", "Detroit": "MI", "Minneapolis": "MN", "Salt Lake City": "UT",
            "Seattle": "WA", "Los Angeles": "CA", "New York": "NY", "Boston": "MA",
            "Dallas": "TX", "Charlotte": "NC", "Phoenix": "AZ", "Miami": "FL",
            "Chicago": "IL", "Washington": "DC", "Newark": "NJ", "Houston": "TX",
            "Denver": "CO", "San Francisco": "CA", "Fort Lauderdale": "FL",
            "Las Vegas": "NV", "Baltimore": "MD", "Oakland": "CA", "Portland": "OR",
            "Anchorage": "AK", "Orlando": "FL"
        }
        
        hub_city = hub.split()[0]  # Get first word (city name)
        state = state_map.get(hub_city, "Unknown")
        
        opportunity = {
            "company_name": f"{airline_name} - {hub} Hub ({base_code})",
            "company_type": "Commercial Airline",
            "category": "airline",
            "city": hub,
            "state": state,
            "aircraft_types": "Various Commercial Aircraft",
            "fleet_size": "Multiple Aircraft",
            "contact_email": all_emails[0] if all_emails else None,
            "contact_phone": all_phones[0] if all_phones else None,
            "website_url": airline_info['about_url'],
            "services_needed": "Terminal cleaning, Gate areas, Crew rooms, Aircraft cabin cleaning, Hangar maintenance",
            "facilities_mentioned": ", ".join(all_facilities) if all_facilities else "Hub operations",
            "base_code": base_code,
            "discovered_at": datetime.now().isoformat(),
            "data_source": "airline_website_scraper",
            "discovered_via": "public_website",
            "estimated_value": "High - Major hub operations"
        }
        
        opportunities.append(opportunity)
        print(f"  ✅ Created opportunity: {hub} Hub ({base_code})")
    
    return opportunities


def scrape_all_airlines(airlines_list=None):
    """
    Scrape all airlines or a specific list.
    
    Args:
        airlines_list: List of airline names to scrape, or None for all
    
    Returns:
        List of opportunities
    """
    all_opportunities = []
    
    targets = AIRLINE_TARGETS
    if airlines_list:
        targets = {k: v for k, v in AIRLINE_TARGETS.items() if k in airlines_list}
    
    print(f"\n🛫 Starting Airline Scraper")
    print(f"📊 Target Airlines: {len(targets)}")
    print(f"📍 Expected Opportunities: {sum(len(v['bases']) for v in targets.values())}")
    print("="*70)
    
    for airline_name, airline_info in targets.items():
        opportunities = scrape_airline_complete(airline_name, airline_info)
        all_opportunities.extend(opportunities)
        time.sleep(3)  # Respectful delay between airlines
    
    return all_opportunities


# ---------------------------------------
# CLI EXECUTION
# ---------------------------------------

if __name__ == "__main__":
    print("\n" + "="*70)
    print("✈️ AIRLINE WEBSITE SCRAPER - Smart Approach")
    print("="*70)
    print("\n💡 Strategy:")
    print("  • Scrape public airline career & about pages")
    print("  • Extract facility locations (hubs/bases)")
    print("  • Find contact information")
    print("  • Create opportunities for each hub")
    print("\n📋 Target Airlines: 8 major carriers")
    print("📍 Expected Opportunities: ~50 hub/base locations")
    print("="*70)
    
    # Run scraper
    results = scrape_all_airlines()
    
    print("\n" + "="*70)
    print(f"✅ SCRAPING COMPLETE - Found {len(results)} Opportunities")
    print("="*70)
    
    if results:
        # Summary by airline
        print("\n📊 SUMMARY BY AIRLINE:")
        airlines = {}
        for r in results:
            airline = r['company_name'].split(' - ')[0]
            airlines[airline] = airlines.get(airline, 0) + 1
        
        for airline, count in airlines.items():
            print(f"  • {airline}: {count} hubs/bases")
        
        # Summary by state
        print("\n📊 SUMMARY BY STATE:")
        states = {}
        for r in results:
            state = r.get('state', 'Unknown')
            states[state] = states.get(state, 0) + 1
        
        for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {state}: {count} locations")
        
        # Contact info stats
        with_email = sum(1 for r in results if r.get('contact_email'))
        with_phone = sum(1 for r in results if r.get('contact_phone'))
        print(f"\n📞 CONTACT INFORMATION:")
        print(f"  • Opportunities with email: {with_email}/{len(results)}")
        print(f"  • Opportunities with phone: {with_phone}/{len(results)}")
        
        # Save results
        filename = f"airline_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
        
        # Sample results
        print("\n📋 Sample Opportunities:")
        for i, opp in enumerate(results[:5], 1):
            print(f"\n{i}. {opp['company_name']}")
            print(f"   Location: {opp['city']}, {opp['state']}")
            print(f"   Services: {opp['services_needed'][:80]}...")
            if opp.get('contact_email'):
                print(f"   Email: {opp['contact_email']}")
            if opp.get('contact_phone'):
                print(f"   Phone: {opp['contact_phone']}")
            print(f"   Base Code: {opp['base_code']}")
    else:
        print("\n⚠️ No opportunities found.")
        print("\nCheck:")
        print("  • Internet connection")
        print("  • Airline website availability")
        print("  • Rate limiting delays")
