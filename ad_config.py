# Ad Service Configuration
# Update these values with your actual ad network credentials

# ============================================================================
# GOOGLE ADSENSE
# ============================================================================
# Sign up at: https://www.google.com/adsense/
# Your publisher ID: ca-pub-1139151650006174
GOOGLE_ADSENSE_CLIENT_ID = "ca-pub-1139151650006174"

# Ad Slots (Create these in your AdSense dashboard)
# Go to Ads → By site → Your site → New ad unit
ADSENSE_HEADER_AD_SLOT = "XXXXXXXXXX"  # Horizontal banner (728x90 or responsive)
ADSENSE_SIDEBAR_AD_SLOT = "XXXXXXXXXX"  # Vertical rectangle (300x250)
ADSENSE_INFEED_AD_SLOT = "XXXXXXXXXX"  # In-feed ad
ADSENSE_SQUARE_AD_SLOT = "XXXXXXXXXX"  # Square ad (300x250)

# ============================================================================
# CARBON ADS (Alternative - Great for tech/business sites)
# ============================================================================
# Sign up at: https://www.carbonads.net/
CARBON_ADS_SERVE_ID = "YOUR_CARBON_ID"
CARBON_ADS_PLACEMENT = "yoursite"

# ============================================================================
# MEDIA.NET (Alternative - Yahoo/Bing network)
# ============================================================================
# Sign up at: https://www.media.net/
MEDIANET_SITE_ID = "XXXXXX"
MEDIANET_AD_UNIT_1 = "XXXXXX"

# ============================================================================
# CUSTOM ADS (Your own promotional content)
# ============================================================================
CUSTOM_ADS_ENABLED = True

# Example custom ads for your platform
CUSTOM_ADS = [
    {
        "title": "Premium Membership - 50% Off!",
        "description": "Unlock unlimited leads, priority support, and advanced analytics. Limited time offer!",
        "link": "/register?promo=PREMIUM50",
        "cta": "Upgrade Now"
    },
    {
        "title": "Refer a Contractor - Earn $50",
        "description": "Know someone who needs leads? Refer them and earn $50 credit when they subscribe.",
        "link": "/referral",
        "cta": "Start Referring"
    },
    {
        "title": "Featured Contractor Spotlight",
        "description": "Get featured on our homepage and social media. Boost your visibility!",
        "link": "/advertise",
        "cta": "Get Featured"
    }
]

# ============================================================================
# AD PLACEMENT SETTINGS
# ============================================================================
ADS_ENABLED = True  # Master switch for all ads
ADS_SHOW_TO_FREE_USERS = True  # Show ads to non-subscribers
ADS_SHOW_TO_PAID_USERS = False  # Hide ads for paid subscribers (premium feature)

# Ad frequency settings
MAX_ADS_PER_PAGE = 3  # Maximum number of ads on a single page
AD_ROTATION_ENABLED = True  # Rotate custom ads

# ============================================================================
# REVENUE TRACKING
# ============================================================================
# Track estimated ad revenue in your analytics
ESTIMATED_CPM = 2.00  # Estimated CPM (Cost Per Mille) in USD
ESTIMATED_CTR = 0.02  # Estimated Click-Through Rate (2%)

# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================
"""
1. GOOGLE ADSENSE SETUP:
   - Go to https://www.google.com/adsense/
   - Create an account and verify your site
   - Get your publisher ID (ca-pub-XXXXXXX)
   - Create ad units in your dashboard
   - Replace GOOGLE_ADSENSE_CLIENT_ID above
   - Replace ad slot IDs for each ad type
   - Add your site to AdSense (can take 24-48 hours for approval)

2. CARBON ADS SETUP (Alternative):
   - Go to https://www.carbonads.net/
   - Apply for an account (requires quality traffic)
   - Get your serve ID and placement code
   - Update CARBON_ADS_SERVE_ID and CARBON_ADS_PLACEMENT

3. MEDIA.NET SETUP (Alternative):
   - Go to https://www.media.net/
   - Sign up and verify your site
   - Create ad units
   - Get your site ID and ad unit IDs
   - Update MEDIANET_SITE_ID and MEDIANET_AD_UNIT_1

4. CUSTOM ADS:
   - Edit CUSTOM_ADS list above
   - Promote your own services
   - Drive upgrades and referrals
   - Test different messages

5. AD PLACEMENT:
   - Homepage: Header ad + in-feed ad
   - Contract pages: Sidebar ads
   - Lead marketplace: No ads (premium feature)
   - Forms: Header ad only (don't overwhelm users)

6. COMPLIANCE:
   - Add Privacy Policy (required by AdSense)
   - Add Cookie Consent banner
   - Disclose ad relationships
   - Follow ad network guidelines

7. OPTIMIZATION:
   - Use A/B testing for ad placements
   - Monitor CTR and revenue in AdSense dashboard
   - Adjust ad density based on user feedback
   - Consider hiding ads for paid users as premium perk
"""

# ============================================================================
# MONETIZATION STRATEGY
# ============================================================================
"""
REVENUE STREAMS FOR YOUR PLATFORM:

1. SUBSCRIPTION FEES (Primary):
   - Free tier: $0/month (with ads, limited leads)
   - Basic: $49/month (no ads, 10 leads)
   - Pro: $99/month (no ads, unlimited leads, priority)
   - Enterprise: $299/month (no ads, white-label, dedicated support)

2. AD REVENUE (Secondary):
   - Display ads on free tier
   - Estimated: $2-5 CPM
   - 10,000 monthly visitors = $20-50/month
   - 50,000 monthly visitors = $100-250/month
   - 100,000 monthly visitors = $200-500/month

3. LEAD SALES (Primary):
   - Charge per lead: $25-50 per commercial lead
   - Charge per lead: $15-30 per residential lead
   - Bundle pricing: 10 leads for $200

4. FEATURED LISTINGS:
   - Contractors pay to be featured: $99/month
   - Sponsored placement in search results
   - Badge on profile

5. AFFILIATE PARTNERSHIPS:
   - Cleaning supplies: 5-10% commission
   - Insurance providers: $50-200 per referral
   - Business software: $20-100 per sign-up

TARGET: $10,000/month revenue
- Subscriptions: $6,000 (60 Pro subscribers × $99)
- Lead sales: $3,000 (100 leads × $30)
- Ad revenue: $500 (display ads)
- Featured listings: $500 (5 contractors × $99)

GROWTH PLAN:
Month 1-3: Build traffic, collect emails, free tier with ads
Month 4-6: Convert 5% to paid ($49 tier), ad revenue grows
Month 7-12: Launch Pro tier, affiliate partnerships, featured listings
Month 13+: Scale to 100+ paid subscribers, reduce reliance on ads
"""
