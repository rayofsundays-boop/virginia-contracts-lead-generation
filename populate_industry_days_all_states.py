#!/usr/bin/env python3
"""
Populate industry_days table with events from all 50 states.
Creates realistic procurement and small business events across the United States.
"""

import sqlite3
from datetime import datetime, timedelta
import random

# All 50 states with major cities
US_STATES = {
    'Alabama': ['Birmingham', 'Montgomery', 'Mobile', 'Huntsville'],
    'Alaska': ['Anchorage', 'Fairbanks', 'Juneau'],
    'Arizona': ['Phoenix', 'Tucson', 'Mesa', 'Scottsdale'],
    'Arkansas': ['Little Rock', 'Fort Smith', 'Fayetteville'],
    'California': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'San Jose'],
    'Colorado': ['Denver', 'Colorado Springs', 'Aurora', 'Fort Collins'],
    'Connecticut': ['Hartford', 'New Haven', 'Stamford', 'Bridgeport'],
    'Delaware': ['Wilmington', 'Dover', 'Newark'],
    'Florida': ['Miami', 'Orlando', 'Tampa', 'Jacksonville', 'Tallahassee'],
    'Georgia': ['Atlanta', 'Savannah', 'Augusta', 'Columbus'],
    'Hawaii': ['Honolulu', 'Hilo', 'Kailua'],
    'Idaho': ['Boise', 'Meridian', 'Nampa'],
    'Illinois': ['Chicago', 'Springfield', 'Naperville', 'Aurora'],
    'Indiana': ['Indianapolis', 'Fort Wayne', 'Evansville'],
    'Iowa': ['Des Moines', 'Cedar Rapids', 'Davenport'],
    'Kansas': ['Wichita', 'Overland Park', 'Kansas City', 'Topeka'],
    'Kentucky': ['Louisville', 'Lexington', 'Bowling Green', 'Frankfort'],
    'Louisiana': ['New Orleans', 'Baton Rouge', 'Shreveport', 'Lafayette'],
    'Maine': ['Portland', 'Augusta', 'Bangor'],
    'Maryland': ['Baltimore', 'Annapolis', 'Frederick', 'Rockville'],
    'Massachusetts': ['Boston', 'Worcester', 'Springfield', 'Cambridge'],
    'Michigan': ['Detroit', 'Grand Rapids', 'Lansing', 'Ann Arbor'],
    'Minnesota': ['Minneapolis', 'St. Paul', 'Rochester', 'Duluth'],
    'Mississippi': ['Jackson', 'Gulfport', 'Biloxi'],
    'Missouri': ['Kansas City', 'St. Louis', 'Springfield', 'Jefferson City'],
    'Montana': ['Billings', 'Missoula', 'Great Falls', 'Helena'],
    'Nebraska': ['Omaha', 'Lincoln', 'Bellevue'],
    'Nevada': ['Las Vegas', 'Reno', 'Henderson', 'Carson City'],
    'New Hampshire': ['Manchester', 'Nashua', 'Concord'],
    'New Jersey': ['Newark', 'Jersey City', 'Trenton', 'Atlantic City'],
    'New Mexico': ['Albuquerque', 'Santa Fe', 'Las Cruces'],
    'New York': ['New York City', 'Buffalo', 'Albany', 'Rochester', 'Syracuse'],
    'North Carolina': ['Charlotte', 'Raleigh', 'Greensboro', 'Durham'],
    'North Dakota': ['Fargo', 'Bismarck', 'Grand Forks'],
    'Ohio': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo'],
    'Oklahoma': ['Oklahoma City', 'Tulsa', 'Norman'],
    'Oregon': ['Portland', 'Eugene', 'Salem', 'Bend'],
    'Pennsylvania': ['Philadelphia', 'Pittsburgh', 'Harrisburg', 'Allentown'],
    'Rhode Island': ['Providence', 'Warwick', 'Cranston'],
    'South Carolina': ['Charleston', 'Columbia', 'Greenville'],
    'South Dakota': ['Sioux Falls', 'Rapid City', 'Pierre'],
    'Tennessee': ['Nashville', 'Memphis', 'Knoxville', 'Chattanooga'],
    'Texas': ['Houston', 'Dallas', 'Austin', 'San Antonio', 'Fort Worth'],
    'Utah': ['Salt Lake City', 'Provo', 'West Valley City'],
    'Vermont': ['Burlington', 'Montpelier', 'Rutland'],
    'Virginia': ['Richmond', 'Virginia Beach', 'Norfolk', 'Arlington', 'Alexandria'],
    'Washington': ['Seattle', 'Spokane', 'Tacoma', 'Olympia'],
    'West Virginia': ['Charleston', 'Huntington', 'Morgantown'],
    'Wisconsin': ['Milwaukee', 'Madison', 'Green Bay'],
    'Wyoming': ['Cheyenne', 'Casper', 'Laramie']
}

EVENT_TYPES = [
    'Industry Day',
    'Small Business Conference',
    'Procurement Matchmaking',
    'Vendor Outreach',
    'SBA Workshop',
    'Networking Event',
    'Contracting Summit',
    'Business Expo'
]

ORGANIZER_TYPES = [
    'State Government',
    'Federal Agency',
    'SBA District Office',
    'Chamber of Commerce',
    'Industry Association',
    'Economic Development'
]

TOPICS_OPTIONS = [
    'Government Contracting 101, SAM Registration, Bid Preparation',
    'Small Business Set-Asides, 8(a) Program, Women-Owned Business',
    'Janitorial Services, Facility Maintenance, Building Operations',
    'Federal Procurement, State Contracts, Local Opportunities',
    'Networking, Matchmaking, Prime Contractor Meetings',
    'Certifications, Compliance, Contract Management',
    'Business Development, Marketing, Proposal Writing',
    'Technology Integration, Innovation, Best Practices'
]

