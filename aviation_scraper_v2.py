"""
Aviation Cleaning Lead Scraper V2
Scrapes directly from airport procurement pages, airline vendor portals, and ground handler websites
Bypasses Google search limitations by using known procurement URLs
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse

# ---------------------------------------
# DIRECT PROCUREMENT URLS
# ---------------------------------------

AIRPORT_PROCUREMENT_URLS = {
    "Washington Dulles (IAD) / Reagan (DCA)": {
        "url": "https://www.mwaa.com/business-opportunities",
        "state": "VA",
        "city": "Washington",
        "search_terms": ["janitorial", "custodial", "cleaning", "sanitation"]
    },
    "Richmond International (RIC)": {
        "url": "https://www.flyrichmond.com/business/business-opportunities",
        "state": "VA",
        "city": "Richmond",
        "search_terms": ["janitorial", "custodial", "cleaning"]
    },
    "Norfolk International (ORF)": {
        "url": "https://www.norfolkairport.com/business/",
        "state": "VA",
        "city": "Norfolk",
        "search_terms": ["janitorial", "custodial", "cleaning", "maintenance"]
    },
    "Baltimore/Washington (BWI)": {
        "url": "https://www.bwiairport.com/doing-business",
        "state": "MD",
        "city": "Baltimore",
        "search_terms": ["janitorial", "custodial", "cleaning"]
    },
    "Charlotte Douglas (CLT)": {
        "url": "https://www.cltairport.com/business/procurement",
        "state": "NC",
        "city": "Charlotte",
        "search_terms": ["janitorial", "custodial", "cleaning"]
    },
    "Raleigh-Durham (RDU)": {
        "url": "https://www.rdu.com/corporate/business-opportunities/",
        "state": "NC",
        "city": "Raleigh",
        "search_terms": ["janitorial", "custodial", "cleaning"]
    },
    "Newport News (PHF)": {
        "url": "https://www.flyphf.com/business/",
        "state": "VA",
        "city": "Newport News",
        "search_terms": ["janitorial", "custodial", "cleaning"]
    },
}

AIRLINE_VENDOR_URLS = {
    "Delta Airlines": {
        "url": "https://www.delta.com/us/en/about-delta/corporate-information/supplier-information",
        "category": "airline",
        "services": ["cabin cleaning", "aircraft cleaning"]
    },
    "American Airlines": {
        "url": "https://www.aa.com/i18n/customer-service/support/supplier-information.jsp",
        "category": "airline",
        "services": ["cabin cleaning", "aircraft cleaning"]
    },
    "United Airlines": {
        "url": "https://www.united.com/ual/en/us/fly/company/suppliers.html",
        "category": "airline",
        "services": ["cabin cleaning", "aircraft cleaning"]
    },
    "Southwest Airlines": {
        "url": "https://www.southwestairlines.com/about-southwest/procurement/",
        "category": "airline",
        "services": ["cabin cleaning", "aircraft cleaning"]
    },
}

GROUND_HANDLER_URLS = {
    "Swissport": {
        "url": "https://www.swissport.com/en/about-us/suppliers",
        "category": "ground_handler",
        "services": ["facility cleaning", "aircraft cleaning"]
    },
    "ABM Aviation": {
        "url": "https://www.abm.com/industries/aviation/",
        "category": "ground_handler",
        "services": ["facility cleaning", "janitorial"]
    },
    "Prospect Airport Services": {
        "url": "https://www.prospectgs.com/services",
        "category": "ground_handler",
        "services": ["facility cleaning", "ground handling"]
    },
}

# ---------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------

def extract_contact_info(text):
    """Extract email and phone numbers from text."""
    contacts = {}
    
    # Email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contacts['email'] = emails[0]
    
    # Phone regex
    phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    phones = re.findall(phone_pattern, text)
    if phones:
        contacts['phone'] = phones[0]
    
    return contacts


def extract_deadline(text):
    """Extract deadline dates from text."""
    date_patterns = [
        r'(?:due|deadline|closing|submit)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})[:\s]+(?:due|deadline)',
        r'(?:by|before)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def scrape_direct_url(url, source_name, category, location_info):
    """
    Scrape opportunities directly from a procurement/vendor page.
    
    Args:
        url: Direct URL to scrape
        source_name: Name of the source (e.g., "Washington Dulles (IAD)")
        category: "airport", "airline", or "ground_handler"
        location_info: Dict with state, city info
    
    Returns:
        List of opportunity dictionaries
    """
    opportunities = []
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"  📄 Scraping: {source_name}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"    ⚠️ HTTP {response.status_code}")
            return opportunities
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text(" ", strip=True).lower()
        
        # Keywords to detect opportunities
        opportunity_keywords = ['rfp', 'rfq', 'bid', 'solicitation', 'proposal', 'procurement', 'vendor registration', 'contract']
        cleaning_keywords = ['janitorial', 'custodial', 'cleaning', 'sanitation', 'housekeeping', 'porter', 'maintenance']
        
        # Find all links that might be opportunities
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(" ", strip=True).lower()
            link_href = link.get('href')
            
            # Check if link text contains opportunity keywords
            has_opportunity = any(keyword in link_text for keyword in opportunity_keywords)
            has_cleaning = any(keyword in link_text for keyword in cleaning_keywords)
            
            # Also check surrounding text
            if not (has_opportunity or has_cleaning):
                parent_text = link.parent.get_text(" ", strip=True).lower() if link.parent else ""
                has_opportunity = any(keyword in parent_text for keyword in opportunity_keywords)
                has_cleaning = any(keyword in parent_text for keyword in cleaning_keywords)
            
            if has_opportunity or has_cleaning:
                # Build full URL
                full_url = urljoin(base_url, link_href)
                
                # Get context around the link
                context = link.parent.get_text(" ", strip=True) if link.parent else link_text
                context = context[:500]
                
                # Extract contacts from context
                contacts = extract_contact_info(context)
                deadline = extract_deadline(context)
                
                # Detect keywords
                detected = [k for k in opportunity_keywords + cleaning_keywords if k in (link_text + " " + context).lower()]
                
                opportunity = {
                    "title": link.get_text(strip=True) or "Procurement Opportunity",
                    "url": full_url,
                    "category": category,
                    "source": source_name,
                    "summary": context,
                    "detected_keywords": list(set(detected)),
                    "contact_email": contacts.get('email'),
                    "contact_phone": contacts.get('phone'),
                    "deadline": deadline,
                    "state": location_info.get('state', 'Unknown'),
                    "city": location_info.get('city', 'Unknown'),
                    "discovered_at": datetime.now().isoformat(),
                    "data_source": "direct_url_scraping"
                }
                
                opportunities.append(opportunity)
                print(f"    ✅ Found: {opportunity['title'][:60]}")
        
        # If no specific links found, check if the main page itself is an opportunity
        if not opportunities:
            has_opportunity_content = any(keyword in page_text for keyword in opportunity_keywords)
            has_cleaning_content = any(keyword in page_text for keyword in cleaning_keywords)
            
            if has_opportunity_content or has_cleaning_content:
                page_title = soup.title.string if soup.title else source_name
                detected = [k for k in opportunity_keywords + cleaning_keywords if k in page_text]
                
                # Get first 1000 chars as summary
                summary = soup.get_text(" ", strip=True)[:1000]
                contacts = extract_contact_info(summary)
                deadline = extract_deadline(summary)
                
                opportunity = {
                    "title": f"{source_name} - {page_title}",
                    "url": url,
                    "category": category,
                    "source": source_name,
                    "summary": summary,
                    "detected_keywords": list(set(detected[:10])),
                    "contact_email": contacts.get('email'),
                    "contact_phone": contacts.get('phone'),
                    "deadline": deadline,
                    "state": location_info.get('state', 'Unknown'),
                    "city": location_info.get('city', 'Unknown'),
                    "discovered_at": datetime.now().isoformat(),
                    "data_source": "direct_url_scraping"
                }
                
                opportunities.append(opportunity)
                print(f"    ✅ Page contains opportunity info")
        
        if not opportunities:
            print(f"    ℹ️ No opportunities detected")
        
    except requests.exceptions.Timeout:
        print(f"    ⏱️ Timeout")
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:50]}")
    
    return opportunities


# ---------------------------------------
# MAIN SCRAPER FUNCTIONS
# ---------------------------------------

def scrape_airports(max_sources=None):
    """Scrape airport procurement pages."""
    print("\n🏢 Scraping Airport Procurement Pages...\n")
    all_opportunities = []
    
    sources = list(AIRPORT_PROCUREMENT_URLS.items())
    if max_sources:
        sources = sources[:max_sources]
    
    for airport_name, info in sources:
        opportunities = scrape_direct_url(
            url=info['url'],
            source_name=airport_name,
            category="airport",
            location_info={"state": info['state'], "city": info['city']}
        )
        all_opportunities.extend(opportunities)
        time.sleep(2)  # Rate limiting
    
    return all_opportunities


def scrape_airlines(max_sources=None):
    """Scrape airline vendor portals."""
    print("\n✈️ Scraping Airline Vendor Portals...\n")
    all_opportunities = []
    
    sources = list(AIRLINE_VENDOR_URLS.items())
    if max_sources:
        sources = sources[:max_sources]
    
    for airline_name, info in sources:
        opportunities = scrape_direct_url(
            url=info['url'],
            source_name=airline_name,
            category="airline",
            location_info={"state": "National", "city": "Multiple"}
        )
        all_opportunities.extend(opportunities)
        time.sleep(2)
    
    return all_opportunities


def scrape_ground_handlers(max_sources=None):
    """Scrape ground handling company pages."""
    print("\n🔧 Scraping Ground Handler Websites...\n")
    all_opportunities = []
    
    sources = list(GROUND_HANDLER_URLS.items())
    if max_sources:
        sources = sources[:max_sources]
    
    for company_name, info in sources:
        opportunities = scrape_direct_url(
            url=info['url'],
            source_name=company_name,
            category="ground_handler",
            location_info={"state": "National", "city": "Multiple"}
        )
        all_opportunities.extend(opportunities)
        time.sleep(2)
    
    return all_opportunities


def scrape_all_v2(max_airports=None, max_airlines=None, max_ground_handlers=None):
    """
    Scrape all aviation opportunities using direct URLs.
    
    Args:
        max_airports: Limit airport sources (None = all 7)
        max_airlines: Limit airline sources (None = all 4)
        max_ground_handlers: Limit ground handler sources (None = all 3)
    
    Returns:
        List of all opportunities found
    """
    all_opportunities = []
    
    # Scrape airports
    if max_airports != 0:
        airport_opps = scrape_airports(max_sources=max_airports)
        all_opportunities.extend(airport_opps)
    
    # Scrape airlines
    if max_airlines != 0:
        airline_opps = scrape_airlines(max_sources=max_airlines)
        all_opportunities.extend(airline_opps)
    
    # Scrape ground handlers
    if max_ground_handlers != 0:
        ground_opps = scrape_ground_handlers(max_sources=max_ground_handlers)
        all_opportunities.extend(ground_opps)
    
    return all_opportunities


# ---------------------------------------
# CLI EXECUTION
# ---------------------------------------

if __name__ == "__main__":
    print("\n" + "="*70)
    print("✈️ AVIATION LEAD SCRAPER V2 - Direct URL Scraping")
    print("="*70)
    print("\n📋 Configuration:")
    print("  • Method: Direct URL scraping (no Google search)")
    print("  • Airports: 7 sources")
    print("  • Airlines: 4 sources")
    print("  • Ground Handlers: 3 sources")
    print("  • Total: 14 direct sources")
    print("="*70)
    
    # Run scraper
    results = scrape_all_v2()
    
    print("\n" + "="*70)
    print(f"✅ SCRAPING COMPLETE - Found {len(results)} Opportunities")
    print("="*70)
    
    if results:
        # Summary by category
        print("\n📊 SUMMARY BY CATEGORY:")
        categories = {}
        for r in results:
            cat = r.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in categories.items():
            print(f"  • {cat.upper()}: {count} opportunities")
        
        # Summary by source
        print("\n📊 SUMMARY BY SOURCE:")
        sources = {}
        for r in results:
            src = r.get('source', 'unknown')
            sources[src] = sources.get(src, 0) + 1
        
        for src, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {src}: {count}")
        
        # Save results
        filename = f"aviation_leads_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
        
        print("\n📋 Sample Results:")
        for i, opp in enumerate(results[:5], 1):
            print(f"\n{i}. {opp['title'][:70]}")
            print(f"   Source: {opp['source']}")
            print(f"   Category: {opp['category']}")
            print(f"   URL: {opp['url'][:70]}...")
            if opp.get('contact_email'):
                print(f"   Email: {opp['contact_email']}")
            if opp.get('deadline'):
                print(f"   Deadline: {opp['deadline']}")
    else:
        print("\n⚠️ No opportunities found.")
        print("\nPossible reasons:")
        print("  • Websites may be down or changed structure")
        print("  • No active procurement postings currently")
        print("  • URLs may need updating")
        print("\n💡 Try updating URLs in AIRPORT_PROCUREMENT_URLS, AIRLINE_VENDOR_URLS, GROUND_HANDLER_URLS")
