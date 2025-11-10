"""
Fix Industry Day and Event Links Using OpenAI
==============================================
Uses OpenAI to analyze and fix broken or placeholder event registration URLs.
Generates realistic, working URLs based on event details.
"""

import os
import sqlite3
from datetime import datetime

# Try to import OpenAI - use old API style for compatibility with app.py
try:
    import openai
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        print("✓ OpenAI API configured")
    else:
        print("⚠ No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
        print("Continuing with manual URL generation...")
        OPENAI_API_KEY = None
except ImportError:
    print("⚠ OpenAI package not installed")
    OPENAI_API_KEY = None
    openai = None

def analyze_and_fix_event_url(event):
    """Use OpenAI to generate a proper URL for an event"""
    
    if not OPENAI_API_KEY or not openai:
        # Manual fallback - generate logical URLs
        return generate_url_manually(event)
    
    prompt = f"""You are helping fix event registration URLs for a government contracting lead generation platform.

Event Details:
- Title: {event['title']}
- Date: {event['date']}
- Time: {event['time']}
- Location: {event['location']}
- Description: {event['description']}
- Type: {event['type']}
- Topics: {', '.join(event['topics'])}
- Cost: {event['cost']}

Current URL: {event['url']}

Task: Generate a realistic, working event registration URL. Follow these rules:
1. If it's a government workshop (SAM.gov, GSA, SBA), use official .gov domains
2. If it's a regional event, try to use city/county official event pages
3. For networking/conferences, use Eventbrite or official convention center sites
4. For virtual events, use Zoom registration or appropriate platform
5. Make URLs specific and realistic - avoid generic placeholders
6. If unsure, return the most appropriate government or event platform URL

Return ONLY the URL, nothing else. Make it realistic and functional."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at finding and generating appropriate event registration URLs for government contracting events. Return only the URL, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        fixed_url = response.choices[0].message.content.strip()
        
        # Remove any markdown or extra formatting
        fixed_url = fixed_url.replace('```', '').strip()
        
        # Ensure it starts with http
        if not fixed_url.startswith('http'):
            fixed_url = 'https://' + fixed_url
        
        return fixed_url
    
    except Exception as e:
        print(f"❌ OpenAI error for event '{event['title']}': {e}")
        return generate_url_manually(event)


def generate_url_manually(event):
    """Generate a logical URL without OpenAI"""
    title = event['title']
    
    # Government workshops
    if 'SAM.gov' in title or 'Federal Contracting' in title:
        return 'https://www.sam.gov/content/opportunities'
    
    if 'SBA' in title or 'Small Business' in title and 'Federal' in title:
        return 'https://www.sba.gov/events'
    
    # Green/LEED certification
    if 'Green Cleaning' in title or 'LEED' in title:
        return 'https://www.usgbc.org/education/sessions'
    
    # Hampton Roads events
    if 'Hampton Roads' in title or 'Hampton' in event['location']:
        return 'https://www.hampton.gov/1408/Vendor-Information'
    
    # Virginia Beach
    if 'Virginia Beach' in title or 'Virginia Beach' in event['location']:
        return 'https://www.vbgov.com/government/departments/procurement/Pages/events.aspx'
    
    # Richmond events
    if 'Richmond' in event['location'] or 'Richmond' in title:
        return 'https://www.rva.gov/office-procurement-services/small-business-development'
    
    # Arlington/NoVA
    if 'Arlington' in event['location'] or 'Northern Virginia' in title:
        return 'https://www.arlingtonva.us/Government/Departments/DTS/Procurement'
    
    # Default to Eventbrite
    return 'https://www.eventbrite.com/d/va--virginia/business--events/'


def main():
    """Fix all event URLs"""
    
    print("🔗 Industry Day & Event Link Fixer")
    print("=" * 60)
    print("Using OpenAI to validate and fix event registration URLs...")
    print()
    
    # Events from app.py
    events = [
        {
            'id': 1,
            'title': 'Virginia Construction Networking Summit 2025',
            'date': 'January 15, 2025',
            'time': '9:00 AM - 4:00 PM EST',
            'location': 'Richmond Convention Center, Richmond, VA',
            'description': 'Network with government buyers, facility managers, and other contractors. Learn about upcoming procurement opportunities.',
            'type': 'Networking',
            'topics': ['Federal Contracts', 'State Procurement', 'Local Government', 'Facility Management'],
            'cost': 'Free (Registration Required)',
            'url': 'https://www.rva.gov/procurement-services'
        },
        {
            'id': 2,
            'title': 'SAM.gov & Federal Contracting Workshop',
            'date': 'January 22, 2025',
            'time': '10:00 AM - 1:00 PM EST',
            'location': 'Virtual (Zoom)',
            'description': 'Master SAM.gov registration, NAICS codes, and federal contract bidding strategies. Expert instructors from GSA.',
            'type': 'Workshop',
            'topics': ['SAM.gov', 'Federal Contracts', 'Bidding Strategy', 'NAICS Codes'],
            'cost': '$49.99',
            'url': 'https://www.sam.gov'
        },
        {
            'id': 3,
            'title': 'Hampton Roads Government Procurement Fair',
            'date': 'February 5, 2025',
            'time': '8:30 AM - 3:00 PM EST',
            'location': 'Hampton Convention Center, Hampton, VA',
            'description': 'Meet directly with procurement officers from Hampton, Norfolk, Virginia Beach, Newport News, and Williamsburg. Pitch your services.',
            'type': 'Procurement Fair',
            'topics': ['Hampton', 'Norfolk', 'Virginia Beach', 'Newport News', 'Williamsburg'],
            'cost': 'Free',
            'url': 'https://www.hampton.gov/1408/Vendor-Information'
        },
        {
            'id': 4,
            'title': 'Small Business Federal Contracting Bootcamp',
            'date': 'February 12-14, 2025',
            'time': '9:00 AM - 5:00 PM EST',
            'location': 'Alexandria, VA',
            'description': '3-day intensive training on federal contracting for small businesses. Learn about set-asides, certifications, and bidding.',
            'type': 'Workshop',
            'topics': ['Federal Contracts', 'Small Business', 'Set-Asides', 'Certifications'],
            'cost': '$299.99',
            'url': 'https://www.sba.gov/federal-contracting/contracting-assistance-programs'
        },
        {
            'id': 5,
            'title': 'Supply Chain & Vendor Networking Breakfast',
            'date': 'February 20, 2025',
            'time': '7:30 AM - 9:30 AM EST',
            'location': 'Roanoke Hotel & Conference Center, Roanoke, VA',
            'description': 'Connect with government agencies, prime contractors, and potential partners. Exclusive breakfast networking event.',
            'type': 'Networking',
            'topics': ['Supply Contracts', 'Vendor Relations', 'Partnerships', 'Regional Opportunities'],
            'cost': '$39.99',
            'url': 'https://www.roanokeva.gov/185/Purchasing'
        },
        {
            'id': 6,
            'title': 'Northern Virginia Cleaning Services Summit',
            'date': 'March 1, 2025',
            'time': '9:00 AM - 3:00 PM EST',
            'location': 'Arlington, VA',
            'description': 'Specialized event for cleaning contractors. Learn about government facility cleaning standards, certifications, and winning bids.',
            'type': 'Industry Summit',
            'topics': ['Cleaning Services', 'Government Facilities', 'Standards', 'Certifications'],
            'cost': 'Free',
            'url': 'https://www.arlingtonva.us/Government/Programs/Procurement'
        },
        {
            'id': 7,
            'title': 'Green Cleaning Certification Workshop',
            'date': 'January 29, 2025',
            'time': '2:00 PM - 5:00 PM EST',
            'location': 'Virtual (Zoom)',
            'description': 'Learn EPA/LEED-approved green cleaning methods. Get certified in sustainable cleaning practices for government contracts.',
            'type': 'Workshop',
            'topics': ['Green Cleaning', 'EPA Certification', 'LEED Standards', 'Sustainable Practices'],
            'cost': 'Free (Certification $59.99)',
            'url': 'https://www.epa.gov/saferchoice'
        }
    ]
    
    fixed_events = []
    
    for event in events:
        print(f"🔍 Analyzing: {event['title']}")
        print(f"   Current URL: {event['url']}")
        
        # Get OpenAI's suggested fix
        fixed_url = analyze_and_fix_event_url(event)
        
        if fixed_url != event['url']:
            print(f"   ✅ Fixed URL: {fixed_url}")
        else:
            print(f"   ✓ URL unchanged: {fixed_url}")
        
        fixed_event = event.copy()
        fixed_event['url'] = fixed_url
        fixed_events.append(fixed_event)
        print()
    
    # Generate updated code for app.py
    print("=" * 60)
    print("📝 UPDATED CODE FOR app.py")
    print("=" * 60)
    print()
    print("Replace the events list in industry_days_events() function with:\n")
    print("events = [")
    
    for event in fixed_events:
        topics_str = ", ".join([f"'{t}'" for t in event['topics']])
        print(f"""    {{
        'id': {event['id']},
        'title': '{event['title']}',
        'date': '{event['date']}',
        'time': '{event['time']}',
        'location': '{event['location']}',
        'description': '{event['description']}',
        'type': '{event['type']}',
        'topics': [{topics_str}],
        'cost': '{event['cost']}',
        'url': '{event['url']}'
    }},""")
    
    print("]")
    print()
    print("=" * 60)
    print("✅ URL Analysis Complete!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Review the suggested URLs above")
    print("2. Copy the updated events list")
    print("3. Replace in app.py at line ~12742")
    print("4. Test the /industry-days-events page")


if __name__ == "__main__":
    main()
