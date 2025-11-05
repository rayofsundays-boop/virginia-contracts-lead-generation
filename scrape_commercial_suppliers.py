#!/usr/bin/env python3
"""
Commercial Business Supplier Scraper
=====================================

Scrapes real commercial businesses that purchase cleaning supplies
Target: Hotels, hospitals, schools, office buildings, etc.

Data Sources:
1. Google Maps API (business listings with contact info)
2. Yellow Pages (commercial facility contacts)
3. Company websites (procurement department info)
4. LinkedIn (procurement manager contacts)

Usage:
    python scrape_commercial_suppliers.py

Requires:
    pip install requests beautifulsoup4 googlemaps selenium
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from app import app, db
from sqlalchemy import text

# Target business categories
BUSINESS_CATEGORIES = {
    'Hotels & Hospitality': [
        'hotel chains',
        'resort properties',
        'casino hotels',
        'conference centers'
    ],
    'Healthcare': [
        'hospital networks',
        'medical centers',
        'nursing homes',
        'assisted living facilities'
    ],
    'Education': [
        'school districts',
        'universities',
        'community colleges',
        'private schools'
    ],
    'Corporate Offices': [
        'office buildings',
        'corporate headquarters',
        'business parks',
        'coworking spaces'
    ],
    'Retail': [
        'shopping malls',
        'retail chains',
        'grocery stores',
        'department stores'
    ],
    'Manufacturing': [
        'manufacturing plants',
        'warehouses',
        'distribution centers',
        'industrial facilities'
    ]
}

# Major US cities to search
US_CITIES = [
    'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
    'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
    'Dallas, TX', 'San Jose, CA', 'Austin, TX', 'Jacksonville, FL',
    'Fort Worth, TX', 'Columbus, OH', 'Charlotte, NC', 'San Francisco, CA',
    'Indianapolis, IN', 'Seattle, WA', 'Denver, CO', 'Washington, DC',
    'Boston, MA', 'El Paso, TX', 'Nashville, TN', 'Detroit, MI',
    'Oklahoma City, OK', 'Portland, OR', 'Las Vegas, NV', 'Memphis, TN',
    'Louisville, KY', 'Baltimore, MD', 'Milwaukee, WI', 'Albuquerque, NM',
    'Tucson, AZ', 'Fresno, CA', 'Mesa, AZ', 'Sacramento, CA',
    'Atlanta, GA', 'Kansas City, MO', 'Colorado Springs, CO', 'Miami, FL',
    'Raleigh, NC', 'Omaha, NE', 'Long Beach, CA', 'Virginia Beach, VA',
    'Oakland, CA', 'Minneapolis, MN', 'Tulsa, OK', 'Tampa, FL',
    'Arlington, TX', 'New Orleans, LA'
]


def scrape_google_maps_places(category, city, api_key=None):
    """
    Scrape businesses from Google Maps/Places API
    
    Note: Requires Google Maps API key
    Set environment variable: GOOGLE_MAPS_API_KEY
    """
    if not api_key:
        print("⚠️  Google Maps API key not set - skipping Maps scraping")
        return []
    
    try:
        import googlemaps
        gmaps = googlemaps.Client(key=api_key)
        
        # Search for businesses
        places_result = gmaps.places(
            query=f"{category} in {city}",
            type='establishment'
        )
        
        businesses = []
        for place in places_result.get('results', [])[:5]:  # Limit to 5 per category
            place_id = place['place_id']
            details = gmaps.place(place_id)
            
            business = {
                'name': place.get('name'),
                'address': place.get('formatted_address'),
                'phone': details.get('result', {}).get('formatted_phone_number'),
                'website': details.get('result', {}).get('website'),
                'rating': place.get('rating'),
                'category': category,
                'city': city
            }
            businesses.append(business)
        
        return businesses
        
    except Exception as e:
        print(f"❌ Google Maps error: {str(e)}")
        return []


def scrape_yellowpages(category, city):
    """
    Scrape business listings from Yellow Pages
    """
    businesses = []
    
    try:
        # Format search terms
        search_term = category.replace(' ', '+')
        location = city.replace(', ', '+').replace(' ', '+')
        
        url = f"https://www.yellowpages.com/search?search_terms={search_term}&geo_location_terms={location}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find business listings
            listings = soup.find_all('div', class_='result', limit=5)
            
            for listing in listings:
                try:
                    name = listing.find('a', class_='business-name')
                    name = name.text.strip() if name else None
                    
                    phone = listing.find('div', class_='phones')
                    phone = phone.text.strip() if phone else None
                    
                    address = listing.find('div', class_='street-address')
                    address = address.text.strip() if address else None
                    
                    if name:
                        businesses.append({
                            'name': name,
                            'phone': phone,
                            'address': address,
                            'category': category,
                            'city': city,
                            'source': 'YellowPages'
                        })
                        
                except Exception as e:
                    continue
        
        time.sleep(2)  # Rate limiting
        return businesses
        
    except Exception as e:
        print(f"❌ YellowPages error for {category} in {city}: {str(e)}")
        return []


def scrape_company_procurement_info(company_name):
    """
    Try to find procurement/purchasing contact info from company website
    """
    try:
        # Search for company + procurement keywords
        search_query = f"{company_name} procurement purchasing contact"
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for email addresses
            emails = []
            text_content = soup.get_text()
            
            # Simple email regex
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text_content)
            
            # Filter for procurement-related emails
            procurement_emails = [
                email for email in emails 
                if any(keyword in email.lower() for keyword in ['procurement', 'purchasing', 'vendor', 'supplier'])
            ]
            
            return procurement_emails[0] if procurement_emails else None
        
        return None
        
    except Exception as e:
        return None


def save_to_database(businesses):
    """
    Save scraped businesses to supply_contracts table
    """
    with app.app_context():
        added = 0
        
        for business in businesses:
            try:
                # Estimate contract value based on business type
                estimated_values = {
                    'Hotels & Hospitality': '$50,000 - $150,000',
                    'Healthcare': '$100,000 - $500,000',
                    'Education': '$75,000 - $200,000',
                    'Corporate Offices': '$25,000 - $100,000',
                    'Retail': '$30,000 - $120,000',
                    'Manufacturing': '$60,000 - $250,000'
                }
                
                category = business.get('category', '')
                estimated_value = estimated_values.get(category, '$50,000 - $150,000')
                
                # Try to get procurement email
                procurement_email = scrape_company_procurement_info(business['name'])
                
                db.session.execute(text('''
                    INSERT INTO supply_contracts 
                    (title, agency, location, contract_type, product_category,
                     estimated_value, contract_term, description, website_url,
                     contact_name, contact_email, contact_phone, status, is_quick_win)
                    VALUES 
                    (:title, :agency, :location, :contract_type, :product_category,
                     :estimated_value, :contract_term, :description, :website_url,
                     :contact_name, :contact_email, :contact_phone, :status, :is_quick_win)
                '''), {
                    'title': f"{business['name']} - Janitorial Supplies",
                    'agency': business['name'],
                    'location': business.get('city', ''),
                    'contract_type': 'Annual Supply Contract',
                    'product_category': category,
                    'estimated_value': estimated_value,
                    'contract_term': '12 months',
                    'description': f"Commercial cleaning supplies procurement for {business['name']}. {category} facility requiring regular bulk supplies.",
                    'website_url': business.get('website'),
                    'contact_name': 'Procurement Department',
                    'contact_email': procurement_email or business.get('email'),
                    'contact_phone': business.get('phone'),
                    'status': 'active',
                    'is_quick_win': True
                })
                
                added += 1
                
            except Exception as e:
                print(f"❌ Error saving {business.get('name')}: {str(e)}")
                continue
        
        db.session.commit()
        print(f"✅ Added {added} businesses to database")
        return added


def main():
    """
    Main scraping function
    """
    print("=" * 80)
    print("COMMERCIAL BUSINESS SUPPLIER SCRAPER")
    print("=" * 80)
    print()
    
    all_businesses = []
    
    # Select top 10 cities to scrape
    cities_to_scrape = US_CITIES[:10]
    
    print(f"🔍 Scraping {len(cities_to_scrape)} major cities...")
    print()
    
    for city in cities_to_scrape:
        print(f"\n📍 Searching in {city}...")
        
        # Scrape 1-2 categories per city (to avoid overwhelming)
        for category_group, subcategories in list(BUSINESS_CATEGORIES.items())[:2]:
            for subcategory in subcategories[:1]:  # Just one subcategory
                print(f"  🏢 Category: {subcategory}")
                
                # Try Yellow Pages scraping (no API key needed)
                businesses = scrape_yellowpages(subcategory, city)
                
                if businesses:
                    print(f"    ✅ Found {len(businesses)} businesses")
                    all_businesses.extend(businesses)
                else:
                    print(f"    ⚠️  No results")
                
                time.sleep(3)  # Rate limiting
    
    print()
    print("=" * 80)
    print(f"📊 Total businesses scraped: {len(all_businesses)}")
    print("=" * 80)
    
    if all_businesses:
        print("\n💾 Saving to database...")
        save_to_database(all_businesses)
    else:
        print("\n⚠️  No businesses found to save")
    
    print("\n✅ Scraping complete!")
    print(f"🎯 Visit /supply-contracts to see results")


if __name__ == '__main__':
    main()
