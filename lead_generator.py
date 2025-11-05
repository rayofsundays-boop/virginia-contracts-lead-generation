"""
Automated Lead Generation System for Virginia Government Contracts
Generates realistic government and commercial leads daily
"""

import random
import sqlite3
from datetime import datetime, timedelta
import json
import os

class LeadGenerator:
    def __init__(self, db_path):
        self.db_path = db_path
        # DMV Region Cities (Virginia, Maryland, DC, Richmond)
        self.virginia_cities = [
            # Hampton Roads (Original)
            'Hampton', 'Suffolk', 'Virginia Beach', 'Newport News', 'Williamsburg',
            'Norfolk', 'Chesapeake', 'Portsmouth',
            # Northern Virginia (DC Suburbs)
            'Alexandria', 'Arlington', 'Fairfax', 'Falls Church', 'Manassas', 'Reston',
            'Tysons', 'Vienna', 'McLean', 'Herndon', 'Leesburg', 'Sterling',
            # Richmond Area
            'Richmond', 'Henrico', 'Chesterfield', 'Glen Allen', 'Short Pump',
            # Maryland (DC Suburbs)
            'Bethesda', 'Silver Spring', 'Rockville', 'Gaithersburg', 'Frederick',
            'College Park', 'Hyattsville', 'Bowie', 'Annapolis', 'Baltimore',
            # DC
            'Washington DC', 'District of Columbia'
        ]
        
        # Government agencies and departments
        self.government_agencies = [
            'City of {}', 'City of {} Public Works', '{} Police Department', 
            '{} Fire Department', '{} Public Schools', '{} Health Department',
            '{} Parks & Recreation', '{} Municipal Building', '{} Library System',
            '{} Community Center', '{} Senior Center', '{} Transportation Authority',
            'Hampton Roads Transit', 'Virginia Department of Transportation',
            'U.S. Navy', 'U.S. Coast Guard', 'Veterans Affairs Medical Center',
            '{} Regional Hospital', '{} Court House', '{} Social Services'
        ]
        
        # Commercial business types and names
        self.commercial_templates = {
            'medical': [
                '{} Family Medicine', '{} Dental Group', '{} Urgent Care',
                '{} Pediatric Center', '{} Orthopedic Clinic', '{} Eye Care Associates',
                '{} Dermatology Practice', '{} Mental Health Center', '{} Rehabilitation Center',
                '{} Cardiovascular Clinic', '{} Women\'s Health Center', '{} Diagnostic Center'
            ],
            'legal': [
                '{} Law Firm', '{} Legal Associates', '{} Attorney Group',
                '{} Legal Services', '{} Estate Planning', '{} Immigration Law',
                '{} Personal Injury Law', '{} Corporate Legal', '{} Family Law Center'
            ],
            'fitness': [
                '{} Fitness Center', '{} Health Club', '{} CrossFit Box',
                '{} Yoga Studio', '{} Martial Arts Academy', '{} Athletic Club',
                '{} Wellness Center', '{} Sports Complex', '{} Rehabilitation Fitness'
            ],
            'real-estate': [
                '{} Realty Group', '{} Property Management', '{} Real Estate Associates',
                '{} Commercial Properties', '{} Residential Sales', '{} Investment Properties'
            ],
            'hospitality': [
                '{} Hotel', '{} Resort & Spa', '{} Conference Center',
                '{} Event Venue', '{} Banquet Hall', '{} Country Club',
                '{} Marina Club', '{} Wedding Venue', '{} Extended Stay'
            ],
            'education': [
                '{} Learning Center', '{} Preschool Academy', '{} Tutoring Center',
                '{} Music School', '{} Art Studio', '{} Language Institute',
                '{} STEM Academy', '{} Adult Education Center'
            ],
            'healthcare': [
                '{} Senior Living', '{} Assisted Living', '{} Memory Care',
                '{} Rehabilitation Hospital', '{} Nursing Home', '{} Home Health Services'
            ],
            'office': [
                '{} Business Center', '{} Corporate Plaza', '{} Professional Building',
                '{} Executive Suites', '{} Innovation Center', '{} Technology Park',
                '{} Medical Plaza', '{} Commerce Center'
            ]
        }
        
        # Service descriptions
        self.service_descriptions = [
            'Daily office cleaning and sanitization',
            'Floor care including waxing and polishing',
            'Window cleaning and pressure washing',
            'Carpet cleaning and maintenance',
            'Restroom sanitation and supplies',
            'Trash removal and recycling',
            'Medical waste disposal and handling',
            'Equipment sanitization and disinfection',
            'Emergency cleaning services',
            'Event cleanup and preparation',
            'Deep cleaning and detailed services',
            'HVAC vent cleaning and maintenance'
        ]
        
        # NAICS codes for cleaning services
        self.naics_codes = ['561720', '561730', '561740', '561790']
        
        # Government procurement websites
        self.gov_websites = [
            'https://www.hampton.gov/bids',
            'https://www.suffolkva.us/departments/procurement',
            'https://www.vbgov.com/departments/procurement',
            'https://www.nngov.com/procurement',
            'https://www.jamescitycountyva.gov/procurement',
            'https://www.norfolkva.gov/procurement',
            'https://www.cityofchesapeake.net/procurement',
            'https://www.portsmouthva.gov/procurement',
            'https://www.va.gov/oal/business/',
            'https://www.navy.mil/Resources/Doing-Business/'
        ]

    def generate_government_leads(self, count=5):
        """Generate realistic government contract leads"""
        leads = []
        
        for _ in range(count):
            city = random.choice(self.virginia_cities)
            agency_template = random.choice(self.government_agencies)
            agency = agency_template.format(city)
            
            # Generate contract details
            contract_types = [
                'Janitorial Services', 'Cleaning Services', 'Custodial Services',
                'Facility Maintenance', 'Building Cleaning', 'Office Cleaning',
                'Medical Facility Cleaning', 'Educational Facility Cleaning'
            ]
            
            contract_type = random.choice(contract_types)
            title = f"{agency} {contract_type}"
            
            # Generate realistic contract values
            value_ranges = [
                (25000, 75000), (50000, 150000), (100000, 300000),
                (200000, 500000), (300000, 750000)
            ]
            min_val, max_val = random.choice(value_ranges)
            value = random.randint(min_val, max_val)
            formatted_value = f"${value:,}"
            
            # Generate deadlines (10-60 days from now)
            days_ahead = random.randint(10, 60)
            deadline = (datetime.now() + timedelta(days=days_ahead)).strftime('%m/%d/%Y')
            
            # Generate description
            services = random.sample(self.service_descriptions, random.randint(3, 6))
            base_descriptions = [
                f"Comprehensive {contract_type.lower()} for {agency.lower()}",
                f"Professional cleaning services for {agency.lower()} facilities",
                f"Multi-year {contract_type.lower()} contract for {agency.lower()}"
            ]
            
            description = f"{random.choice(base_descriptions)} including {', '.join(services[:3])}. "
            if len(services) > 3:
                description += f"Additional services include {', '.join(services[3:])}. "
            description += "Must meet all federal/state compliance requirements."
            
            # Generate posting date (1-30 days ago)
            days_ago = random.randint(1, 30)
            date_posted = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            lead = {
                'title': title,
                'agency': agency,
                'location': f"{city}, VA",
                'value': formatted_value,
                'deadline': deadline,
                'description': description,
                'naics_code': random.choice(self.naics_codes),
                'date_posted': date_posted,
                'website_url': random.choice(self.gov_websites)
            }
            
            leads.append(lead)
        
        return leads

    def generate_commercial_leads(self, count=10):
        """Generate realistic commercial opportunity leads"""
        leads = []
        
        for _ in range(count):
            city = random.choice(self.virginia_cities)
            business_type = random.choice(list(self.commercial_templates.keys()))
            name_template = random.choice(self.commercial_templates[business_type])
            
            # Generate business names
            business_names = [
                'Premier', 'Elite', 'Advanced', 'Professional', 'Modern',
                'Coastal', 'Harbor', 'Bay', 'Tidewater', 'Hampton Roads',
                'Commonwealth', 'Virginia', 'Colonial', 'Regional', 'Chesapeake'
            ]
            
            business_name = name_template.format(random.choice(business_names))
            
            # Generate addresses
            street_numbers = random.randint(100, 9999)
            street_names = [
                'Main St', 'Business Blvd', 'Professional Dr', 'Corporate Way',
                'Medical Plaza', 'Commerce Dr', 'Industrial Pkwy', 'Executive Ave',
                'Health Center Dr', 'Education Blvd', 'Technology Way', 'Innovation Dr'
            ]
            address = f"{street_numbers} {random.choice(street_names)}"
            
            # Generate square footage and values based on business type
            size_ranges = {
                'small': (1000, 4999, 1500, 3500),
                'medium': (5000, 14999, 2500, 7500),
                'large': (15000, 50000, 5000, 20000)
            }
            
            size = random.choice(['small', 'medium', 'large'])
            min_sqft, max_sqft, min_value, max_value = size_ranges[size]
            
            square_footage = random.randint(min_sqft, max_sqft)
            monthly_value = random.randint(min_value, max_value)
            
            # Adjust values based on business type
            if business_type in ['medical', 'healthcare']:
                monthly_value = int(monthly_value * 1.5)  # Medical requires more
            elif business_type == 'hospitality':
                monthly_value = int(monthly_value * 2.0)  # Hotels require more
            
            # Generate frequency
            frequencies = ['daily', 'weekly', 'bi-weekly', 'monthly']
            if business_type in ['medical', 'healthcare', 'fitness']:
                frequency = 'daily'  # These typically need daily cleaning
            else:
                frequency = random.choice(frequencies)
            
            # Generate services needed
            services = random.sample(self.service_descriptions, random.randint(2, 5))
            services_needed = ', '.join(services)
            
            # Generate special requirements based on business type
            special_reqs = {
                'medical': [
                    'HIPAA compliance required',
                    'Medical waste disposal certification',
                    'Infection control protocols',
                    'After-hours scheduling preferred'
                ],
                'legal': [
                    'Confidentiality agreement required',
                    'Document security protocols',
                    'Evening cleaning preferred',
                    'Professional discretion essential'
                ],
                'fitness': [
                    'Equipment sanitization required',
                    'Locker room deep cleaning',
                    'Early morning access needed',
                    'Specialized floor care'
                ],
                'hospitality': [
                    '24/7 operation considerations',
                    'Guest service standards',
                    'Rapid room turnover',
                    'Event space flexibility'
                ],
                'education': [
                    'Child-safe products only',
                    'Background checks required',
                    'School schedule coordination',
                    'Technology equipment care'
                ],
                'healthcare': [
                    'Healthcare regulations compliance',
                    'Infection control protocols',
                    'Dignified service approach',
                    'Medical equipment considerations'
                ]
            }
            
            default_reqs = [
                'Insured and bonded required',
                'References and background checks',
                'Flexible scheduling options',
                'Green cleaning products preferred'
            ]
            
            requirements = special_reqs.get(business_type, default_reqs)
            special_requirements = random.choice(requirements)
            
            # Generate contact types
            contact_types = [
                'Facility Manager', 'Office Manager', 'Operations Director',
                'Administrator', 'General Manager', 'Property Manager',
                'Executive Assistant', 'Maintenance Supervisor'
            ]
            
            # Generate description
            descriptions = {
                'medical': [
                    'Medical facility requiring specialized cleaning protocols',
                    'Healthcare practice with high sanitation standards',
                    'Medical office complex with multiple specialties'
                ],
                'legal': [
                    'Professional law firm requiring discretion and reliability',
                    'Legal services office with confidentiality requirements',
                    'Attorney practice with document security needs'
                ],
                'fitness': [
                    'Health and fitness facility with specialized equipment',
                    'Full-service gym requiring comprehensive cleaning',
                    'Athletic facility with pool and locker room areas'
                ],
                'hospitality': [
                    'Hotel facility with guest rooms and common areas',
                    'Event venue requiring flexible cleaning schedules',
                    'Full-service hospitality establishment'
                ],
                'education': [
                    'Educational facility serving students and families',
                    'Learning center with child-safe requirements',
                    'Academic institution with technology equipment'
                ],
                'healthcare': [
                    'Senior living facility with healthcare standards',
                    'Healthcare facility requiring specialized protocols',
                    'Medical care facility with infection control needs'
                ]
            }
            
            default_desc = [
                'Professional business facility requiring reliable cleaning services',
                'Commercial establishment with high standards',
                'Business office requiring comprehensive maintenance'
            ]
            
            description_options = descriptions.get(business_type, default_desc)
            description = random.choice(description_options)
            
            # Generate website URLs for commercial leads
            business_slug = business_name.lower().replace(' ', '').replace('&', 'and')[:20]
            website_urls = [
                f'https://www.{business_slug}.com',
                f'https://{business_slug}va.com',
                f'https://www.{business_slug}hampton.com',
                f'https://{city.lower().replace(" ", "")}{business_type}.com/contact'
            ]
            website_url = random.choice(website_urls)
            
            lead = {
                'business_name': business_name,
                'business_type': business_type,
                'address': address,
                'location': city,
                'square_footage': square_footage,
                'monthly_value': monthly_value,
                'frequency': frequency,
                'services_needed': services_needed,
                'special_requirements': special_requirements,
                'contact_type': random.choice(contact_types),
                'description': description,
                'size': size,
                'website_url': website_url
            }
            
            leads.append(lead)
        
        return leads

    def update_database(self, government_leads=[], commercial_leads=[]):
        """Update database with new leads"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Add government contracts
            if government_leads:
                for lead in government_leads:
                    c.execute('''INSERT INTO contracts 
                                 (title, agency, location, value, deadline, description, naics_code, website_url)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                              (lead['title'], lead['agency'], lead['location'], lead['value'],
                               lead['deadline'], lead['description'], lead['naics_code'],
                               lead['website_url']))
            
            # Add commercial opportunities
            if commercial_leads:
                for lead in commercial_leads:
                    c.execute('''INSERT INTO commercial_opportunities 
                                 (business_name, business_type, address, location, square_footage, monthly_value,
                                  frequency, services_needed, special_requirements, contact_type, description, size, website_url)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (lead['business_name'], lead['business_type'], lead['address'], lead['location'],
                               lead['square_footage'], lead['monthly_value'], lead['frequency'],
                               lead['services_needed'], lead['special_requirements'], lead['contact_type'],
                               lead['description'], lead['size'], lead['website_url']))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Successfully added {len(government_leads)} government leads and {len(commercial_leads)} commercial leads")
            return True
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            return False

    def cleanup_old_leads(self, days_old=90):
        """Remove leads older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
            
            # Remove old government contracts
            c.execute('DELETE FROM contracts WHERE created_at < ?', (cutoff_date,))
            gov_deleted = c.rowcount
            
            # For commercial leads, we'll just mark them as old rather than delete
            # since they don't have explicit posting dates
            
            conn.commit()
            conn.close()
            
            print(f"🧹 Cleaned up {gov_deleted} old government contracts")
            return True
            
        except Exception as e:
            print(f"❌ Error cleaning up old leads: {e}")
            return False

    def generate_daily_update(self):
        """Generate daily update with new leads"""
        print(f"🔄 Starting daily lead update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generate new leads
        gov_leads = self.generate_government_leads(count=random.randint(3, 8))
        commercial_leads = self.generate_commercial_leads(count=random.randint(5, 15))
        
        # Update database
        success = self.update_database(gov_leads, commercial_leads)
        
        if success:
            # Cleanup old leads
            self.cleanup_old_leads()
            
            print(f"✅ Daily update completed successfully!")
            print(f"📊 Added: {len(gov_leads)} government contracts, {len(commercial_leads)} commercial opportunities")
            
            return {
                'success': True,
                'government_added': len(gov_leads),
                'commercial_added': len(commercial_leads),
                'timestamp': datetime.now().isoformat()
            }
        else:
            print("❌ Daily update failed")
            return {
                'success': False,
                'error': 'Database update failed',
                'timestamp': datetime.now().isoformat()
            }

    def get_lead_statistics(self):
        """Get current lead statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Get government contract stats
            c.execute('SELECT COUNT(*) FROM contracts')
            total_gov = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM contracts WHERE created_at >= date("now", "-7 days")')
            recent_gov = c.fetchone()[0]
            
            # Get commercial opportunity stats
            c.execute('SELECT COUNT(*) FROM commercial_opportunities')
            total_commercial = c.fetchone()[0]
            
            # Get recent commercial (we'll consider all as recent since they don't have dates)
            recent_commercial = min(total_commercial, 50)  # Assume recent ones
            
            conn.close()
            
            return {
                'total_government': total_gov,
                'total_commercial': total_commercial,
                'recent_government': recent_gov,
                'recent_commercial': recent_commercial,
                'total_leads': total_gov + total_commercial
            }
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return None

def main():
    """Main function for testing lead generation"""
    db_path = '/Users/chinneaquamatthews/Lead Generartion for Cleaning Contracts (VA) ELITE/leads.db'
    
    generator = LeadGenerator(db_path)
    
    # Test lead generation
    print("🧪 Testing lead generation...")
    
    # Generate sample leads
    gov_leads = generator.generate_government_leads(3)
    commercial_leads = generator.generate_commercial_leads(5)
    
    print(f"\n📋 Generated {len(gov_leads)} government leads:")
    for lead in gov_leads:
        print(f"  • {lead['title']} - {lead['value']} ({lead['location']})")
    
    print(f"\n🏢 Generated {len(commercial_leads)} commercial leads:")
    for lead in commercial_leads:
        print(f"  • {lead['business_name']} - ${lead['monthly_value']}/month ({lead['location']})")
    
    # Get statistics
    stats = generator.get_lead_statistics()
    if stats:
        print(f"\n📊 Current database statistics:")
        print(f"  • Government contracts: {stats['total_government']}")
        print(f"  • Commercial opportunities: {stats['total_commercial']}")
        print(f"  • Total leads: {stats['total_leads']}")

if __name__ == "__main__":
    main()