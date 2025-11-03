import requests
import json
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=90)

payload = {
    "filters": {
        "award_type_codes": ["A", "B", "C", "D"],
        "place_of_performance_scope": "domestic",
        "place_of_performance_locations": [{"state": "VA", "country": "USA"}],
        "time_period": [{
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "date_type": "action_date"
        }]
    },
    "limit": 2,
    "page": 1
}

print("Fetching from USAspending.gov...")
response = requests.post(
    'https://api.usaspending.gov/api/v2/search/spending_by_award/',
    json=payload,
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])
    print(f"\nGot {len(results)} results")
    
    if results:
        print("\nFirst result structure:")
        print(json.dumps(results[0], indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
