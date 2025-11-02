"""
Virginia eVA Procurement Portal Scraper
Scrapes future procurement opportunities from Virginia's official procurement portal
and adds them to the local government contracts database.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import re
import time

# Database connection
DB_PATH = 'leads.db'

def clean_text(text):
    """Clean and normalize text from web scraping"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def extract_price_range(price_text):
    """Extract numeric value from price range text"""
    if not price_text or "Not provided" in price_text:
        return "Not specified"
    return clean_text(price_text)

def scrape_eva_opportunities():
    """Scrape opportunities from Virginia eVA portal"""
    url = "https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)"
    
    print("🔍 Fetching Virginia eVA procurement opportunities...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        opportunities = []
        
        # Parse the text content directly
        page_text = soup.get_text()
        
        # Split by FPR entries
        fpr_sections = page_text.split('FPR')
        
        for section in fpr_sections[1:]:  # Skip first split before any FPR
            try:
                lines = [line.strip() for line in section.split('\n') if line.strip()]
                
                if len(lines) < 3:
                    continue
                
                # First non-empty line is usually the FPR number
                fpr_number = lines[0].strip() if lines else "N/A"
                
                # Find title (usually appears before the FPR section)
                title = "Procurement Opportunity"
                
                # Extract agency (look for Department, Virginia, etc.)
                agency = "Virginia State Agency"
                for line in lines:
                    if any(keyword in line for keyword in ['Department', 'Virginia', 'Agency', 'Division']):
                        agency = line
                        break
                
                # Extract estimated issue date
                issue_date = "Not specified"
                for line in lines:
                    if 'Estimated Issue Date:' in line:
                        issue_date = line.replace('Estimated Issue Date:', '').strip()
                        break
                
                # Extract price range
                price_value = 0
                price_text = "Not specified"
                for line in lines:
                    if 'Estimated Price Range:' in line:
                        price_text = line.replace('Estimated Price Range:', '').strip()
                        # Try to extract numeric value
                        price_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', price_text)
                        if price_match:
                            price_value = float(price_match.group(1).replace(',', ''))
                        break
                
                # Extract buyer info
                buyer_name = "Procurement Office"
                buyer_email = ""
                buyer_phone = ""
                
                for line in lines:
                    if 'Buyer:' in line:
                        buyer_name = line.replace('Buyer:', '').strip()
                    elif '@' in line and '.gov' in line:
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.gov', line)
                        if email_match:
                            buyer_email = email_match.group(0)
                    elif re.search(r'\d{3}[-\s]?\d{3}[-\s]?\d{4}', line):
                        phone_match = re.search(r'(\d{3}[-\s]?\d{3}[-\s]?\d{4})', line)
                        if phone_match:
                            buyer_phone = phone_match.group(1)
                
                # Determine category
                category = "General Services"
                section_lower = section.lower()
                if 'non-prof serv' in section_lower or 'professional' in section_lower:
                    category = "Professional Services"
                elif 'tech' in section_lower or 'technology' in section_lower:
                    category = "Technology Services"
                elif 'supplies' in section_lower or 'equipment' in section_lower:
                    category = "Supplies & Equipment"
                elif 'cleaning' in section_lower or 'janitorial' in section_lower:
                    category = "Cleaning Services"
                
                # Skip entries without meaningful data
                if fpr_number in ['Login', 'Success', 'Commodities', 'N/A']:
                    continue
                
                # Create description
                description = f"Virginia eVA Future Procurement\n"
                description += f"FPR Number: {fpr_number}\n"
                description += f"Estimated Issue Date: {issue_date}\n"
                description += f"Price Range: {price_text}\n"
                if buyer_email:
                    description += f"Contact: {buyer_name} ({buyer_email})\n"
                description += f"Category: {category}"
                
                # Create opportunity record
                opportunity = {
                    'title': f"FPR {fpr_number} - {agency[:50]}",
                    'agency': agency,
                    'location': 'Virginia',
                    'value': price_value,
                    'deadline': issue_date,
                    'description': description,
                    'naics_code': '',
                    'website_url': url
                }
                
                opportunities.append(opportunity)
                
            except Exception as e:
                print(f"⚠️  Error parsing section: {str(e)[:100]}")
                continue
        
        # Remove duplicates
        unique_opps = []
        seen_titles = set()
        for opp in opportunities:
            if opp['title'] not in seen_titles:
                unique_opps.append(opp)
                seen_titles.add(opp['title'])
        
        print(f"✅ Found {len(unique_opps)} unique opportunities from Virginia eVA")
        return unique_opps
        
    except Exception as e:
        print(f"❌ Error scraping eVA portal: {e}")
        return []

def save_to_database(opportunities):
    """Save opportunities to the database"""
    if not opportunities:
        print("No opportunities to save.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    for opp in opportunities:
        try:
            # Check if opportunity already exists (by title and agency)
            cursor.execute('''
                SELECT id FROM contracts 
                WHERE title = ? AND agency = ?
            ''', (opp['title'], opp['agency']))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE contracts SET
                        location = ?, value = ?, deadline = ?, 
                        description = ?, naics_code = ?, website_url = ?
                    WHERE id = ?
                ''', (
                    opp['location'], opp['value'], opp['deadline'], 
                    opp['description'], opp['naics_code'], opp['website_url'],
                    existing[0]
                ))
                updated_count += 1
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO contracts (
                        title, agency, location, value, deadline, 
                        description, naics_code, website_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    opp['title'], opp['agency'], opp['location'], 
                    opp['value'], opp['deadline'], opp['description'], 
                    opp['naics_code'], opp['website_url']
                ))
                added_count += 1
                
        except Exception as e:
            print(f"⚠️  Error saving opportunity '{opp.get('title', 'Unknown')}': {e}")
            skipped_count += 1
            continue
    
    conn.commit()
    conn.close()
    
    print(f"✅ Added {added_count} new opportunities")
    print(f"🔄 Updated {updated_count} existing opportunities")
    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} opportunities due to errors")
    print(f"📊 Total processed: {added_count + updated_count}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("🏛️  VIRGINIA eVA PROCUREMENT SCRAPER")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Scrape opportunities
    opportunities = scrape_eva_opportunities()
    
    if opportunities:
        print()
        print("💾 Saving to database...")
        save_to_database(opportunities)
    else:
        print("❌ No opportunities found to save.")
    
    print()
    print("=" * 60)
    print(f"✅ SCRAPING COMPLETED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
