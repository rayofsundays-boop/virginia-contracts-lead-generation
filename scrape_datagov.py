"""
Enhanced Data.gov Contract Scraper
Fetches real federal contracts from USAspending.gov API
Handles actual response structure and extracts available data
"""
import requests
import json
from datetime import datetime, timedelta
from app import app, db
from sqlalchemy import text

# USAspending.gov API endpoint
USASPENDING_API = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

def fetch_virginia_contracts(days_back=90, max_results=200):
    """
    Fetch real contracts from USAspending.gov for Virginia
    """
    print("=" * 70)
    print("DATA.GOV CONTRACT SCRAPER")
    print("=" * 70)
    print()
    
    # Calculate date range
    end_date_dt = datetime.now()
    start_date_dt = end_date_dt - timedelta(days=days_back)
    
    print(f"📅 Searching period: {start_date_dt.strftime('%Y-%m-%d')} to {end_date_dt.strftime('%Y-%m-%d')}")
    print(f"🎯 Target: Virginia cleaning/janitorial contracts")
    print(f"📊 Max results: {max_results}")
    print()
    
    all_contracts = []
    page = 1
    per_page = 100  # API max limit
    
    while len(all_contracts) < max_results:
        print(f"📄 Fetching page {page}...")
        
        # Search filters for cleaning/janitorial services
        payload = {
            "filters": {
                "time_period": [
                    {
                        "start_date": start_date_dt.strftime("%Y-%m-%d"),
                        "end_date": end_date_dt.strftime("%Y-%m-%d")
                    }
                ],
                "place_of_performance_locations": [
                    {"country": "USA", "state": "VA"}
                ],
                "award_type_codes": ["A", "B", "C", "D"],  # Contracts
            },
            "fields": [
                "Award ID",
                "Recipient Name", 
                "Start Date",
                "End Date",
                "Award Amount",
                "Awarding Agency",
                "Awarding Sub Agency",
                "Award Type",
                "recipient_location_state_code",
                "recipient_location_city_name",
                "Place of Performance City Name",
                "Place of Performance State Code",
                "NAICS Code",
                "NAICS Description",
                "Award Description",
                "Product or Service Code",
                "PSC Description"
            ],
            "limit": per_page,
            "page": page
            }
        
        try:
            response = requests.post(
                USASPENDING_API,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                break
            
            data = response.json()
            
            if 'results' not in data:
                print(f"❌ No 'results' in response")
                break
            
            results = data['results']
            if not results:
                print(f"✅ No more results (reached end at page {page})")
                break
            
            print(f"   Received {len(results)} awards")
            
            # Parse awards
            for idx, award in enumerate(results, len(all_contracts) + 1):
                try:
                    # Extract available fields
                    award_id = award.get('Award ID', f'USASPEND-{idx}')
                    recipient = award.get('Recipient Name', 'Unknown Recipient')
                    amount = award.get('Award Amount', 0)
                    agency = award.get('Awarding Agency', 'Unknown Agency')
                    sub_agency = award.get('Awarding Sub Agency', '')
                    naics = award.get('NAICS Code', '')
                    naics_desc = award.get('NAICS Description', '')
                    psc_code = award.get('Product or Service Code', '')
                    psc_desc = award.get('PSC Description', '')
                    start_date = award.get('Start Date', '')
                    end_date = award.get('End Date', '')
                    city = award.get('Place of Performance City Name', '') or award.get('recipient_location_city_name', '')
                    state = award.get('Place of Performance State Code', 'VA')
                    
                    # Build location
                    location = f"{city}, {state}" if city else state
                    
                    # Build description from available data
                    desc_parts = []
                    if naics_desc:
                        desc_parts.append(f"NAICS: {naics_desc}")
                    if psc_desc:
                        desc_parts.append(f"Service: {psc_desc}")
                    if recipient:
                        desc_parts.append(f"Awarded to: {recipient}")
                    if start_date and end_date:
                        desc_parts.append(f"Period: {start_date} to {end_date}")
                    
                    description = " | ".join(desc_parts) if desc_parts else "Federal contract from USAspending.gov"
                    
                    # Format value
                    if amount:
                        value = f"${amount:,.0f}"
                    else:
                        value = "Amount not disclosed"
                    
                    # Build title
                    if naics_desc:
                        title = naics_desc[:100]
                    elif psc_desc:
                        title = psc_desc[:100]
                    else:
                        title = f"Contract {award_id}"
                    
                    contract = {
                        'title': title,
                        'agency': agency,
                        'department': sub_agency,
                        'location': location,
                        'value': value,
                        'deadline': None,  # Historical data doesn't have deadlines
                        'description': description,
                        'naics_code': str(naics) if naics else '',
                        'sam_gov_url': f"https://www.usaspending.gov/award/{award_id}" if award_id else '',
                        'notice_id': award_id,
                        'set_aside': '',
                        'posted_date': start_date if start_date else datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    all_contracts.append(contract)
                    
                except Exception as e:
                    print(f"   ❌ Error parsing award {idx}: {e}")
                    continue
            
            # Check if we should fetch more pages
            if len(all_contracts) >= max_results:
                print(f"✅ Reached max results ({max_results})")
                break
            
            if len(results) < per_page:
                print(f"✅ Received fewer than {per_page} results - end of data")
                break
            
            page += 1
            
        except requests.exceptions.Timeout:
            print("❌ Request timeout - API not responding")
            break
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            break
    
    print()
    print(f"✅ Successfully fetched {len(all_contracts)} total contracts")
    
    # Print sample
    if all_contracts:
        print("\n📋 Sample contracts:")
        for i, c in enumerate(all_contracts[:5], 1):
            print(f"   {i}. {c['title'][:60]}... ({c['value']})")
    
    return all_contracts

def filter_cleaning_contracts(contracts):
    """
    Filter contracts to focus on cleaning/janitorial services
    """
    print("\n🔍 Filtering for cleaning/janitorial contracts...")
    
    # Keywords to look for
    cleaning_keywords = [
        'clean', 'janitor', 'custodial', 'housekeep', 'sanitiz',
        'maint', 'facility', 'building service', 'floor care',
        'waste', 'carpet', 'window clean'
    ]
    
    # NAICS codes for facility services
    facility_naics = ['561', '5617', '56172', '56173', '56179']
    
    filtered = []
    for contract in contracts:
        # Check NAICS code
        naics = contract.get('naics_code', '')
        if any(naics.startswith(code) for code in facility_naics):
            filtered.append(contract)
            continue
        
        # Check title and description
        text = (contract.get('title', '') + ' ' + contract.get('description', '')).lower()
        if any(keyword in text for keyword in cleaning_keywords):
            filtered.append(contract)
    
    print(f"   Found {len(filtered)} cleaning-related contracts out of {len(contracts)} total")
    return filtered

def upload_to_database(contracts):
    """
    Upload contracts to database, replacing demo data
    """
    if not contracts:
        print("\n❌ No contracts to upload")
        return
    
    print(f"\n💾 Uploading {len(contracts)} contracts to database...")
    
    with app.app_context():
        # Remove demo data
        deleted = db.session.execute(text('''
            DELETE FROM federal_contracts WHERE description LIKE '%DEMO DATA%'
        ''')).rowcount
        
        if deleted > 0:
            print(f"   Removed {deleted} demo contracts")
        
        # Insert new contracts
        inserted = 0
        skipped = 0
        
        for contract in contracts:
            try:
                # Check if already exists
                existing = db.session.execute(text('''
                    SELECT COUNT(*) FROM federal_contracts WHERE notice_id = :notice_id
                '''), {'notice_id': contract['notice_id']}).scalar()
                
                if existing > 0:
                    skipped += 1
                    continue
                
                db.session.execute(text('''
                    INSERT INTO federal_contracts 
                    (title, agency, department, location, value, deadline, description, 
                     naics_code, sam_gov_url, notice_id, set_aside, posted_date)
                    VALUES (:title, :agency, :department, :location, :value, :deadline, 
                            :description, :naics_code, :sam_gov_url, :notice_id, 
                            :set_aside, :posted_date)
                '''), contract)
                inserted += 1
                
            except Exception as e:
                print(f"   ❌ Error inserting {contract['title'][:50]}: {e}")
        
        db.session.commit()
        print(f"\n✅ Upload complete!")
        print(f"   Inserted: {inserted} new contracts")
        print(f"   Skipped: {skipped} duplicates")
        print(f"   Total in database: {inserted + skipped}")

def main():
    """Main scraper execution"""
    print("\n🚀 Starting Data.gov contract scraper...\n")
    
    # Fetch contracts
    contracts = fetch_virginia_contracts(days_back=90, max_results=200)
    
    if not contracts:
        print("\n❌ No contracts fetched. Check API connection.")
        return
    
    # Filter for cleaning services
    cleaning_contracts = filter_cleaning_contracts(contracts)
    
    if not cleaning_contracts:
        print("\n⚠️  No cleaning contracts found in results")
        print("   Uploading all Virginia contracts instead...")
        cleaning_contracts = contracts[:50]  # Limit to 50 most recent
    
    # Upload to database
    upload_to_database(cleaning_contracts)
    
    print("\n" + "=" * 70)
    print("✅ Scraping complete! Refresh your federal contracts page.")
    print("=" * 70)

if __name__ == '__main__':
    main()
