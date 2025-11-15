"""
Run Google API Lead Generation
Finds and imports commercial cleaning leads automatically
"""
from google_lead_generator import GoogleLeadGenerator
from app import app, db
from sqlalchemy import text

def generate_and_import_google_leads():
    """Generate leads from Google and import to database"""
    
    with app.app_context():
        print("\n🚀 Starting Google API Lead Generation...")
        print("=" * 60)
        
        # Initialize generator
        try:
            generator = GoogleLeadGenerator()
            print("✅ Google API initialized")
        except Exception as e:
            print(f"❌ Error initializing Google API: {e}")
            print("⚠️  Make sure GOOGLE_API_KEY is set in environment variables")
            return
        
        # Cities to search
        cities = [
            ('Virginia Beach', 'VA', 15),
            ('Norfolk', 'VA', 10),
            ('Hampton', 'VA', 10),
            ('Newport News', 'VA', 10),
            ('Chesapeake', 'VA', 10)
        ]
        
        all_leads = []
        
        # Generate leads for each city
        for city, state, radius in cities:
            print(f"\n🔍 Searching {city}, {state} (radius: {radius} miles)...")
            
            try:
                leads = generator.find_commercial_properties(city, state, radius_miles=radius)
                print(f"   ✅ Found {len(leads)} commercial properties")
                all_leads.extend(leads)
                
                # Also get property managers
                pm_leads = generator.find_property_managers(city, state, radius_miles=radius)
                print(f"   ✅ Found {len(pm_leads)} property management companies")
                all_leads.extend(pm_leads)
                
                # Get aviation facilities (use larger radius)
                aviation_leads = generator.find_aviation_facilities(city, state, radius_miles=radius*2)
                print(f"   ✅ Found {len(aviation_leads)} aviation facilities")
                all_leads.extend(aviation_leads)
                
            except Exception as e:
                print(f"   ⚠️  Error searching {city}: {e}")
                continue
        
        print(f"\n📊 Total leads found: {len(all_leads)}")
        print("=" * 60)
        
        # Show sample leads
        print("\n📋 Sample leads:")
        for lead in all_leads[:15]:
            print(f"\n   • {lead['company_name']}")
            print(f"     Category: {lead.get('category', 'N/A')}")
            print(f"     Location: {lead['city']}, {lead['state']}")
            print(f"     Phone: {lead.get('phone', 'N/A')}")
            print(f"     Rating: {lead.get('rating', 'N/A')}/5")
        
        # Import to database
        print(f"\n💾 Importing leads to database...")
        saved_count = 0
        duplicate_count = 0
        
        for lead in all_leads:
            try:
                # Check if lead already exists
                existing = db.session.execute(text("""
                    SELECT id FROM commercial_lead_requests 
                    WHERE business_name = :business_name AND city = :city
                """), {
                    'business_name': lead['company_name'],
                    'city': lead['city']
                }).fetchone()
                
                if existing:
                    duplicate_count += 1
                    continue
                
                # Insert new lead
                db.session.execute(text("""
                    INSERT INTO commercial_lead_requests
                    (business_name, contact_name, email, phone, address, city, state,
                     business_type, square_footage, frequency, services_needed, special_requirements,
                     status, created_at)
                    VALUES
                    (:business_name, :contact_name, :email, :phone, :address, :city, :state,
                     :business_type, :square_footage, :frequency, :services_needed, :special_requirements,
                     'open', CURRENT_TIMESTAMP)
                """), {
                    'business_name': lead['company_name'],
                    'contact_name': 'Google Places',
                    'email': 'google-lead@contractlink.ai',
                    'phone': lead.get('phone', 'N/A'),
                    'address': lead.get('address', 'N/A'),
                    'city': lead['city'],
                    'state': lead['state'],
                    'business_type': lead.get('category', 'Commercial Property'),
                    'square_footage': lead.get('estimated_sqft', 0),
                    'frequency': 'To Be Determined',
                    'services_needed': 'Commercial Cleaning Services',
                    'special_requirements': f"Rating: {lead.get('rating', 'N/A')}/5 ({lead.get('total_ratings', 0)} reviews). Website: {lead.get('website', 'N/A')}. Google Place ID: {lead.get('place_id', 'N/A')}"
                })
                db.session.commit()
                saved_count += 1
                
            except Exception as e:
                print(f"⚠️  Error saving {lead['company_name']}: {e}")
                db.session.rollback()
                continue
        
        print(f"\n✅ Import complete!")
        print(f"   📥 New leads saved: {saved_count}")
        print(f"   🔄 Duplicates skipped: {duplicate_count}")
        print(f"   📊 Total processed: {len(all_leads)}")
        print("\n" + "=" * 60)

if __name__ == '__main__':
    generate_and_import_google_leads()
