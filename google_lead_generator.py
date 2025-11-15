"""
Google API Lead Generator
Uses Google Places and Custom Search to find real cleaning contract opportunities
"""
import os
import json
import googlemaps
from datetime import datetime
from typing import List, Dict

class GoogleLeadGenerator:
    """Generate cleaning contract leads using Google APIs"""
    
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.gmaps = googlemaps.Client(key=self.api_key)
        self.custom_search_key = os.environ.get('GOOGLE_CUSTOM_SEARCH_KEY', self.api_key)
        self.search_engine_id = os.environ.get('GOOGLE_SEARCH_ENGINE_ID')
    
    def find_commercial_properties(self, city: str, state: str, radius_miles: int = 20) -> List[Dict]:
        """
        Find commercial properties that need cleaning services
        
        Target types:
        - Office buildings
        - Medical facilities
        - Shopping centers
        - Warehouses
        - Schools
        """
        leads = []
        
        # Convert city, state to coordinates
        location = f"{city}, {state}"
        geocode_result = self.gmaps.geocode(location)
        
        if not geocode_result:
            print(f"⚠️  Could not find location: {location}")
            return leads
        
        lat_lng = geocode_result[0]['geometry']['location']
        
        # Property types to search
        property_types = [
            ('office', 'Corporate Office Building'),
            ('hospital', 'Medical Facility'),
            ('shopping_mall', 'Shopping Center'),
            ('school', 'Educational Facility'),
            ('university', 'University Campus'),
            ('warehouse', 'Warehouse/Distribution Center'),
            ('hotel', 'Hotel/Hospitality'),
            ('gym', 'Fitness Center'),
            ('restaurant', 'Restaurant/Food Service')
        ]
        
        radius_meters = radius_miles * 1609.34
        
        for place_type, category in property_types:
            try:
                places_result = self.gmaps.places_nearby(
                    location=lat_lng,
                    radius=radius_meters,
                    type=place_type
                )
                
                for place in places_result.get('results', [])[:5]:  # Top 5 per category
                    place_id = place.get('place_id')
                    
                    # Get detailed info
                    details = self.gmaps.place(place_id=place_id)['result']
                    
                    lead = {
                        'company_name': details.get('name', 'Unknown'),
                        'category': category,
                        'address': details.get('formatted_address', ''),
                        'city': city,
                        'state': state,
                        'phone': details.get('formatted_phone_number', ''),
                        'website': details.get('website', ''),
                        'rating': details.get('rating', 0),
                        'total_ratings': details.get('user_ratings_total', 0),
                        'business_status': details.get('business_status', 'OPERATIONAL'),
                        'place_id': place_id,
                        'types': details.get('types', []),
                        'data_source': 'google_places_api',
                        'discovered_at': datetime.now().isoformat()
                    }
                    
                    # Estimate square footage based on type
                    sqft_estimates = {
                        'office': '10,000 - 50,000 sq ft',
                        'hospital': '50,000 - 200,000 sq ft',
                        'shopping_mall': '100,000 - 500,000 sq ft',
                        'school': '50,000 - 150,000 sq ft',
                        'university': '100,000+ sq ft',
                        'warehouse': '50,000 - 200,000 sq ft',
                        'hotel': '20,000 - 100,000 sq ft',
                        'gym': '5,000 - 20,000 sq ft',
                        'restaurant': '2,000 - 10,000 sq ft'
                    }
                    
                    lead['estimated_sqft'] = sqft_estimates.get(place_type, '10,000+ sq ft')
                    
                    leads.append(lead)
                    
                print(f"✅ Found {len(places_result.get('results', []))} {category} leads in {city}, {state}")
                
            except Exception as e:
                print(f"⚠️  Error searching {category}: {e}")
                continue
        
        return leads
    
    def search_rfps_and_bids(self, keywords: List[str], location: str = None, days_back: int = 30) -> List[Dict]:
        """
        Search for RFPs and bid opportunities using Google Custom Search
        
        Keywords: cleaning contracts, janitorial RFP, facility maintenance, etc.
        """
        if not self.search_engine_id:
            print("⚠️  GOOGLE_SEARCH_ENGINE_ID not configured")
            return []
        
        leads = []
        
        # Custom Search API (requires setup in Google Cloud Console)
        # This is a placeholder - you'll need to implement with the Custom Search JSON API
        # https://developers.google.com/custom-search/v1/overview
        
        search_queries = [
            f"{keyword} {location if location else ''} RFP".strip()
            for keyword in keywords
        ]
        
        print(f"🔍 Searching for: {search_queries}")
        print(f"⚠️  Custom Search API integration pending - requires search engine ID setup")
        
        return leads
    
    def enrich_lead_data(self, company_name: str, city: str, state: str) -> Dict:
        """
        Enrich existing lead with Google data
        Find additional contact info, verify address, get photos, etc.
        """
        query = f"{company_name} {city} {state}"
        
        try:
            places_result = self.gmaps.places(query=query)
            
            if places_result.get('results'):
                place = places_result['results'][0]
                place_id = place.get('place_id')
                
                # Get full details
                details = self.gmaps.place(place_id=place_id)['result']
                
                enriched_data = {
                    'google_verified': True,
                    'phone': details.get('formatted_phone_number', ''),
                    'website': details.get('website', ''),
                    'address': details.get('formatted_address', ''),
                    'rating': details.get('rating', 0),
                    'reviews_count': details.get('user_ratings_total', 0),
                    'photos': [photo.get('photo_reference') for photo in details.get('photos', [])[:3]],
                    'business_hours': details.get('opening_hours', {}).get('weekday_text', []),
                    'place_id': place_id,
                    'google_maps_url': details.get('url', ''),
                    'enriched_at': datetime.now().isoformat()
                }
                
                return enriched_data
        except Exception as e:
            print(f"⚠️  Error enriching {company_name}: {e}")
        
        return {'google_verified': False}
    
    def find_property_managers(self, city: str, state: str, radius_miles: int = 25) -> List[Dict]:
        """
        Find property management companies (potential clients)
        """
        location = f"{city}, {state}"
        geocode_result = self.gmaps.geocode(location)
        
        if not geocode_result:
            return []
        
        lat_lng = geocode_result[0]['geometry']['location']
        radius_meters = radius_miles * 1609.34
        
        leads = []
        
        # Search for property management companies
        places_result = self.gmaps.places_nearby(
            location=lat_lng,
            radius=radius_meters,
            keyword='property management'
        )
        
        for place in places_result.get('results', []):
            place_id = place.get('place_id')
            details = self.gmaps.place(place_id=place_id)['result']
            
            lead = {
                'company_name': details.get('name', 'Unknown'),
                'category': 'Property Management Company',
                'address': details.get('formatted_address', ''),
                'city': city,
                'state': state,
                'phone': details.get('formatted_phone_number', ''),
                'website': details.get('website', ''),
                'rating': details.get('rating', 0),
                'data_source': 'google_places_api',
                'lead_type': 'property_manager',
                'discovered_at': datetime.now().isoformat()
            }
            
            leads.append(lead)
        
        return leads

def demo_usage():
    """Demo: Generate leads for Virginia Beach"""
    generator = GoogleLeadGenerator()
    
    print("\n🔍 Searching for commercial properties in Virginia Beach, VA...")
    leads = generator.find_commercial_properties('Virginia Beach', 'VA', radius_miles=15)
    
    print(f"\n✅ Found {len(leads)} potential leads")
    
    # Show sample
    if leads:
        print("\n📋 Sample leads:")
        for lead in leads[:5]:
            print(f"   • {lead['company_name']} - {lead['category']}")
            print(f"     {lead['address']}")
            print(f"     Phone: {lead.get('phone', 'N/A')}")
            print()
    
    # Save to file
    output_file = 'google_leads_export.json'
    with open(output_file, 'w') as f:
        json.dump(leads, f, indent=2)
    
    print(f"💾 Saved {len(leads)} leads to {output_file}")

if __name__ == '__main__':
    demo_usage()
