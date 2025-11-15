"""
Nationwide Google API Lead Generation
Finds and imports commercial cleaning leads across all 50 US states
"""
from google_lead_generator import GoogleLeadGenerator
from app import app, db
from sqlalchemy import text

# Top 3 cities per state for comprehensive coverage
US_CITIES = {
    'AL': [('Birmingham', 12), ('Montgomery', 10), ('Mobile', 10)],
    'AK': [('Anchorage', 15), ('Fairbanks', 10), ('Juneau', 8)],
    'AZ': [('Phoenix', 15), ('Tucson', 12), ('Mesa', 10)],
    'AR': [('Little Rock', 12), ('Fort Smith', 10), ('Fayetteville', 10)],
    'CA': [('Los Angeles', 15), ('San Francisco', 15), ('San Diego', 15)],
    'CO': [('Denver', 15), ('Colorado Springs', 12), ('Aurora', 10)],
    'CT': [('Hartford', 12), ('New Haven', 10), ('Stamford', 10)],
    'DE': [('Wilmington', 10), ('Dover', 8), ('Newark', 8)],
    'FL': [('Miami', 15), ('Orlando', 15), ('Tampa', 15)],
    'GA': [('Atlanta', 15), ('Savannah', 12), ('Augusta', 10)],
    'HI': [('Honolulu', 12), ('Hilo', 8), ('Kailua', 8)],
    'ID': [('Boise', 12), ('Meridian', 10), ('Idaho Falls', 8)],
    'IL': [('Chicago', 15), ('Aurora', 12), ('Naperville', 10)],
    'IN': [('Indianapolis', 15), ('Fort Wayne', 12), ('Evansville', 10)],
    'IA': [('Des Moines', 12), ('Cedar Rapids', 10), ('Davenport', 10)],
    'KS': [('Wichita', 12), ('Overland Park', 10), ('Kansas City', 12)],
    'KY': [('Louisville', 12), ('Lexington', 12), ('Bowling Green', 10)],
    'LA': [('New Orleans', 12), ('Baton Rouge', 12), ('Shreveport', 10)],
    'ME': [('Portland', 10), ('Lewiston', 8), ('Bangor', 8)],
    'MD': [('Baltimore', 15), ('Annapolis', 10), ('Rockville', 10)],
    'MA': [('Boston', 15), ('Worcester', 12), ('Springfield', 10)],
    'MI': [('Detroit', 15), ('Grand Rapids', 12), ('Warren', 10)],
    'MN': [('Minneapolis', 15), ('Saint Paul', 12), ('Rochester', 10)],
    'MS': [('Jackson', 12), ('Gulfport', 10), ('Southaven', 8)],
    'MO': [('Kansas City', 15), ('Saint Louis', 15), ('Springfield', 10)],
    'MT': [('Billings', 10), ('Missoula', 8), ('Great Falls', 8)],
    'NE': [('Omaha', 12), ('Lincoln', 12), ('Bellevue', 8)],
    'NV': [('Las Vegas', 15), ('Reno', 12), ('Henderson', 10)],
    'NH': [('Manchester', 10), ('Nashua', 8), ('Concord', 8)],
    'NJ': [('Newark', 15), ('Jersey City', 12), ('Paterson', 10)],
    'NM': [('Albuquerque', 12), ('Las Cruces', 10), ('Santa Fe', 10)],
    'NY': [('New York City', 15), ('Buffalo', 15), ('Rochester', 12)],
    'NC': [('Charlotte', 15), ('Raleigh', 15), ('Greensboro', 12)],
    'ND': [('Fargo', 10), ('Bismarck', 8), ('Grand Forks', 8)],
    'OH': [('Columbus', 15), ('Cleveland', 15), ('Cincinnati', 15)],
    'OK': [('Oklahoma City', 12), ('Tulsa', 12), ('Norman', 10)],
    'OR': [('Portland', 15), ('Eugene', 12), ('Salem', 10)],
    'PA': [('Philadelphia', 15), ('Pittsburgh', 15), ('Allentown', 12)],
    'RI': [('Providence', 12), ('Warwick', 8), ('Cranston', 8)],
    'SC': [('Charleston', 12), ('Columbia', 12), ('Greenville', 10)],
    'SD': [('Sioux Falls', 10), ('Rapid City', 8), ('Aberdeen', 8)],
    'TN': [('Nashville', 15), ('Memphis', 15), ('Knoxville', 12)],
    'TX': [('Houston', 15), ('Dallas', 15), ('Austin', 15)],
    'UT': [('Salt Lake City', 12), ('Provo', 10), ('West Valley City', 10)],
    'VT': [('Burlington', 10), ('South Burlington', 8), ('Rutland', 8)],
    'VA': [('Virginia Beach', 15), ('Richmond', 15), ('Norfolk', 12)],
    'WA': [('Seattle', 15), ('Spokane', 12), ('Tacoma', 12)],
    'WV': [('Charleston', 10), ('Huntington', 8), ('Morgantown', 8)],
    'WI': [('Milwaukee', 15), ('Madison', 12), ('Green Bay', 10)],
    'WY': [('Cheyenne', 8), ('Casper', 8), ('Laramie', 8)],
    'DC': [('Washington', 15)]
}

