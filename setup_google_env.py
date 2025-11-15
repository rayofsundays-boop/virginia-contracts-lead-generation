"""
Set Google API Environment Variables
Run this on Render Shell to configure your Google API credentials
"""

# YOUR GOOGLE API CREDENTIALS
API_KEY = "YOUR_GOOGLE_API_KEY"  # Replace with your actual API key
SEARCH_ENGINE_ID = "YOUR_CSE_ID"  # Replace with your actual Search Engine ID

# Instructions for setting environment variables in Render:
print("""
╔════════════════════════════════════════════════════════════════╗
║  GOOGLE API ENVIRONMENT VARIABLES SETUP                         ║
╚════════════════════════════════════════════════════════════════╝

📋 Add these environment variables in Render Dashboard:

1. Go to: https://dashboard.render.com/
2. Select: virginia-contracts-lead-generation
3. Click: "Environment" (left sidebar)
4. Add these 2 variables:

┌────────────────────────────────────────────────────────────────┐
│ Variable 1: GOOGLE_API_KEY                                      │
├────────────────────────────────────────────────────────────────┤
│ Key:   GOOGLE_API_KEY                                           │
│ Value: YOUR_GOOGLE_API_KEY (replace with your actual key)      │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Variable 2: GOOGLE_SEARCH_ENGINE_ID                             │
├────────────────────────────────────────────────────────────────┤
│ Key:   GOOGLE_SEARCH_ENGINE_ID                                  │
│ Value: YOUR_CSE_ID (replace with your actual CSE ID)           │
└────────────────────────────────────────────────────────────────┘

5. Click "Save Changes"
6. Service will auto-restart (2-3 minutes)

═══════════════════════════════════════════════════════════════

✅ What These Enable:

🔑 GOOGLE_API_KEY
   → Google Places API (find businesses)
   → Google Geocoding API (convert addresses to coordinates)
   → Google Custom Search API (find RFPs and bid opportunities)

🔍 GOOGLE_SEARCH_ENGINE_ID
   → Custom Search Engine for finding government RFPs
   → Searches for "cleaning contract RFP Virginia"
   → Finds active procurement opportunities

═══════════════════════════════════════════════════════════════

🧪 After Setup, Test With:

python << 'EOF'
import os
api_key = os.environ.get('GOOGLE_API_KEY')
cse_id = os.environ.get('GOOGLE_SEARCH_ENGINE_ID')

if api_key:
    print(f"✅ GOOGLE_API_KEY is set ({api_key[:10]}...)")
else:
    print("❌ GOOGLE_API_KEY is NOT set")

if cse_id:
    print(f"✅ GOOGLE_SEARCH_ENGINE_ID is set ({cse_id[:15]}...)")
else:
    print("⚠️  GOOGLE_SEARCH_ENGINE_ID is NOT set (optional)")
EOF

═══════════════════════════════════════════════════════════════

🚀 Then Run Lead Generation:

python run_google_lead_generation.py

Expected: 50-150+ commercial cleaning leads from 5 Virginia cities!

═══════════════════════════════════════════════════════════════
""")

# Display your current values (for copy/paste reference)
print("\n📝 YOUR CREDENTIALS (copy these):\n")
print(f"GOOGLE_API_KEY = {API_KEY}")
print(f"GOOGLE_SEARCH_ENGINE_ID = {SEARCH_ENGINE_ID}")
print()
