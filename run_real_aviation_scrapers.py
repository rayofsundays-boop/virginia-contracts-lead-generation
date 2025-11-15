#!/usr/bin/env python3
"""
Run Real Aviation Scrapers
1. Remove fake/sample leads
2. Run aviation_scraper_v2.py (airport procurement, airlines, ground handlers)
3. Run aviation_airline_scraper.py (airline hubs and bases)
4. Save all real leads to database
"""

from app import app, db
from sqlalchemy import text
import sys

def clear_fake_aviation_leads():
    """Remove fake/sample aviation leads"""
    with app.app_context():
        try:
            print("🗑️  Removing fake/sample aviation leads...")
            result = db.session.execute(text("""
                DELETE FROM aviation_cleaning_leads 
                WHERE data_source = 'Manual seed data'
            """))
            db.session.commit()
            deleted_count = result.rowcount
            print(f"✅ Removed {deleted_count} fake leads")
            return deleted_count
        except Exception as e:
            print(f"❌ Error removing fake leads: {e}")
            db.session.rollback()
            return 0

def run_aviation_scraper_v2():
    """Run aviation_scraper_v2.py - Scrapes airport procurement pages"""
    try:
        print("\n🛫 Running Aviation Scraper V2 (Airport Procurement Pages)...")
        from aviation_scraper_v2 import scrape_all_v2
        
        # Scrape airports, airlines, and ground handlers
        results = scrape_all_v2(max_airports=10, max_airlines=5, max_ground_handlers=3)
        
        if results:
            print(f"✅ Found {len(results)} opportunities from Aviation Scraper V2")
            return results
        else:
            print("⚠️  No results from Aviation Scraper V2")
            return []
            
    except ImportError as e:
        print(f"❌ Aviation Scraper V2 not available: {e}")
        return []
    except Exception as e:
        print(f"❌ Error running Aviation Scraper V2: {e}")
        import traceback
        traceback.print_exc()
        return []

def run_airline_scraper():
    """Run aviation_airline_scraper.py - Scrapes airline hub pages"""
    try:
        print("\n✈️  Running Airline Hub Scraper...")
        from aviation_airline_scraper import scrape_all_airlines
        
        # Scrape all major airlines
        results = scrape_all_airlines(airlines_list=None)  # None = all airlines
        
        if results:
            print(f"✅ Found {len(results)} airline hub opportunities")
            return results
        else:
            print("⚠️  No results from Airline Hub Scraper")
            return []
            
    except ImportError as e:
        print(f"❌ Airline Hub Scraper not available: {e}")
        return []
    except Exception as e:
        print(f"❌ Error running Airline Hub Scraper: {e}")
        import traceback
        traceback.print_exc()
        return []

def save_leads_to_database(leads):
    """Save scraped leads to database"""
    with app.app_context():
        try:
            saved_count = 0
            for lead in leads:
                try:
                    # Extract lead data
                    company_name = lead.get('company_name', 'Unknown')[:200]
                    company_type = lead.get('company_type', lead.get('category', 'Aviation'))
                    city = lead.get('city', 'Unknown')
                    state = lead.get('state', 'Unknown')
                    
                    # Optional fields
                    aircraft_types = lead.get('aircraft_types', '')
                    fleet_size = lead.get('fleet_size')
                    contact_email = lead.get('contact_email', lead.get('email', ''))
                    contact_phone = lead.get('contact_phone', lead.get('phone', ''))
                    website_url = lead.get('website_url', lead.get('url', ''))
                    services_needed = lead.get('services_needed', lead.get('services', 'Aviation cleaning'))
                    estimated_value = lead.get('estimated_monthly_value', lead.get('value', ''))
                    notes = lead.get('notes', lead.get('description', ''))
                    data_source = lead.get('data_source', 'Web scraper')
                    
                    # Insert into database
                    db.session.execute(text("""
                        INSERT INTO aviation_cleaning_leads
                        (company_name, company_type, aircraft_types, fleet_size, city, state,
                         contact_phone, contact_email, website_url, services_needed,
                         estimated_monthly_value, notes, data_source, is_active)
                        VALUES
                        (:company_name, :company_type, :aircraft_types, :fleet_size, :city, :state,
                         :contact_phone, :contact_email, :website_url, :services_needed,
                         :estimated_monthly_value, :notes, :data_source, TRUE)
                        ON CONFLICT (company_name, city, state) DO UPDATE SET
                        contact_email = EXCLUDED.contact_email,
                        contact_phone = EXCLUDED.contact_phone,
                        website_url = EXCLUDED.website_url,
                        last_verified = CURRENT_TIMESTAMP
                    """), {
                        'company_name': company_name,
                        'company_type': company_type,
                        'aircraft_types': aircraft_types,
                        'fleet_size': fleet_size,
                        'city': city,
                        'state': state,
                        'contact_phone': contact_phone,
                        'contact_email': contact_email,
                        'website_url': website_url,
                        'services_needed': services_needed,
                        'estimated_monthly_value': estimated_value,
                        'notes': notes,
                        'data_source': data_source
                    })
                    saved_count += 1
                    print(f"  ✅ Saved: {company_name[:50]}")
                    
                except Exception as e:
                    print(f"  ⚠️ Error saving {company_name}: {e}")
                    continue
            
            db.session.commit()
            print(f"\n✅ Successfully saved {saved_count}/{len(leads)} real aviation leads")
            return saved_count
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            db.session.rollback()
            return 0

def main():
    """Main execution"""
    print("="*60)
    print("🛫 REAL AVIATION LEADS SCRAPER")
    print("="*60)
    
    # Step 1: Remove fake leads
    clear_fake_aviation_leads()
    
    # Step 2: Run scrapers
    all_leads = []
    
    # Run Aviation Scraper V2 (airport procurement)
    v2_results = run_aviation_scraper_v2()
    if v2_results:
        all_leads.extend(v2_results)
    
    # Run Airline Hub Scraper
    airline_results = run_airline_scraper()
    if airline_results:
        all_leads.extend(airline_results)
    
    # Step 3: Save to database
    if all_leads:
        print(f"\n📊 Total leads scraped: {len(all_leads)}")
        saved_count = save_leads_to_database(all_leads)
        
        # Verify final count
        with app.app_context():
            result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
            total = result.scalar()
            print(f"\n📈 Final database count: {total} real aviation leads")
    else:
        print("\n⚠️  No leads found from any scraper")
    
    print("\n" + "="*60)
    print("✅ SCRAPING COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
