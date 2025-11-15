"""
Aviation Cleaning Lead Scraper
Scrapes airport procurement portals, airline vendor portals, and ground-handling companies
for janitorial, custodial, and aircraft cleaning contract opportunities.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import urllib.parse
from datetime import datetime
import re

# ---------------------------------------
# ✈️ SCRAPING PROMPT (SYSTEM INSTRUCTIONS)
# ---------------------------------------

SCRAPER_PROMPT = """
Your task is to scrape and extract all active airline, airport, aviation, and aircraft cleaning contract opportunities
from airport procurement portals, airline vendor portals, and ground-handling companies.

You must extract:
- title
- category (airport, airline, ground handling)
- link to the opportunity
- summary or description
- due date
- required documents
- vendor registration link (if applicable)
- subcontractor contact info (if listed)
- location
- estimated value (if available)
- notes

Search patterns:
1. Airport procurement portals:
   "Airport name + procurement"
   "Airport name + janitorial"
   "Airport name + aircraft cleaning"
   "Airport name + custodial services + RFP"

2. Airline vendor registration:
   "airline name + vendor registration"
   "airline name + cabin cleaning RFP"
   "airline name + cleaning contract"

3. Ground handling companies:
   "Company name + subcontractor"
   "Company name + vendor registration"
   "Company name + cleaning contract"

ONLY return contract opportunities, RFPs, RFQs, bid notices, or vendor registration instructions.
IGNORE job postings.

Return output as a JSON array of objects with a summary following the JSON block.
"""

# ---------------------------------------
# SEARCH TERMS & TARGET LISTS
# ---------------------------------------

AIRPORTS = [
    "Washington Dulles IAD MWAA procurement",
    "Reagan National DCA MWAA procurement",
    "Richmond International Airport RIC procurement",
    "Norfolk Airport ORF procurement",
    "Baltimore Washington International BWI procurement",
    "Charlotte Douglas Airport CLT procurement",
    "Raleigh Durham Airport RDU procurement",
    "Newport News Airport PHF procurement",
]

AIRLINES = [
    "Delta Airlines supplier portal",
    "American Airlines vendor registration",
    "United Airlines supplier registration",
    "Southwest Airlines supplier portal",
    "JetBlue Airways vendor registration",
    "Spirit Airlines supplier portal",
    "Frontier Airlines vendor registration",
]

GROUND_HANDLERS = [
    "Swissport subcontractor",
    "GAT Airline Ground Support vendor registration",
    "Prospect Airport Services subcontractor",
    "ABM Aviation cleaning contract",
    "PrimeFlight Aviation Services subcontractor",
    "Menzies Aviation vendor registration",
    "Signature Flight Support subcontractor",
    "Atlantic Aviation vendor registration",
]

# ---------------------------------------
# BASIC SCRAPER FUNCTION
# ---------------------------------------

def google_search(query, num_results=5):
    """Performs a simple Google scraping request via search query."""
    try:
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        links = []
        for g in soup.select("a"):
            href = g.get("href")
            if href and "http" in href and "google" not in href:
                # Clean up Google redirect URLs
                if "/url?q=" in href:
                    href = href.split("/url?q=")[1].split("&")[0]
                    href = urllib.parse.unquote(href)
                
                if href.startswith("http") and "google" not in href:
                    links.append(href)

        return list(set(links[:num_results]))  # Remove duplicates
    except Exception as e:
        print(f"  ⚠️ Google search error: {e}")
        return []


def extract_contact_info(text):
    """Extract email and phone numbers from text."""
    contacts = {}
    
    # Email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contacts['email'] = emails[0]
    
    # Phone regex (various formats)
    phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    phones = re.findall(phone_pattern, text)
    if phones:
        contacts['phone'] = phones[0]
    
    return contacts


def extract_deadline(text):
    """Attempt to extract deadline dates from text."""
    # Look for common date patterns near keywords like "due", "deadline", "closing"
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


def scrape_page(url):
    """Scrape a webpage and return detected opportunities."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Get page title
        title = soup.title.string if soup.title else url.split('//')[-1].split('/')[0]
        
        # Get full text
        text = soup.get_text(" ", strip=True)
        text_lower = text.lower()

        # Detection filters
        cleaning_keywords = ["janitorial", "custodial", "cleaning", "sanitation", "housekeeping", "porter"]
        contract_keywords = ["rfp", "rfq", "bid", "solicitation", "proposal", "contract", "vendor", "supplier"]
        
        # Check if page contains both cleaning and contract keywords
        has_cleaning = any(k in text_lower for k in cleaning_keywords)
        has_contract = any(k in contract_keywords for k in contract_keywords)
        
        # Filter out job posting sites
        job_sites = ["indeed", "linkedin", "glassdoor", "monster", "ziprecruiter", "careers"]
        is_job_site = any(site in url.lower() for site in job_sites)
        
        if has_cleaning and has_contract and not is_job_site:
            # Extract information
            detected_keywords = [k for k in cleaning_keywords + contract_keywords if k in text_lower]
            contacts = extract_contact_info(text[:5000])
            deadline = extract_deadline(text[:5000])
            
            # Extract summary (first 500 chars with contract keywords)
            summary = ""
            for keyword in contract_keywords:
                if keyword in text_lower:
                    idx = text_lower.index(keyword)
                    start = max(0, idx - 200)
                    end = min(len(text), idx + 300)
                    summary = text[start:end].strip()
                    break
            
            if not summary:
                summary = text[:500]
            
            return {
                "url": url,
                "title": title.strip() if title else "Untitled",
                "detected_keywords": detected_keywords,
                "summary": summary,
                "contact_email": contacts.get('email'),
                "contact_phone": contacts.get('phone'),
                "deadline": deadline,
                "discovered_at": datetime.now().isoformat()
            }
        return None
    except requests.exceptions.Timeout:
        print(f"  ⏱️ Timeout: {url}")
        return None
    except Exception as e:
        print(f"  ❌ Error scraping {url}: {str(e)[:50]}")
        return None


