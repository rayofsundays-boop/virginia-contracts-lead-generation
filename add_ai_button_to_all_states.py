#!/usr/bin/env python3
"""
Add 'Find City RFPs (AI)' button to all state cards in state_procurement_portals.html
"""

import re

# State codes mapping
STATE_CODES = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY', 'Washington DC': 'DC'
}

def add_ai_button_to_states():
    """Add AI button to all state cards that don't have it"""
    
    with open('templates/state_procurement_portals.html', 'r') as f:
        content = f.read()
    
    modified = False
    
    for state_name, state_code in STATE_CODES.items():
        # Skip if already has AI button
        button_pattern = f"findCityRFPs('{state_name}', '{state_code}')"
        if button_pattern in content:
            print(f"✓ {state_name} already has AI button")
            continue
        
        # Find the state card
        # Pattern: <div class="card-body"> followed by <p> then first <a href or <button
        state_card_pattern = re.compile(
            rf'<!-- {state_name} -->.*?<div class="card-body">\s*'
            rf'<p[^>]*>.*?</p>\s*'
            rf'(<(?:a href|button)[^>]*>)',
            re.DOTALL | re.IGNORECASE
        )
        
        match = state_card_pattern.search(content)
        if not match:
            print(f"⚠ Could not find card for {state_name}")
            continue
        
        # Determine button color based on state
        btn_color = 'success' if state_name == 'Virginia' else 'success'
        
        # Create AI button HTML
        ai_button = f'''                    <button onclick="findCityRFPs('{state_name}', '{state_code}')" class="btn btn-{btn_color} btn-sm w-100 mb-2">
                        <i class="fas fa-robot me-2"></i>Find City RFPs (AI)
                    </button>
'''
        
        # Insert AI button before the first link/button
        insert_pos = match.start(1)
        content = content[:insert_pos] + ai_button + content[insert_pos:]
        
        modified = True
        print(f"✅ Added AI button to {state_name}")
    
    if modified:
        # Write back to file
        with open('templates/state_procurement_portals.html', 'w') as f:
            f.write(content)
        print(f"\n🎉 Successfully updated state_procurement_portals.html")
    else:
        print(f"\n✓ All states already have AI buttons")

if __name__ == '__main__':
    add_ai_button_to_states()
