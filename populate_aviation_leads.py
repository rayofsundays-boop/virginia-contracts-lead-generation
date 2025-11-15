#!/usr/bin/env python3
"""
Populate aviation_cleaning_leads table with sample data
Run this to add aviation opportunities to the database
"""

from app import app, db
from sqlalchemy import text

def populate_aviation_leads():
    """Add sample aviation cleaning leads to database"""
    with app.app_context():
        try:
            # First, ensure the table exists
            print("🔧 Creating aviation_cleaning_leads table if it doesn't exist...")
            db.session.execute(text('''CREATE TABLE IF NOT EXISTS aviation_cleaning_leads
                     (id SERIAL PRIMARY KEY,
                      company_name TEXT NOT NULL,
                      company_type TEXT NOT NULL,
                      aircraft_types TEXT,
                      fleet_size INTEGER,
                      city TEXT NOT NULL,
                      state TEXT NOT NULL,
                      address TEXT,
                      contact_name TEXT,
                      contact_title TEXT,
                      contact_email TEXT,
                      contact_phone TEXT,
                      website_url TEXT,
                      services_needed TEXT,
                      estimated_monthly_value TEXT,
                      current_contract_status TEXT,
                      notes TEXT,
                      data_source TEXT,
                      discovered_via TEXT DEFAULT 'ai_scraper',
                      discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      last_verified TIMESTAMP,
                      is_active BOOLEAN DEFAULT TRUE,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      UNIQUE(company_name, city, state))'''))
            db.session.commit()
            print("✅ Table created successfully")
            
        except Exception as e:
            print(f"⚠️ Table creation warning (may already exist): {e}")
            db.session.rollback()
        
        try:
            # Sample aviation leads data
            aviation_leads = [
                {
                    'company_name': 'Delta Air Lines - ATL Hub',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Boeing 737, Airbus A320, Boeing 757',
                    'fleet_size': 200,
                    'city': 'Atlanta',
                    'state': 'GA',
                    'address': 'Hartsfield-Jackson Atlanta International Airport',
                    'contact_name': 'Facilities Manager',
                    'contact_email': 'facilities@delta.com',
                    'contact_phone': '(404) 715-2600',
                    'website_url': 'https://www.delta.com',
                    'services_needed': 'Aircraft cabin cleaning, hangar maintenance, facility cleaning',
                    'estimated_monthly_value': '$50,000 - $100,000',
                    'current_contract_status': 'Open',
                    'notes': 'Major airline hub with 24/7 operations. High-volume cleaning needs.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'American Airlines - DFW Hub',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Boeing 737, Airbus A321, Boeing 777',
                    'fleet_size': 180,
                    'city': 'Dallas',
                    'state': 'TX',
                    'address': 'Dallas/Fort Worth International Airport',
                    'contact_name': 'Procurement Department',
                    'contact_email': 'procurement@aa.com',
                    'contact_phone': '(817) 963-1234',
                    'website_url': 'https://www.aa.com',
                    'services_needed': 'Aircraft interior cleaning, terminal cleaning, ground support',
                    'estimated_monthly_value': '$45,000 - $90,000',
                    'current_contract_status': 'Open',
                    'notes': 'Largest airline hub in Texas. Multiple terminals and hangars.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'United Airlines - ORD Hub',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Boeing 737, Boeing 787, Airbus A320',
                    'fleet_size': 150,
                    'city': 'Chicago',
                    'state': 'IL',
                    'address': "O'Hare International Airport",
                    'contact_name': 'Operations Manager',
                    'contact_email': 'operations@united.com',
                    'contact_phone': '(872) 825-4000',
                    'website_url': 'https://www.united.com',
                    'services_needed': 'Cabin cleaning, lavatory service, galley cleaning, terminal maintenance',
                    'estimated_monthly_value': '$40,000 - $80,000',
                    'current_contract_status': 'Open',
                    'notes': "Busy international hub at O'Hare. High standards required.",
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'Southwest Airlines - DAL Base',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Boeing 737 (all variants)',
                    'fleet_size': 120,
                    'city': 'Dallas',
                    'state': 'TX',
                    'address': 'Dallas Love Field',
                    'contact_name': 'Facilities Director',
                    'contact_email': 'facilities@southwest.com',
                    'contact_phone': '(214) 792-4000',
                    'website_url': 'https://www.southwest.com',
                    'services_needed': 'Aircraft cleaning, hangar cleaning, office facility maintenance',
                    'estimated_monthly_value': '$35,000 - $70,000',
                    'current_contract_status': 'Open',
                    'notes': 'Fast turnaround cleaning required. Volume-based opportunities.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'JetBlue Airways - JFK Base',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Airbus A320, Airbus A321',
                    'fleet_size': 90,
                    'city': 'New York',
                    'state': 'NY',
                    'address': 'John F. Kennedy International Airport, Terminal 5',
                    'contact_name': 'Ground Services',
                    'contact_email': 'groundservices@jetblue.com',
                    'contact_phone': '(718) 286-7900',
                    'website_url': 'https://www.jetblue.com',
                    'services_needed': 'Aircraft interior cleaning, terminal facilities, crew areas',
                    'estimated_monthly_value': '$30,000 - $60,000',
                    'current_contract_status': 'Open',
                    'notes': 'Focus on customer experience. Modern terminal facilities.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'Spirit Airlines - FLL Base',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Airbus A320 family',
                    'fleet_size': 75,
                    'city': 'Fort Lauderdale',
                    'state': 'FL',
                    'address': 'Fort Lauderdale-Hollywood International Airport',
                    'contact_name': 'Operations Support',
                    'contact_email': 'ops@spirit.com',
                    'contact_phone': '(954) 447-7965',
                    'website_url': 'https://www.spirit.com',
                    'services_needed': 'Aircraft cleaning, lavatory service, hangar maintenance',
                    'estimated_monthly_value': '$25,000 - $50,000',
                    'current_contract_status': 'Open',
                    'notes': 'High-frequency flights. Cost-effective cleaning solutions preferred.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'Frontier Airlines - DEN Base',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Airbus A320neo',
                    'fleet_size': 60,
                    'city': 'Denver',
                    'state': 'CO',
                    'address': 'Denver International Airport',
                    'contact_name': 'Facilities Manager',
                    'contact_email': 'facilities@flyfrontier.com',
                    'contact_phone': '(720) 374-4200',
                    'website_url': 'https://www.flyfrontier.com',
                    'services_needed': 'Aircraft cabin cleaning, ground support areas, terminal facilities',
                    'estimated_monthly_value': '$22,000 - $45,000',
                    'current_contract_status': 'Open',
                    'notes': 'Growing airline with expansion plans. Long-term opportunities.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'Alaska Airlines - SEA Hub',
                    'company_type': 'Commercial Airline',
                    'aircraft_types': 'Boeing 737, Airbus A320',
                    'fleet_size': 85,
                    'city': 'Seattle',
                    'state': 'WA',
                    'address': 'Seattle-Tacoma International Airport',
                    'contact_name': 'Ground Operations',
                    'contact_email': 'groundops@alaskaair.com',
                    'contact_phone': '(206) 392-5040',
                    'website_url': 'https://www.alaskaair.com',
                    'services_needed': 'Aircraft cleaning, hangar maintenance, office cleaning, lounge facilities',
                    'estimated_monthly_value': '$35,000 - $70,000',
                    'current_contract_status': 'Open',
                    'notes': 'West Coast hub. Strong focus on sustainability and eco-friendly practices.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'NetJets - CMH Operations Center',
                    'company_type': 'Private Jet Operator',
                    'aircraft_types': 'Bombardier, Cessna Citation, Embraer Phenom',
                    'fleet_size': 45,
                    'city': 'Columbus',
                    'state': 'OH',
                    'address': 'John Glenn Columbus International Airport',
                    'contact_name': 'Facilities Director',
                    'contact_email': 'facilities@netjets.com',
                    'contact_phone': '(614) 239-5000',
                    'website_url': 'https://www.netjets.com',
                    'services_needed': 'Private aircraft detailing, hangar cleaning, executive lounge maintenance',
                    'estimated_monthly_value': '$20,000 - $40,000',
                    'current_contract_status': 'Open',
                    'notes': 'Premium service expectations. White-glove cleaning standards.',
                    'data_source': 'Manual seed data'
                },
                {
                    'company_name': 'Signature Flight Support - TEB FBO',
                    'company_type': 'Fixed Base Operator (FBO)',
                    'aircraft_types': 'Various private jets and business aircraft',
                    'fleet_size': 30,
                    'city': 'Teterboro',
                    'state': 'NJ',
                    'address': 'Teterboro Airport',
                    'contact_name': 'FBO Manager',
                    'contact_email': 'teterboro@signatureflight.com',
                    'contact_phone': '(201) 288-1775',
                    'website_url': 'https://www.signatureflight.com',
                    'services_needed': 'Terminal cleaning, hangar maintenance, aircraft detailing services',
                    'estimated_monthly_value': '$15,000 - $30,000',
                    'current_contract_status': 'Open',
                    'notes': 'High-end FBO serving NYC area. Luxury service standards required.',
                    'data_source': 'Manual seed data'
                }
            ]
            
            # Insert each lead
            inserted_count = 0
            for lead in aviation_leads:
                try:
                    db.session.execute(text('''
                        INSERT INTO aviation_cleaning_leads 
                        (company_name, company_type, aircraft_types, fleet_size, city, state, address,
                         contact_name, contact_email, contact_phone, website_url, services_needed,
                         estimated_monthly_value, current_contract_status, notes, data_source, is_active)
                        VALUES 
                        (:company_name, :company_type, :aircraft_types, :fleet_size, :city, :state, :address,
                         :contact_name, :contact_email, :contact_phone, :website_url, :services_needed,
                         :estimated_monthly_value, :current_contract_status, :notes, :data_source, TRUE)
                        ON CONFLICT (company_name, city, state) DO NOTHING
                    '''), lead)
                    inserted_count += 1
                except Exception as e:
                    print(f"⚠️ Error inserting {lead['company_name']}: {e}")
                    continue
            
            db.session.commit()
            print(f"✅ Successfully populated {inserted_count} aviation leads")
            
            # Verify
            result = db.session.execute(text('SELECT COUNT(*) FROM aviation_cleaning_leads'))
            total = result.scalar()
            print(f"📊 Total aviation leads in database: {total}")
            
        except Exception as e:
            print(f"❌ Error populating aviation leads: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    populate_aviation_leads()
