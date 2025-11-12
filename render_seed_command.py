#!/usr/bin/env python3
"""
Copy and paste this entire script into Render's Shell
This will seed the industry_days table with events
"""

from app import app, db
from sqlalchemy import text
from datetime import datetime, timedelta

with app.app_context():
    try:
        print("🌱 Starting database seeding...")
        
        # Create table if not exists
        is_postgres = 'postgresql' in str(db.engine.url)
        id_type = 'SERIAL PRIMARY KEY' if is_postgres else 'INTEGER PRIMARY KEY'
        bool_type = 'BOOLEAN' if is_postgres else 'INTEGER'
        reg_default = 'TRUE' if is_postgres else '1'
        virt_default = 'FALSE' if is_postgres else '0'
        
        ddl = f'''CREATE TABLE IF NOT EXISTS industry_days (
            id {id_type},
            event_title TEXT NOT NULL,
            organizer TEXT NOT NULL,
            organizer_type TEXT,
            event_date DATE NOT NULL,
            event_time TEXT,
            location TEXT,
            city TEXT,
            state TEXT,
            venue_name TEXT,
            event_type TEXT DEFAULT 'Industry Day',
            description TEXT,
            target_audience TEXT,
            registration_required {bool_type} DEFAULT {reg_default},
            registration_deadline DATE,
            registration_link TEXT,
            contact_name TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            topics TEXT,
            is_virtual {bool_type} DEFAULT {virt_default},
            virtual_link TEXT,
            attachments TEXT,
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
        
        db.session.execute(text(ddl))
        db.session.commit()
        print("✅ Table created/verified")
        
        # Check existing count
        count = db.session.execute(text('SELECT COUNT(*) FROM industry_days')).scalar() or 0
        print(f"📊 Current events: {count}")
        
        if count > 0:
            print("⚠️  Events already exist. Clearing old events...")
            db.session.execute(text('DELETE FROM industry_days'))
            db.session.commit()
        
        # Generate events for all 50 states
        today = datetime.utcnow().date()
        states = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia',
                  'Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland',
                  'Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey',
                  'New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina',
                  'South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming']
        
        cities = {
            'Alabama': 'Montgomery', 'Alaska': 'Anchorage', 'Arizona': 'Phoenix', 'Arkansas': 'Little Rock',
            'California': 'Sacramento', 'Colorado': 'Denver', 'Connecticut': 'Hartford', 'Delaware': 'Dover',
            'Florida': 'Tallahassee', 'Georgia': 'Atlanta', 'Hawaii': 'Honolulu', 'Idaho': 'Boise',
            'Illinois': 'Springfield', 'Indiana': 'Indianapolis', 'Iowa': 'Des Moines', 'Kansas': 'Topeka',
            'Kentucky': 'Frankfort', 'Louisiana': 'Baton Rouge', 'Maine': 'Augusta', 'Maryland': 'Annapolis',
            'Massachusetts': 'Boston', 'Michigan': 'Lansing', 'Minnesota': 'St. Paul', 'Mississippi': 'Jackson',
            'Missouri': 'Jefferson City', 'Montana': 'Helena', 'Nebraska': 'Lincoln', 'Nevada': 'Carson City',
            'New Hampshire': 'Concord', 'New Jersey': 'Trenton', 'New Mexico': 'Santa Fe', 'New York': 'Albany',
            'North Carolina': 'Raleigh', 'North Dakota': 'Bismarck', 'Ohio': 'Columbus', 'Oklahoma': 'Oklahoma City',
            'Oregon': 'Salem', 'Pennsylvania': 'Harrisburg', 'Rhode Island': 'Providence', 'South Carolina': 'Columbia',
            'South Dakota': 'Pierre', 'Tennessee': 'Nashville', 'Texas': 'Austin', 'Utah': 'Salt Lake City',
            'Vermont': 'Montpelier', 'Virginia': 'Richmond', 'Washington': 'Olympia', 'West Virginia': 'Charleston',
            'Wisconsin': 'Madison', 'Wyoming': 'Cheyenne'
        }
        
        event_types = ['Industry Day', 'Procurement Fair', 'Networking Event', 'Workshop', 'Small Business Conference']
        
        events_to_insert = []
        for i, state in enumerate(states):
            for j in range(4):  # 4 events per state = 200 total
                event_date = today + timedelta(days=7 + (i * 2) + j)
                city = cities.get(state, 'Capital City')
                event_type = event_types[j % len(event_types)]
                
                event = {
                    'event_title': f'{state} {event_type} - {event_date.strftime("%B %Y")}',
                    'organizer': f'{state} Department of Commerce',
                    'organizer_type': 'State Agency',
                    'event_date': event_date.strftime('%Y-%m-%d'),
                    'event_time': '09:00 AM - 4:00 PM',
                    'location': f'{city}, {state}',
                    'city': city,
                    'state': state,
                    'venue_name': f'{state} Convention Center',
                    'event_type': event_type,
                    'description': f'Join procurement professionals and businesses for networking and learning about upcoming opportunities in {state}.',
                    'target_audience': 'Small businesses, contractors, vendors',
                    'registration_required': True,
                    'registration_deadline': (event_date - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'registration_link': f'https://eventbrite.com/{state.lower().replace(" ", "-")}-{event_type.lower().replace(" ", "-")}',
                    'contact_name': 'Procurement Office',
                    'contact_email': f'procurement@{state.lower().replace(" ", "")}.gov',
                    'contact_phone': '(555) 123-4567',
                    'topics': 'Government contracting,networking,procurement opportunities,small business',
                    'is_virtual': False,
                    'virtual_link': None,
                    'attachments': None,
                    'status': 'upcoming'
                }
                events_to_insert.append(event)
        
        # Insert events
        insert_sql = text('''
            INSERT INTO industry_days (
                event_title, organizer, organizer_type, event_date, event_time, location, city, state, venue_name,
                event_type, description, target_audience, registration_required, registration_deadline, registration_link,
                contact_name, contact_email, contact_phone, topics, is_virtual, virtual_link, attachments, status
            ) VALUES (
                :event_title, :organizer, :organizer_type, :event_date, :event_time, :location, :city, :state, :venue_name,
                :event_type, :description, :target_audience, :registration_required, :registration_deadline, :registration_link,
                :contact_name, :contact_email, :contact_phone, :topics, :is_virtual, :virtual_link, :attachments, :status
            )
        ''')
        
        for event in events_to_insert:
            db.session.execute(insert_sql, event)
        
        db.session.commit()
        
        # Verify
        final_count = db.session.execute(text('SELECT COUNT(*) FROM industry_days')).scalar()
        print(f"✅ Successfully seeded {final_count} events!")
        print("🎉 Visit /industry-days-events to see the events")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
