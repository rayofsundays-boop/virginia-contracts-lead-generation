#!/usr/bin/env python3
"""
Fix Supply Contract URLs using OpenAI and Smart URL Generation
Finds correct business URLs for suppliers with broken links
"""

import os
import sys
import sqlite3
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

def test_url(url, timeout=5):
    """Test if URL is accessible"""
    if not url:
        return False
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def guess_supplier_urls(company_name):
    """Generate intelligent guesses for supplier portal URLs"""
    # Clean company name
    clean_name = company_name.lower()
    clean_name = re.sub(r'\s+(inc|corp|corporation|llc|ltd|international|group|hotels?|healthcare|clinic|facilities|properties|management)\.?', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    clean_name = clean_name.strip()
    
    # Create domain-friendly version
    domain_base = clean_name.replace(' ', '')
    
    # Common supplier portal patterns
    patterns = [
        f"https://www.{domain_base}.com/suppliers",
        f"https://{domain_base}.com/suppliers",
        f"https://www.{domain_base}.com/vendors",
        f"https://{domain_base}.com/vendors",
        f"https://supplier.{domain_base}.com",
        f"https://vendors.{domain_base}.com",
        f"https://www.{domain_base}.com/about/suppliers",
        f"https://www.{domain_base}.com/corporate/suppliers",
        f"https://www.{domain_base}.com/procurement",
        f"https://www.{domain_base}.com/doing-business",
        f"https://www.{domain_base}.com/supply-chain",
        f"https://www.{domain_base}.com",  # Just homepage
        f"https://{domain_base}.com",  # Homepage without www
    ]
    
    return patterns

def find_working_url(url_list):
    """Test list of URLs and return first working one"""
    for url in url_list:
        if test_url(url):
            return url
    return None

def find_business_with_openai(company_name, location=None):
    """Use OpenAI to research and find business URL"""
    if not OPENAI_API_KEY:
        print("  ⚠️  No OPENAI_API_KEY configured")
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        query = f"{company_name}"
        if location:
            query += f" in {location}"
        
        prompt = f"""Find the official supplier/vendor portal website URL for: {query}

Research their procurement or supplier registration page. Common patterns:
- /suppliers
- /vendors  
- /procurement
- /doing-business
- supplier.companyname.com

Return ONLY the exact working URL, no JSON, no explanation. Example:
https://www.companyname.com/suppliers"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a business research assistant. Return only the exact URL, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        url = response.choices[0].message.content.strip()
        
        # Clean up response
        url = url.replace('```', '').strip()
        if not url.startswith('http'):
            return None
        
        # Test if URL works
        if test_url(url):
            return url
        
        print(f"  ⚠️  OpenAI suggested URL doesn't work: {url}")
        return None
        
    except Exception as e:
        print(f"  🔴 OpenAI API error: {str(e)[:60]}")
        return None

def fix_supply_contract_urls(dry_run=False, limit=None):
    """Main function to fix all broken supply contract URLs"""
    
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    # Get all supply contracts with URLs
    query = """
        SELECT id, title, agency, location, website_url, contact_phone 
        FROM supply_contracts 
        WHERE website_url IS NOT NULL
        ORDER BY id
    """
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
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
        
        new_url = None
        
        # Method 1: Try intelligent URL guessing
        print(f"   ↻ Trying intelligent URL patterns...")
        url_guesses = guess_supplier_urls(agency)
        new_url = find_working_url(url_guesses)
        
        # Method 2: Fallback to OpenAI
        if not new_url:
            print(f"   ↻ Trying OpenAI research...")
            new_url = find_business_with_openai(agency, location)
        
        if new_url:
            print(f"   ✅ Found: {new_url}")
            
            if not dry_run:
                # Update database
                cursor.execute("""
                    UPDATE supply_contracts 
                    SET website_url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_url, contract_id))
                conn.commit()
                print(f"   💾 Updated database")
            else:
                print(f"   🔍 DRY RUN: Would update to {new_url}")
            
            fixed_count += 1
        else:
            print(f"   ❌ Could not find valid URL")
            failed_count += 1
        
        # Rate limiting for OpenAI API
        time.sleep(0.5)
    
    print(f"\n{'='*80}")
    print(f"📊 Final Results:")
    print(f"   ✅ Fixed: {fixed_count}/{len(broken)}")
    print(f"   ❌ Failed: {failed_count}/{len(broken)}")
    print(f"   📈 Success Rate: {(fixed_count/len(broken)*100):.1f}%")
    print(f"{'='*80}\n")
    
    conn.close()

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    limit = None
    
    # Parse limit argument
    for arg in sys.argv:
        if arg.startswith('--limit='):
            limit = int(arg.split('=')[1])
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No database changes will be made\n")
    else:
        print("\n⚠️  LIVE MODE - Database will be updated\n")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    fix_supply_contract_urls(dry_run=dry_run, limit=limit)
