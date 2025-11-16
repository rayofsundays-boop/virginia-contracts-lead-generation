#!/usr/bin/env python3
"""
Fix Supply Contract URLs with Enhanced Intelligent Pattern Matching
Uses advanced URL pattern recognition to fix broken supplier portal links
"""

import os
import sys
import sqlite3
import requests
import time
import re
from urllib.parse import urlparse

def test_url(url, timeout=5):
    """Test if URL is accessible"""
    if not url:
        return False
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        # Try GET if HEAD fails
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except:
            return False

def extract_domain_from_company(company_name):
    """Extract the most likely domain name from company name"""
    # Known company to domain mappings
    known_mappings = {
        'marriott international': 'marriott',
        'hilton worldwide': 'hilton',
        'hyatt hotels': 'hyatt',
        'hca healthcare': 'hcahealthcare',
        'kaiser permanente': 'kaiserpermanente',
        'mayo clinic': 'mayoclinic',
        'lausd': 'lausd',
        'university of california': 'ucop',
        'nyc doe': 'schools.nyc',
        'brookfield': 'brookfield',
        'cbre group': 'cbre',
        'target corporation': 'target',
        'walmart': 'walmart',
        'boeing': 'boeing',
        'general motors': 'gm',
        'amazon': 'amazon',
    }
    
    # Check known mappings first
    company_lower = company_name.lower()
    for key, domain in known_mappings.items():
        if key in company_lower:
            return domain
    
    # Generic extraction
    clean_name = company_name.lower()
    # Remove common suffixes
    clean_name = re.sub(r'\s+(inc|corp|corporation|llc|ltd|limited|international|group|hotels?|healthcare|health\s+system|clinic|facilities|properties|management|asset\s+management|worldwide|global)\.?', '', clean_name, flags=re.IGNORECASE)
    # Remove special characters
    clean_name = re.sub(r'[^\w\s]', '', clean_name)
    clean_name = clean_name.strip()
    
    # Create domain-friendly version
    if ' ' in clean_name:
        # For multi-word names, try concatenating
        domain_base = clean_name.replace(' ', '')
    else:
        domain_base = clean_name
    
    return domain_base

def generate_url_patterns(company_name, old_url=None):
    """Generate comprehensive list of possible URLs"""
    domain = extract_domain_from_company(company_name)
    
    urls = []
    
    # If we have an old URL, try to fix common issues
    if old_url:
        parsed = urlparse(old_url)
        base_domain = parsed.netloc
        
        # Try different paths on same domain
        for path in ['', '/suppliers', '/vendors', '/doing-business', '/procurement', 
                     '/supply-chain', '/about/suppliers', '/corporate/suppliers',
                     '/about-us/suppliers', '/business/suppliers']:
            urls.append(f"https://{base_domain}{path}")
        
        # Try without subdomain
        if base_domain.startswith('www.'):
            main_domain = base_domain[4:]
            for path in ['', '/suppliers', '/vendors']:
                urls.append(f"https://{main_domain}{path}")
        else:
            # Try with www
            for path in ['', '/suppliers', '/vendors']:
                urls.append(f"https://www.{base_domain}{path}")
    
    # Try based on domain extraction
    tlds = ['com', 'org', 'net']
    
    for tld in tlds:
        # With www
        urls.extend([
            f"https://www.{domain}.{tld}",
            f"https://www.{domain}.{tld}/suppliers",
            f"https://www.{domain}.{tld}/vendors",
            f"https://www.{domain}.{tld}/procurement",
            f"https://www.{domain}.{tld}/doing-business",
            f"https://www.{domain}.{tld}/supply-chain",
            f"https://www.{domain}.{tld}/about/suppliers",
            f"https://www.{domain}.{tld}/corporate/suppliers",
            f"https://www.{domain}.{tld}/business/suppliers",
        ])
        
        # Without www
        urls.extend([
            f"https://{domain}.{tld}",
            f"https://{domain}.{tld}/suppliers",
            f"https://{domain}.{tld}/vendors",
            f"https://{domain}.{tld}/procurement",
        ])
        
        # Subdomain variations
        urls.extend([
            f"https://supplier.{domain}.{tld}",
            f"https://vendors.{domain}.{tld}",
            f"https://procurement.{domain}.{tld}",
        ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls

def find_working_url(url_list, verbose=False):
    """Test list of URLs and return first working one"""
    for url in url_list:
        if verbose:
            print(f"      Testing: {url}")
        
        if test_url(url):
            return url
    
    return None

def fix_supply_contract_urls(dry_run=False, limit=None, verbose=False):
    """Main function to fix all broken supply contract URLs"""
    
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    # Get all supply contracts with URLs (use ROWID since id column is NULL)
    query = """
        SELECT ROWID, title, agency, location, website_url, contact_phone 
        FROM supply_contracts 
        WHERE website_url IS NOT NULL
        ORDER BY ROWID
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
    fixed_urls = []
    
    for contract in broken:
        contract_id, title, agency, location, old_url, phone = contract
        
        print(f"\n🔍 [{fixed_count + failed_count + 1}/{len(broken)}] {title[:60]}...")
        print(f"   Agency: {agency}")
        print(f"   Old URL: {old_url}")
        
        # Generate URL patterns
        url_patterns = generate_url_patterns(agency, old_url)
        
        if verbose:
            print(f"   Generated {len(url_patterns)} URL patterns to test...")
        
        # Find working URL
        new_url = find_working_url(url_patterns, verbose=verbose)
        
        if new_url:
            print(f"   ✅ Found: {new_url}")
            fixed_urls.append({
                'id': contract_id,
                'title': title,
                'old': old_url,
                'new': new_url
            })
            
            if not dry_run:
                # Update database using ROWID
                cursor.execute("""
                    UPDATE supply_contracts 
                    SET website_url = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE ROWID = ?
                """, (new_url, contract_id))
                conn.commit()
                print(f"   💾 Updated database (ROWID: {contract_id})")
            else:
                print(f"   🔍 DRY RUN: Would update to {new_url}")
            
            fixed_count += 1
        else:
            print(f"   ❌ Could not find valid URL (tested {len(url_patterns)} patterns)")
            failed_count += 1
        
        # Rate limiting
        time.sleep(0.2)
    
    print(f"\n{'='*80}")
    print(f"📊 Final Results:")
    print(f"   ✅ Fixed: {fixed_count}/{len(broken)}")
    print(f"   ❌ Failed: {failed_count}/{len(broken)}")
    print(f"   📈 Success Rate: {(fixed_count/len(broken)*100):.1f}%")
    print(f"{'='*80}\n")
    
    if fixed_urls and not dry_run:
        print(f"\n✅ Successfully updated {len(fixed_urls)} URLs:")
        for item in fixed_urls:
            print(f"   • {item['title'][:50]}")
            print(f"     {item['new']}")
    
    conn.close()

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
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
    
    fix_supply_contract_urls(dry_run=dry_run, limit=limit, verbose=verbose)