def generate_nationwide_leads():
    """Generate leads from all 50 states + DC"""
    
    with app.app_context():
        print("\n🇺🇸 NATIONWIDE GOOGLE API LEAD GENERATION")
        print("=" * 70)
        print(f"📍 Searching {len(US_CITIES)} states/territories")
        print(f"🏙️  Total cities: {sum(len(cities) for cities in US_CITIES.values())}")
        print("=" * 70)
        
        # Initialize generator
        try:
            generator = GoogleLeadGenerator()
            print("✅ Google API initialized\n")
        except Exception as e:
            print(f"❌ Error initializing Google API: {e}")
            print("⚠️  Make sure GOOGLE_API_KEY is set in environment variables")
            return
        
        all_leads = []
        commercial_count = 0
        property_mgmt_count = 0
        aviation_count = 0
        states_completed = 0
        
        # Process each state
        for state_code, cities in sorted(US_CITIES.items()):
            print(f"\n{'='*70}")
            print(f"📍 STATE: {state_code} ({len(cities)} cities)")
            print(f"{'='*70}")
            
            state_leads = 0
            
            for idx, (city, radius) in enumerate(cities, 1):
                print(f"\n🔍 [{idx}/{len(cities)}] {city}, {state_code} (radius: {radius} miles)")
                
                try:
                    # Commercial properties
                    leads = generator.find_commercial_properties(city, state_code, radius_miles=radius)
                    print(f"   ✅ Commercial properties: {len(leads)}")
                    all_leads.extend(leads)
                    commercial_count += len(leads)
                    state_leads += len(leads)
                    
                    # Property managers
                    pm_leads = generator.find_property_managers(city, state_code, radius_miles=radius)
                    print(f"   ✅ Property managers: {len(pm_leads)}")
                    all_leads.extend(pm_leads)
                    property_mgmt_count += len(pm_leads)
                    state_leads += len(pm_leads)
                    
                    # Aviation facilities (larger radius)
                    aviation_leads = generator.find_aviation_facilities(city, state_code, radius_miles=radius*2)
                    print(f"   ✅ Aviation facilities: {len(aviation_leads)}")
                    all_leads.extend(aviation_leads)
                    aviation_count += len(aviation_leads)
                    state_leads += len(aviation_leads)
                    
                except Exception as e:
                    print(f"   ⚠️  Error searching {city}: {e}")
                    continue
            
            states_completed += 1
            print(f"\n✅ {state_code} COMPLETE: {state_leads} leads")
            print(f"📊 Progress: {states_completed}/{len(US_CITIES)} states ({(states_completed/len(US_CITIES)*100):.1f}%)")
        
        print(f"\n{'='*70}")
        print(f"📊 NATIONWIDE TOTALS")
        print(f"{'='*70}")
        print(f"🏢 Commercial properties: {commercial_count}")
        print(f"🏘️  Property managers: {property_mgmt_count}")
        print(f"✈️  Aviation facilities: {aviation_count}")
        print(f"📍 States covered: {states_completed}/{len(US_CITIES)}")
        print(f"🎯 TOTAL LEADS FOUND: {len(all_leads)}")
        print(f"{'='*70}")
        
        # Show sample leads by category
        print("\n📋 SAMPLE LEADS BY CATEGORY:")
        
        # Commercial
        commercial_samples = [l for l in all_leads if l.get('lead_type') != 'property_manager' and l.get('lead_type') != 'aviation'][:10]
        if commercial_samples:
            print(f"\n🏢 COMMERCIAL PROPERTIES ({len(commercial_samples)} shown):")
            for lead in commercial_samples:
                print(f"   • {lead['company_name']} - {lead.get('category', 'N/A')}")
                print(f"     📍 {lead['city']}, {lead['state']}")
                print(f"     📞 {lead.get('phone', 'N/A')}")
        
        # Property Management
        pm_samples = [l for l in all_leads if l.get('lead_type') == 'property_manager'][:5]
        if pm_samples:
            print(f"\n🏘️  PROPERTY MANAGERS ({len(pm_samples)} shown):")
            for lead in pm_samples:
                print(f"   • {lead['company_name']}")
                print(f"     📍 {lead['city']}, {lead['state']}")
                print(f"     ⭐ {lead.get('rating', 'N/A')}/5")
        
        # Aviation
        aviation_samples = [l for l in all_leads if l.get('lead_type') == 'aviation'][:5]
        if aviation_samples:
            print(f"\n✈️  AVIATION FACILITIES ({len(aviation_samples)} shown):")
            for lead in aviation_samples:
                print(f"   • {lead['company_name']} - {lead.get('category', 'N/A')}")
                print(f"     📍 {lead['city']}, {lead['state']}")
                print(f"     📞 {lead.get('phone', 'N/A')}")
        
        # Import to database
        print(f"\n{'='*70}")
        print(f"💾 IMPORTING TO DATABASE...")
        print(f"{'='*70}")
        
        saved_count = 0
        duplicate_count = 0
        error_count = 0
        
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
                    'special_requirements': f"Rating: {lead.get('rating', 'N/A')}/5 ({lead.get('total_ratings', 0)} reviews). Website: {lead.get('website', 'N/A')}. Google Place ID: {lead.get('place_id', 'N/A')}. Lead type: {lead.get('lead_type', 'commercial')}"
                })
                db.session.commit()
                saved_count += 1
                
                # Progress indicator every 50 saves
                if saved_count % 50 == 0:
                    print(f"   💾 Saved {saved_count} leads so far...")
                
            except Exception as e:
                error_count += 1
                db.session.rollback()
                if error_count <= 5:  # Only show first 5 errors
                    print(f"   ⚠️  Error saving {lead['company_name']}: {str(e)[:100]}")
                continue
        
        print(f"\n{'='*70}")
        print(f"✅ IMPORT COMPLETE!")
        print(f"{'='*70}")
        print(f"📥 New leads saved: {saved_count}")
        print(f"🔄 Duplicates skipped: {duplicate_count}")
        print(f"❌ Errors: {error_count}")
        print(f"📊 Total processed: {len(all_leads)}")
        print(f"{'='*70}\n")

if __name__ == '__main__':
    generate_nationwide_leads()