def create_table(cursor):
    """Create industry_days table if it doesn't exist"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS industry_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_title TEXT NOT NULL,
            organizer TEXT NOT NULL,
            organizer_type TEXT,
            event_date DATE NOT NULL,
            event_time TEXT,
            location TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            venue_name TEXT,
            event_type TEXT NOT NULL,
            description TEXT,
            target_audience TEXT,
            registration_required BOOLEAN DEFAULT 1,
            registration_deadline DATE,
            registration_link TEXT,
            contact_name TEXT,
            contact_email TEXT,
            contact_phone TEXT,
            topics TEXT,
            is_virtual BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_industry_days_date ON industry_days(event_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_industry_days_city ON industry_days(event_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_industry_days_state ON industry_days(state)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_industry_days_status ON industry_days(status)')

def generate_events(cursor):
    """Generate realistic events for all 50 states"""
    
    print('🎯 Generating industry days & procurement events for all 50 states...\n')
    
    events_created = 0
    start_date = datetime.now() + timedelta(days=7)  # Start 1 week from now
    
    for state, cities in US_STATES.items():
        # Generate 3-5 events per state
        num_events = random.randint(3, 5)
        
        for i in range(num_events):
            city = random.choice(cities)
            event_type = random.choice(EVENT_TYPES)
            organizer_type = random.choice(ORGANIZER_TYPES)
            
            # Generate event date (next 6 months)
            days_ahead = random.randint(7, 180)
            event_date = start_date + timedelta(days=days_ahead)
            
            # Registration deadline 2 weeks before event
            reg_deadline = event_date - timedelta(days=14)
            
            # Event time
            hour = random.choice([8, 9, 10, 13, 14])
            event_time = f"{hour:02d}:00 - {hour+3:02d}:00"
            
            # Virtual or in-person (30% virtual)
            is_virtual = random.random() < 0.3
            
            # Generate event details
            event_title = f"{state} {event_type} - {event_date.strftime('%B %Y')}"
            organizer = f"{state} Department of Commerce" if organizer_type == 'State Government' else f"{state} SBA Office"
            venue_name = f"{city} Convention Center" if not is_virtual else "Virtual Event Platform"
            location = state if is_virtual else f"{city}, {state}"
            
            description = f"Join us for the {event_type.lower()} focused on government contracting opportunities in {state}. Meet prime contractors, learn about upcoming solicitations, and network with procurement officials."
            
            target_audience = "Small businesses, minority-owned firms, veteran-owned businesses, cleaning contractors"
            
            contact_name = f"{random.choice(['John', 'Mary', 'David', 'Sarah', 'Michael', 'Jennifer'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Davis'])}"
            contact_email = f"procurement@{state.lower().replace(' ', '')}.gov"
            contact_phone = f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
            
            registration_link = f"https://events.{state.lower().replace(' ', '')}.gov/register/{random.randint(1000, 9999)}"
            
            topics = random.choice(TOPICS_OPTIONS)
            
            cursor.execute('''
                INSERT INTO industry_days (
                    event_title, organizer, organizer_type, event_date, event_time,
                    location, city, state, venue_name, event_type, description,
                    target_audience, registration_required, registration_deadline,
                    registration_link, contact_name, contact_email, contact_phone,
                    topics, is_virtual, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_title, organizer, organizer_type, event_date.strftime('%Y-%m-%d'),
                event_time, location, city, state, venue_name, event_type,
                description, target_audience, True, reg_deadline.strftime('%Y-%m-%d'),
                registration_link, contact_name, contact_email, contact_phone,
                topics, is_virtual, 'upcoming'
            ))
            
            events_created += 1
            
        print(f'✅ {state}: Created {num_events} events')
    
    return events_created

def main():
    """Main execution"""
    print('🚀 INDUSTRY DAYS & EVENTS - ALL 50 STATES POPULATION\n')
    print('='*80)
    
    conn = sqlite3.connect('leads.db')
    cursor = conn.cursor()
    
    try:
        # Check if table exists and has data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='industry_days'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute('SELECT COUNT(*) FROM industry_days')
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f'⚠️  Table already has {existing_count} events')
                response = input('Delete existing data and repopulate? (yes/no): ').strip().lower()
                
                if response == 'yes':
                    cursor.execute('DELETE FROM industry_days')
                    print('🗑️  Deleted existing events\n')
                else:
                    print('❌ Cancelled')
                    return
        
        # Create table
        print('📋 Creating industry_days table...')
        create_table(cursor)
        print('✅ Table created\n')
        
        # Generate events
        events_created = generate_events(cursor)
        
        conn.commit()
        
        print('\n' + '='*80)
        print(f'✅ SUCCESS! Created {events_created} events across all 50 states\n')
        
        # Show statistics
        cursor.execute('SELECT COUNT(DISTINCT state) FROM industry_days')
        state_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT city) FROM industry_days')
        city_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM industry_days WHERE is_virtual = 1')
        virtual_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT event_type, COUNT(*) FROM industry_days GROUP BY event_type ORDER BY COUNT(*) DESC')
        type_stats = cursor.fetchall()
        
        print('📊 STATISTICS:')
        print(f'   States: {state_count}')
        print(f'   Cities: {city_count}')
        print(f'   Total Events: {events_created}')
        print(f'   Virtual Events: {virtual_count}')
        print(f'   In-Person Events: {events_created - virtual_count}')
        
        print('\n📈 Events by Type:')
        for event_type, count in type_stats:
            print(f'   {event_type}: {count}')
        
        print('\n🎉 All 50 states now have procurement events!')
        print('🌐 Visit /industry-days to see the full calendar')
        
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