# ---------------------------------------
# MAIN SCRAPER PIPELINE
# ---------------------------------------

def scrape_all(max_results_per_category=3):
    """
    Scrape all aviation cleaning opportunities.
    
    Args:
        max_results_per_category: Limit results per search term to avoid rate limits
    
    Returns:
        List of opportunity dictionaries
    """
    all_results = []

    SEARCH_GROUPS = {
        "airport": AIRPORTS,
        "airline": AIRLINES,
        "ground_handler": GROUND_HANDLERS
    }

    for category, items in SEARCH_GROUPS.items():
        print(f"\n🔍 Searching {category.upper()} sources ({len(items)} queries)...\n")

        for q in items:
            print(f"  📡 Query: {q}")
            
            # Step 1: search Google
            links = google_search(q, num_results=max_results_per_category)
            print(f"    Found {len(links)} potential pages")

            for link in links:
                # Step 2: scrape each result
                result = scrape_page(link)
                if result:
                    result["category"] = category
                    result["search_query"] = q
                    all_results.append(result)
                    print(f"    ✅ Opportunity found: {result['title'][:60]}")

                time.sleep(2)  # Rate limiting

            time.sleep(1)  # Pause between searches

    return all_results


def scrape_by_category(category="airport", max_results=5):
    """
    Scrape opportunities for a specific category.
    
    Args:
        category: "airport", "airline", or "ground_handler"
        max_results: Maximum results per search query
    
    Returns:
        List of opportunity dictionaries
    """
    SEARCH_GROUPS = {
        "airport": AIRPORTS,
        "airline": AIRLINES,
        "ground_handler": GROUND_HANDLERS
    }
    
    if category not in SEARCH_GROUPS:
        print(f"❌ Invalid category: {category}")
        return []
    
    results = []
    items = SEARCH_GROUPS[category]
    
    print(f"\n🔍 Searching {category.upper()} ({len(items)} queries)...\n")
    
    for q in items:
        print(f"  📡 Query: {q}")
        links = google_search(q, num_results=max_results)
        print(f"    Found {len(links)} potential pages")
        
        for link in links:
            result = scrape_page(link)
            if result:
                result["category"] = category
                result["search_query"] = q
                results.append(result)
                print(f"    ✅ Found: {result['title'][:60]}")
            
            time.sleep(2)
        
        time.sleep(1)
    
    return results


# ---------------------------------------
# RUN SCRAPER (CLI)
# ---------------------------------------

if __name__ == "__main__":
    print("\n" + "="*70)
    print("✈️ AIRLINE & AIRPORT CLEANING LEAD SCRAPER")
    print("="*70)
    print(SCRAPER_PROMPT)
    print("="*70)

    # Run scraper
    results = scrape_all(max_results_per_category=3)

    print("\n" + "="*70)
    print(f"✅ SCRAPING COMPLETE - FOUND {len(results)} OPPORTUNITIES")
    print("="*70)
    
    if results:
        print("\n📊 SUMMARY BY CATEGORY:")
        categories = {}
        for r in results:
            cat = r.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in categories.items():
            print(f"  • {cat.upper()}: {count} opportunities")
        
        print("\n📋 DETAILED RESULTS:\n")
        print(json.dumps(results, indent=2))
        
        # Save to file
        filename = f"aviation_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
    else:
        print("\n⚠️ No opportunities found. Try adjusting search terms or running again later.")
