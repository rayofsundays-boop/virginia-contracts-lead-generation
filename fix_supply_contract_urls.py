#!/usr/bin/env python3
"""
Fix Supply Contract URLs using Google Places API
Finds correct business URLs and contact info for suppliers with broken links
"""

import os
import sys
import sqlite3
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# Google Places API setup
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
GOOGLE_PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# OpenAI as fallback
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

def test_url(url):
    """Test if URL is accessible"""
    if not url:
        return False
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def find_business_with_google_places(company_name, location=None):
    """Find business using Google Places API"""
    if not GOOGLE_API_KEY:
        print("⚠️  No GOOGLE_API_KEY in environment")
        return None
    
    # Build search query
    query = f"{company_name}"
    if location:
        query += f" {location}"
    
    try:
        # Step 1: Find Place
        params = {
            'input': query,
            'inputtype': 'textquery',
            'fields': 'place_id,name',
            'key': GOOGLE_API_KEY
        }
        
        response = requests.get(GOOGLE_PLACES_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'OK' or not data.get('candidates'):
            print(f"  ⚠️  No Google Places results for: {query}")
            return None
        
        place_id = data['candidates'][0]['place_id']
        
        # Step 2: Get Place Details
        detail_params = {
            'place_id': place_id,
            'fields': 'name,website,formatted_phone_number,formatted_address',
            'key': GOOGLE_API_KEY
        }
        
        detail_response = requests.get(GOOGLE_PLACE_DETAILS_URL, params=detail_params, timeout=10)
        detail_response.raise_for_status()
        detail_data = detail_response.json()
        
        if detail_data.get('status') != 'OK':
            return None
        
        result = detail_data.get('result', {})
        website = result.get('website')
        phone = result.get('formatted_phone_number')
        address = result.get('formatted_address')
        
        # Verify website works
        if website and test_url(website):
            return {
                'website': website,
                'phone': phone,
                'address': address
            }
        
        print(f"  ⚠️  Google Places found no valid website for: {query}")
        return None
        
    except Exception as e:
        print(f"  🔴 Google Places API error: {str(e)[:60]}")
        return None

def find_business_with_openai(company_name, location=None):
    """Use OpenAI to research and find business URL"""
    if not OPENAI_API_KEY:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        query = f"{company_name}"
        if location:
            query += f" in {location}"
        
        prompt = f"""Find the official website URL for this business: {query}

Research their official website and provide:
1. Official website URL (must be valid and working)
2. Phone number (if available)
3. Verify the business exists

Return JSON only:
{{
    "website": "https://example.com",
    "phone": "+1-555-123-4567",
    "verified": true
}}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a business research assistant. Always return valid JSON with real, verified information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        data = json.loads(content)
        
        website = data.get('website')
        if website and test_url(website):
            return {
                'website': website,
                'phone': data.get('phone'),
                'address': None
            }
        
        return None
        
    except Exception as e:
        print(f"  🔴 OpenAI API error: {str(e)[:60]}")
        return None

def fix_supply_contract_urls(dry_run=False):
    """Main function to fix all broken supply contract URLs"""
    
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    # Get all supply contracts with URLs
    cursor.execute("""
        SELECT id, title, agency, location, website_url, contact_phone 
        FROM supply_contracts 
        WHERE website_url IS NOT NULL
        ORDER BY id
    """)
    
    contracts = cursor.fetchall()
    total = len(contracts)
    
    print(f"\n{'='*80}")
    print(f"🔍 Testing {total} Supply Contract URLs")
    print(f"{'='*80}\n")
    
    broken = []
    working = []
    
    # Test all URLs first
    for contract in contracts:
        contract_id, title, agency, location, url, phone = contract
        
        if test_url(url):
            working.append(contract)
            print(f"✅ Working: {title[:50]}...")
        else:
            broken.append(contract)
            print(f"❌ Broken:  {title[:50]}... | {url}")
    
    print(f"\n{'='*80}")
    print(f"📊 Results: {len(working)} working, {len(broken)} broken")
    print(f"{'='*80}\n")
    
    if not broken:
        print("🎉 All URLs are working!")
        conn.close()
        return
    
    # Fix broken URLs
    print(f"\n{'='*80}")
    print(f"🔧 Attempting to fix {len(broken)} broken URLs...")
    print(f"{'='*80}\n")
    
    fixed_count = 0
    failed_count = 0
    
    for contract in broken:
        contract_id, title, agency, location, old_url, phone = contract
        
        print(f"\n🔍 Fixing: {title[:60]}...")
        print(f"   Agency: {agency}")
        print(f"   Location: {location}")
        print(f"   Old URL: {old_url}")
        
        # Try Google Places first
        result = find_business_with_google_places(agency, location)
        
        # Fallback to OpenAI if Google fails
        if not result:
            print(f"   ↻ Trying OpenAI fallback...")
            result = find_business_with_openai(agency, location)
        
        if result:
            new_url = result['website']
            new_phone = result.get('phone') or phone
            
            print(f"   ✅ Found: {new_url}")
            
            if not dry_run:
                # Update database
                cursor.execute("""
                    UPDATE supply_contracts 
                    SET website_url = ?, contact_phone = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_url, new_phone, contract_id))
                conn.commit()
                print(f"   💾 Updated database")
            else:
                print(f"   🔍 DRY RUN: Would update database")
            
            fixed_count += 1
        else:
            print(f"   ❌ Could not find valid URL")
            failed_count += 1
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\n{'='*80}")
    print(f"📊 Final Results:")
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   🔧 Total broken: {len(broken)}")
    print(f"{'='*80}\n")
    
    conn.close()

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No database changes will be made\n")
    else:
        print("\n⚠️  LIVE MODE - Database will be updated\n")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    fix_supply_contract_urls(dry_run=dry_run)
