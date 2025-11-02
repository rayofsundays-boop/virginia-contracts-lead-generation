#!/usr/bin/env python3
"""
Migration script to add commercial_opportunities table and populate with data
"""

from app import app, db
from sqlalchemy import text

def run_migration():
    """Add commercial_opportunities table and populate with all commercial leads"""
    
    with app.app_context():
        print("🔧 Starting migration: Adding commercial_opportunities table...")
        
        try:
            # Check if table already exists
            result = db.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='commercial_opportunities'"
            )).fetchone()
            
            if result:
                print("✅ Table 'commercial_opportunities' already exists")
                # Check count
                count = db.session.execute(text("SELECT COUNT(*) FROM commercial_opportunities")).scalar()
                print(f"   Current records: {count}")
                
                if count > 0:
                    user_input = input("⚠️  Table has data. Do you want to clear and repopulate? (yes/no): ")
                    if user_input.lower() != 'yes':
                        print("❌ Migration cancelled")
                        return
                    
                    # Clear existing data
                    db.session.execute(text("DELETE FROM commercial_opportunities"))
                    db.session.commit()
                    print("🗑️  Cleared existing data")
            else:
                # Create the table
                print("📝 Creating commercial_opportunities table...")
                db.session.execute(text('''
                    CREATE TABLE commercial_opportunities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        business_name TEXT NOT NULL,
                        business_type TEXT,
                        location TEXT,
                        square_footage INTEGER,
                        monthly_value REAL,
                        frequency TEXT,
                        services_needed TEXT,
                        special_requirements TEXT,
                        description TEXT,
                        contact_name TEXT,
                        contact_email TEXT,
                        contact_phone TEXT,
                        website_url TEXT,
                        size TEXT,
                        contact_type TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                '''))
                db.session.commit()
                print("✅ Table created successfully")
            
            # Now populate with all commercial opportunities
            print("\n📊 Populating commercial opportunities...")
            
            # ALL VIRGINIA COMMERCIAL OPPORTUNITIES (Hampton Roads + NoVA + Richmond)
            commercial_opportunities = [
                # HAMPTON ROADS - Hampton
                {'business_name': 'Sentara Hampton General Hospital', 'business_type': 'Hospital', 'location': 'Hampton, VA', 'square_footage': 120000, 'monthly_value': 35000, 'frequency': 'Daily', 'services_needed': 'Healthcare facility cleaning, infection control, terminal cleaning', 'description': 'Major hospital seeking comprehensive environmental services with Joint Commission compliance.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.sentara.com'},
                {'business_name': 'Peninsula Town Center', 'business_type': 'Shopping Center', 'location': 'Hampton, VA', 'square_footage': 450000, 'monthly_value': 28000, 'frequency': 'Daily', 'services_needed': 'Retail common area cleaning, restroom services, special event cleanup', 'description': 'Major shopping center requiring daily maintenance and weekend deep cleaning.', 'size': 'Large', 'contact_type': 'Bid', 'website_url': None},
                {'business_name': 'Langley Federal Credit Union HQ', 'business_type': 'Corporate Office', 'location': 'Hampton, VA', 'square_footage': 85000, 'monthly_value': 18000, 'frequency': 'Daily', 'services_needed': 'Office cleaning, floor care, window washing', 'description': 'Corporate headquarters requiring professional office cleaning services.', 'size': 'Medium', 'contact_type': 'Direct', 'website_url': 'https://www.lfcu.com'},
                
                # HAMPTON ROADS - Norfolk
                {'business_name': 'Sentara Norfolk General Hospital', 'business_type': 'Hospital', 'location': 'Norfolk, VA', 'square_footage': 300000, 'monthly_value': 75000, 'frequency': 'Daily', 'services_needed': 'Full hospital environmental services, ICU cleaning, surgical suite maintenance', 'description': 'Level 1 trauma center requiring 24/7 environmental services with specialized training.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.sentara.com'},
                {'business_name': 'MacArthur Center', 'business_type': 'Shopping Mall', 'location': 'Norfolk, VA', 'square_footage': 750000, 'monthly_value': 45000, 'frequency': 'Daily', 'services_needed': 'Mall common areas, food court, restrooms, parking garage', 'description': 'Premier shopping destination requiring comprehensive cleaning services.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': None},
                {'business_name': 'Dominion Tower', 'business_type': 'Class A Office Building', 'location': 'Norfolk, VA', 'square_footage': 500000, 'monthly_value': 55000, 'frequency': 'Daily', 'services_needed': 'Multi-tenant office tower cleaning, high-rise window washing', 'description': 'Downtown Norfolk\'s premier office tower seeking professional janitorial services.', 'size': 'Large', 'contact_type': 'Bid', 'website_url': None},
                {'business_name': 'Norfolk Marriott Waterside', 'business_type': 'Hotel', 'location': 'Norfolk, VA', 'square_footage': 180000, 'monthly_value': 32000, 'frequency': 'Daily', 'services_needed': 'Hotel housekeeping, banquet/event cleaning, public space maintenance', 'description': 'Full-service waterfront hotel requiring comprehensive cleaning services.', 'size': 'Large', 'contact_type': 'Direct', 'website_url': 'https://www.marriott.com'},
                
                # HAMPTON ROADS - Virginia Beach
                {'business_name': 'Sentara Virginia Beach General', 'business_type': 'Hospital', 'location': 'Virginia Beach, VA', 'square_footage': 250000, 'monthly_value': 65000, 'frequency': 'Daily', 'services_needed': 'Hospital environmental services, patient room cleaning, OR suite maintenance', 'description': 'Major hospital requiring Joint Commission compliant cleaning services.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.sentara.com'},
                {'business_name': 'Hilton Virginia Beach Oceanfront', 'business_type': 'Hotel', 'location': 'Virginia Beach, VA', 'square_footage': 220000, 'monthly_value': 38000, 'frequency': 'Daily', 'services_needed': 'Full hotel housekeeping, conference center, restaurant cleaning', 'description': 'Oceanfront resort requiring year-round comprehensive cleaning services.', 'size': 'Large', 'contact_type': 'Direct', 'website_url': 'https://www.hilton.com'},
                {'business_name': 'Town Center Virginia Beach', 'business_type': 'Mixed-Use Development', 'location': 'Virginia Beach, VA', 'square_footage': 600000, 'monthly_value': 42000, 'frequency': 'Daily', 'services_needed': 'Retail, dining, office, and residential common area cleaning', 'description': 'Premier mixed-use development requiring comprehensive property services.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': None},
                {'business_name': 'Pembroke Office Park', 'business_type': 'Office Park', 'location': 'Virginia Beach, VA', 'square_footage': 400000, 'monthly_value': 35000, 'frequency': 'Daily', 'services_needed': 'Multi-building office park cleaning and property maintenance', 'description': 'Major office park with multiple tenants requiring coordinated cleaning services.', 'size': 'Large', 'contact_type': 'Bid', 'website_url': None},
                
                # HAMPTON ROADS - Newport News
                {'business_name': 'Riverside Regional Medical Center', 'business_type': 'Hospital', 'location': 'Newport News, VA', 'square_footage': 200000, 'monthly_value': 55000, 'frequency': 'Daily', 'services_needed': 'Healthcare environmental services, infection prevention, specialty unit cleaning', 'description': 'Regional medical center requiring comprehensive environmental services.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.rivhs.com'},
                {'business_name': 'City Center at Oyster Point', 'business_type': 'Mixed-Use Development', 'location': 'Newport News, VA', 'square_footage': 350000, 'monthly_value': 28000, 'frequency': 'Daily', 'services_needed': 'Retail, restaurant, office, and residential common areas', 'description': 'Growing mixed-use development requiring professional property services.', 'size': 'Large', 'contact_type': 'Bid', 'website_url': None},
                
                # RICHMOND METRO - Richmond City
                {'business_name': 'VCU Health System', 'business_type': 'Hospital', 'location': 'Richmond, VA', 'square_footage': 850000, 'monthly_value': 195000, 'frequency': 'Daily', 'services_needed': 'Academic medical center cleaning, patient care areas, research labs, surgical suites', 'description': 'Flagship academic medical center - Level 1 trauma center with 865+ beds. Requires 24/7 environmental services with specialized protocols for OR, ICU, NICU, and research facilities. Joint Commission and Magnet hospital standards.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.vcuhealth.org'},
                {'business_name': 'CJW Medical Center', 'business_type': 'Hospital', 'location': 'Richmond, VA', 'square_footage': 520000, 'monthly_value': 125000, 'frequency': 'Daily', 'services_needed': 'Two-campus hospital cleaning, emergency services, surgical centers, patient rooms', 'description': 'Two hospital campuses (Chippenham and Johnston-Willis) with 700+ combined beds. Comprehensive environmental services for emergency departments, surgical centers, ICUs, and patient care areas.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.cjwmedical.com'},
                {'business_name': 'HCA Henrico Doctors\' Hospital', 'business_type': 'Hospital', 'location': 'Henrico, VA', 'square_footage': 450000, 'monthly_value': 108000, 'frequency': 'Daily', 'services_needed': 'Hospital environmental services, patient care, specialty units, surgical services', 'description': '340-bed regional medical center with Forest and Parham campuses. Requires infection prevention protocols, terminal cleaning, and specialty unit maintenance.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://henricodoctors.com'},
                {'business_name': 'Bon Secours St. Mary\'s Hospital', 'business_type': 'Hospital', 'location': 'Richmond, VA', 'square_footage': 380000, 'monthly_value': 92000, 'frequency': 'Daily', 'services_needed': 'Catholic health system facility cleaning, patient care, emergency services', 'description': '391-bed hospital part of Bon Secours Mercy Health system. Comprehensive environmental services with emphasis on patient safety and infection control.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.bonsecours.com'},
                
                {'business_name': 'Short Pump Town Center', 'business_type': 'Shopping Center', 'location': 'Henrico, VA', 'square_footage': 1400000, 'monthly_value': 115000, 'frequency': 'Daily', 'services_needed': 'Major retail mall cleaning, food court, restrooms, common areas, parking structures', 'description': 'Virginia\'s premier shopping destination with 1.4M sq ft and 140+ stores. Requires comprehensive mall maintenance, food court deep cleaning, restroom services, and special event support.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.simon.com/mall/short-pump-town-center'},
                {'business_name': 'Regency Square Mall', 'business_type': 'Shopping Center', 'location': 'Richmond, VA', 'square_footage': 750000, 'monthly_value': 65000, 'frequency': 'Daily', 'services_needed': 'Indoor mall cleaning, common areas, restrooms, food court maintenance', 'description': 'Historic Richmond shopping center requiring daily maintenance and periodic deep cleaning of common areas and tenant spaces.', 'size': 'Large', 'contact_type': 'Bid', 'website_url': None},
                {'business_name': 'Stony Point Fashion Park', 'business_type': 'Shopping Center', 'location': 'Richmond, VA', 'square_footage': 550000, 'monthly_value': 48000, 'frequency': 'Daily', 'services_needed': 'Upscale outdoor shopping center cleaning, common areas, dining district', 'description': 'Upscale open-air shopping and dining destination. Requires exterior and interior common area maintenance with focus on premium appearance.', 'size': 'Large', 'contact_type': 'Bid', 'website_url': None},
                
                {'business_name': 'Capital One Headquarters', 'business_type': 'Corporate Office', 'location': 'Richmond, VA', 'square_footage': 1200000, 'monthly_value': 135000, 'frequency': 'Daily', 'services_needed': 'Fortune 500 corporate campus cleaning, office towers, data centers, cafeterias, conference centers', 'description': 'Fortune 500 financial services headquarters with multiple towers and 7,000+ employees. Requires executive-level office cleaning, 24/7 data center services, and campus-wide facility maintenance.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.capitalone.com'},
                {'business_name': 'Dominion Energy Headquarters', 'business_type': 'Corporate Office', 'location': 'Richmond, VA', 'square_footage': 850000, 'monthly_value': 88000, 'frequency': 'Daily', 'services_needed': 'Energy company headquarters cleaning, office towers, executive floors, trading floors', 'description': 'Fortune 500 energy company headquarters. Downtown office complex requiring professional corporate cleaning with emphasis on executive suites and trading floor areas.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.dominionenergy.com'},
                {'business_name': 'Altria Corporate Center', 'business_type': 'Corporate Office', 'location': 'Richmond, VA', 'square_footage': 920000, 'monthly_value': 92000, 'frequency': 'Daily', 'services_needed': 'Fortune 500 headquarters cleaning, office buildings, executive spaces, visitor centers', 'description': 'Fortune 500 company headquarters complex. Comprehensive facility services including office cleaning, executive floor maintenance, and visitor center presentation standards.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.altria.com'},
                {'business_name': 'CoStar Group Office', 'business_type': 'Corporate Office', 'location': 'Richmond, VA', 'square_footage': 280000, 'monthly_value': 42000, 'frequency': 'Daily', 'services_needed': 'Technology company office cleaning, open floor plans, conference rooms', 'description': 'Commercial real estate information and analytics company. Modern tech office requiring flexible cleaning schedules and tech-friendly maintenance.', 'size': 'Large', 'contact_type': 'Direct', 'website_url': 'https://www.costargroup.com'},
                
                {'business_name': 'James Center', 'business_type': 'Office Building', 'location': 'Richmond, VA', 'square_footage': 1100000, 'monthly_value': 95000, 'frequency': 'Daily', 'services_needed': 'Three-tower Class A office complex, multi-tenant cleaning, retail spaces', 'description': 'Iconic downtown Richmond office complex with three interconnected towers. Multi-tenant environment requiring coordinated building-wide services and retail space maintenance.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': None},
                {'business_name': 'Riverfront Plaza', 'business_type': 'Office Building', 'location': 'Richmond, VA', 'square_footage': 750000, 'monthly_value': 68000, 'frequency': 'Daily', 'services_needed': 'Twin tower office building cleaning, plaza maintenance, parking structure', 'description': 'Two distinctive towers on Richmond riverfront. Class A office space requiring premium cleaning standards and plaza area maintenance.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': None},
                {'business_name': 'Innsbrook Corporate Center', 'business_type': 'Office Park', 'location': 'Henrico, VA', 'square_footage': 2500000, 'monthly_value': 185000, 'frequency': 'Daily', 'services_needed': 'Largest suburban office park on East Coast - 50+ buildings, multi-tenant services', 'description': '2,500-acre office park with 50+ buildings and 16,000+ employees. Largest suburban office development on East Coast. Requires coordinated multi-building cleaning services and common area maintenance.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': None},
                
                {'business_name': 'The Jefferson Hotel', 'business_type': 'Hotel', 'location': 'Richmond, VA', 'square_footage': 280000, 'monthly_value': 62000, 'frequency': 'Daily', 'services_needed': 'Historic luxury hotel cleaning, guest rooms, ballrooms, fine dining restaurants, spa', 'description': 'Five-star historic luxury hotel (est. 1895). Requires white-glove service standards for 181 guest rooms, grand ballrooms, upscale restaurants, and full-service spa.', 'size': 'Large', 'contact_type': 'Direct', 'website_url': 'https://www.jeffersonhotel.com'},
                {'business_name': 'Omni Richmond Hotel', 'business_type': 'Hotel', 'location': 'Richmond, VA', 'square_footage': 425000, 'monthly_value': 52000, 'frequency': 'Daily', 'services_needed': 'Full-service hotel cleaning, 361 rooms, conference facilities, restaurants', 'description': 'Downtown convention hotel with 361 guest rooms and extensive meeting space. Requires comprehensive housekeeping and event cleanup services.', 'size': 'Large', 'contact_type': 'Direct', 'website_url': 'https://www.omnihotels.com'},
                {'business_name': 'The Graduate Richmond', 'business_type': 'Hotel', 'location': 'Richmond, VA', 'square_footage': 185000, 'monthly_value': 28000, 'frequency': 'Daily', 'services_needed': 'Boutique hotel cleaning, guest rooms, restaurant, rooftop bar, meeting spaces', 'description': 'Boutique hotel near VCU with 73 unique rooms, rooftop bar, and restaurant. Requires attention to design details and modern hospitality standards.', 'size': 'Medium', 'contact_type': 'Direct', 'website_url': 'https://www.graduatehotels.com'},
                
                {'business_name': 'Virginia Biotechnology Research Park', 'business_type': 'Research/Tech Park', 'location': 'Richmond, VA', 'square_footage': 650000, 'monthly_value': 52000, 'frequency': 'Daily', 'services_needed': 'Bioscience research facility cleaning, labs with specialized protocols, clean rooms', 'description': '34-acre research park with biotech labs and research facilities. Requires specialized cleaning for laboratory spaces, clean rooms, and research environments with strict contamination protocols.', 'size': 'Enterprise', 'contact_type': 'Bid', 'website_url': 'https://www.vabiotech.com'},
                {'business_name': 'White Oak Technology Park', 'business_type': 'Technology Park', 'location': 'Henrico, VA', 'square_footage': 580000, 'monthly_value': 48000, 'frequency': 'Daily', 'services_needed': 'Technology campus cleaning, office spaces, data centers, R&D facilities', 'description': 'Emerging technology park with mix of office and R&D facilities. Requires flexible cleaning schedules accommodating 24/7 tech operations.', 'size': 'Large', 'contact_type': 'Bid', 'website_url': None},
            ]
            
            # Insert all opportunities
            inserted = 0
            for opp in commercial_opportunities:
                try:
                    db.session.execute(text('''
                        INSERT INTO commercial_opportunities 
                        (business_name, business_type, location, square_footage, monthly_value, 
                         frequency, services_needed, description, size, contact_type, website_url, status)
                        VALUES 
                        (:business_name, :business_type, :location, :square_footage, :monthly_value,
                         :frequency, :services_needed, :description, :size, :contact_type, :website_url, 'active')
                    '''), opp)
                    inserted += 1
                except Exception as e:
                    print(f"   ⚠️  Error inserting {opp['business_name']}: {e}")
            
            db.session.commit()
            
            print(f"\n✅ Migration completed successfully!")
            print(f"   📊 Inserted {inserted} commercial opportunities")
            print(f"\n🎯 All leads are now available at /customer-leads")
            
            # Show summary
            total_count = db.session.execute(text("SELECT COUNT(*) FROM commercial_opportunities")).scalar()
            print(f"\n📈 Database Summary:")
            print(f"   - Commercial opportunities: {total_count}")
            
            # Show breakdown by location
            print(f"\n📍 Breakdown by Region:")
            regions = db.session.execute(text("""
                SELECT 
                    CASE 
                        WHEN location LIKE '%Hampton%' OR location LIKE '%Norfolk%' OR 
                             location LIKE '%Virginia Beach%' OR location LIKE '%Newport News%' 
                        THEN 'Hampton Roads'
                        WHEN location LIKE '%Richmond%' OR location LIKE '%Henrico%' OR 
                             location LIKE '%Chesterfield%'
                        THEN 'Richmond Metro'
                        ELSE 'Other'
                    END as region,
                    COUNT(*) as count
                FROM commercial_opportunities
                GROUP BY region
            """)).fetchall()
            
            for region in regions:
                print(f"   - {region[0]}: {region[1]} opportunities")
                
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()


if __name__ == '__main__':
    run_migration()
