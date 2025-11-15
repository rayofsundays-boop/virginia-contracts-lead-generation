# Google API Setup for Render

## Error: GOOGLE_API_KEY not set

You need to add your Google API key as an environment variable in Render.

## Step-by-Step Setup

### 1. Go to Render Dashboard
- Open: https://dashboard.render.com/
- Select your service: **virginia-contracts-lead-generation**

### 2. Add Environment Variables
- Click **"Environment"** in the left sidebar
- Click **"Add Environment Variable"** button

**Add Variable 1:**
  - **Key**: `GOOGLE_API_KEY`
  - **Value**: Your Google API key (e.g., `AIzaSyC...`)
  
**Add Variable 2:**
  - **Key**: `GOOGLE_SEARCH_ENGINE_ID`
  - **Value**: Your Custom Search Engine ID (e.g., `e1234567...`)

- Click **"Save Changes"** after adding both

### 3. Restart Service (if needed)
Render usually auto-restarts when you add environment variables, but if not:
- Click **"Manual Deploy"** → **"Deploy latest commit"**
- Wait 2-3 minutes for restart

### 4. Verify Setup
Run this on Render Shell to check if both variables are set:

```bash
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
```

### 5. Run Lead Generation
Once the key is set:

```bash
python run_google_lead_generation.py
```

## Your Google Credentials

You have two credentials to set:

**1. Google API Key** (`GOOGLE_API_KEY`)
   - Format: `AIzaSyC...` (39 characters)
   - Used for: Places API, Geocoding API, Custom Search API
   - Get it from: https://console.cloud.google.com/apis/credentials

**2. Custom Search Engine ID** (`GOOGLE_SEARCH_ENGINE_ID`)
   - Format: `e1234567890abcdef...` (~40 characters)
   - Used for: Finding RFPs and bid opportunities
   - Get it from: https://programmablesearchengine.google.com/controlpanel/all

## What the Key Enables

With the Google API key set, the script will:
- 🔍 Search 5 Virginia cities for commercial properties
- 🏢 Find offices, hospitals, malls, schools, hotels, gyms, restaurants
- 📞 Get real phone numbers and addresses
- ⭐ Include Google ratings and review counts
- 💾 Save 50-150+ leads to your database automatically

## Troubleshooting

**If you see "Quota exceeded":**
- Free tier: 2,500 requests/day
- Each city search = ~20 requests
- Script searches 5 cities × 2 (properties + managers) = ~200 requests total

**If you see "API not enabled":**
- Go to: https://console.cloud.google.com/apis/library
- Enable: **Places API** and **Geocoding API**

**If you see "Invalid API key":**
- Check that you copied the full key (no spaces)
- Verify the key is active in Google Cloud Console
