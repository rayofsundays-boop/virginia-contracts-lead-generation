#!/usr/bin/env python3
"""
Run this script in Render Shell to fix the industry_days table and seed events
Copy/paste: python fix_production_db.py
"""

from app import app, db
from sqlalchemy import text
from datetime import datetime, timedelta

with app.app_context():
    try:
        print("🔧 Starting database fix...")
        
        # Step 1: Add missing columns
        print("📝 Adding city and state columns...")
        db.session.execute(text('ALTER TABLE industry_days ADD COLUMN IF NOT EXISTS city TEXT'))
        db.session.execute(text('ALTER TABLE industry_days ADD COLUMN IF NOT EXISTS state TEXT'))
        db.session.commit()
        print("✅ Columns added!")
        
        # Step 2: Clear old data
        print("🗑️  Clearing old events...")
        db.session.execute(text('DELETE FROM industry_days'))
        db.session.commit()
        
        # Step 3: Seed new data
        print("🌱 Seeding events for all 50 states...")
        today = datetime.utcnow().date()
        
        states = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware',
                  'Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky',
                  'Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi',
                  'Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico',
                  'New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania',
                  'Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont',
                  'Virginia','Washington','West Virginia','Wisconsin','Wyoming']
        
        cities = {
            'Alabama':'Montgomery','Alaska':'Anchorage','Arizona':'Phoenix','Arkansas':'Little Rock',
            'California':'Sacramento','Colorado':'Denver','Connecticut':'Hartford','Delaware':'Dover',
            'Florida':'Tallahassee','Georgia':'Atlanta','Hawaii':'Honolulu','Idaho':'Boise',
            'Illinois':'Springfield','Indiana':'Indianapolis','Iowa':'Des Moines','Kansas':'Topeka',
            'Kentucky':'Frankfort','Louisiana':'Baton Rouge','Maine':'Augusta','Maryland':'Annapolis',
            'Massachusetts':'Boston','Michigan':'Lansing','Minnesota':'St. Paul','Mississippi':'Jackson',
            'Missouri':'Jefferson City','Montana':'Helena','Nebraska':'Lincoln','Nevada':'Carson City',
            'New Hampshire':'Concord','New Jersey':'Trenton','New Mexico':'Santa Fe','New York':'Albany',
            'North Carolina':'Raleigh','North Dakota':'Bismarck','Ohio':'Columbus','Oklahoma':'Oklahoma City',
            'Oregon':'Salem','Pennsylvania':'Harrisburg','Rhode Island':'Providence','South Carolina':'Columbia',
            'South Dakota':'Pierre','Tennessee':'Nashville','Texas':'Austin','Utah':'Salt Lake City',
            'Vermont':'Montpelier','Virginia':'Richmond','Washington':'Olympia','West Virginia':'Charleston',
            'Wisconsin':'Madison','Wyoming':'Cheyenne'
        }
        
        types = ['Industry Day','Procurement Fair','Networking Event','Workshop']
        
        insert_sql = text('''
            INSERT INTO industry_days (
                event_title, organizer, organizer_type, event_date, event_time, 
                location, city, state, venue_name, event_type, description, 
                target_audience, registration_required, registration_deadline, 
                registration_link, contact_name, contact_email, contact_phone, 
                topics, is_virtual, status
            ) VALUES (
                :title, :org, :org_type, :date, :time, :loc, :city, :state, 
                :venue, :type, :desc, :audience, :reg_req, :reg_dead, :reg_link, 
                :contact, :email, :phone, :topics, :virtual, :status
            )
        ''')
        
        for i, state in enumerate(states):
            for j in range(4):
                event_date = today + timedelta(days=7 + (i * 2) + j)
                city = cities[state]
                
                db.session.execute(insert_sql, {
                    'title': f'{state} {types[j % len(types)]} - {event_date.strftime("%B %Y")}',
                    'org': f'{state} Department of Commerce',
                    'org_type': 'State Agency',
                    'date': event_date,
                    'time': '9:00 AM - 4:00 PM',
                    'loc': f'{city}, {state}',
                    'city': city,
                    'state': state,
                    'venue': f'{state} Convention Center',
                    'type': types[j % len(types)],
                    'desc': f'Join procurement professionals for networking and opportunities in {state}.',
                    'audience': 'Small businesses, contractors, vendors',
                    'reg_req': True,
                    'reg_dead': event_date - timedelta(days=7),
                    'reg_link': f'https://eventbrite.com/{state.lower().replace(" ","-")}-{types[j % len(types)].lower().replace(" ","-")}',
                    'contact': 'Procurement Office',
                    'email': f'procurement@{state.lower().replace(" ","")}.gov',
                    'phone': '(555) 123-4567',
                    'topics': 'Government contracting,networking,procurement',
                    'virtual': False,
                    'status': 'upcoming'
                })
        
        db.session.commit()
        
        # Step 4: Verify
        count = db.session.execute(text('SELECT COUNT(*) FROM industry_days')).scalar()
        print(f"✅ Successfully seeded {count} events!")
        
        # Show sample
        sample = db.session.execute(text('SELECT event_title, city, state FROM industry_days LIMIT 5')).fetchall()
        print("\n📋 Sample events:")
        for evt in sample:
            print(f"   • {evt[0]} in {evt[1]}, {evt[2]}")
        
        print("\n🎉 Database fix complete! Visit /industry-days-events to see events")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
