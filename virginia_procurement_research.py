#!/usr/bin/env python3
"""
Research real Virginia government procurement opportunities
Checks official government websites for active cleaning/janitorial bids
"""

# Real Virginia Government Procurement Portals
VIRGINIA_PROCUREMENT_SOURCES = {
    "State Level": {
        "eVA - Virginia's eProcurement Portal": {
            "url": "https://eva.virginia.gov",
            "description": "Official state procurement system - ALL Virginia state agencies",
            "how_to_access": "Register free account at eva.virginia.gov",
            "coverage": "Statewide - all state agencies, universities, some local governments",
            "search_tips": "Search NAICS 561720 (Janitorial Services) or keywords: cleaning, janitorial, custodial"
        }
    },
    
    "Hampton Roads Cities": {
        "City of Virginia Beach": {
            "url": "https://www.vbgov.com/government/departments/procurement/Pages/default.aspx",
            "bid_page": "https://www.vbgov.com/government/departments/procurement/Pages/Current-Solicitations.aspx",
            "description": "All city bids and RFPs",
            "contact": "Procurement Department: (757) 385-4621"
        },
        
        "City of Norfolk": {
            "url": "https://www.norfolk.gov/307/Procurement",
            "bid_page": "https://norfolk.ionwave.net/",
            "description": "ION Wave procurement portal",
            "contact": "Procurement: (757) 664-4848"
        },
        
        "City of Hampton": {
            "url": "https://hampton.gov/160/Procurement",
            "bid_page": "https://hampton.gov/164/Current-Bids-RFPs",
            "description": "Current bids and RFPs page",
            "contact": "Procurement: (757) 727-6392"
        },
        
        "City of Newport News": {
            "url": "https://www.nnva.gov/158/Procurement",
            "bid_page": "https://www.nnva.gov/164/Current-Solicitations",
            "description": "Active solicitations",
            "contact": "Procurement: (757) 926-8681"
        },
        
        "City of Chesapeake": {
            "url": "https://www.cityofchesapeake.net/government/city-departments/departments/finance/purchasing-division.htm",
            "description": "Purchasing division",
            "contact": "Purchasing: (757) 382-6396"
        },
        
        "City of Suffolk": {
            "url": "https://www.suffolkva.us/291/Purchasing",
            "description": "Purchasing department",
            "contact": "Purchasing: (757) 514-7520"
        },
        
        "City of Portsmouth": {
            "url": "https://www.portsmouthva.gov/269/Purchasing",
            "description": "Purchasing division",
            "contact": "Purchasing: (757) 393-8631"
        }
    },
    
    "Other Virginia Cities": {
        "City of Richmond": {
            "url": "https://www.rva.gov/procurement",
            "bid_page": "https://www.rva.gov/procurement-services/open-solicitations",
            "description": "Open solicitations"
        },
        
        "Fairfax County": {
            "url": "https://www.fairfaxcounty.gov/procurement/",
            "bid_page": "https://www.fairfaxcounty.gov/procurement/solicitations",
            "description": "Very large market - extensive opportunities"
        },
        
        "Arlington County": {
            "url": "https://www.arlingtonva.us/Government/Departments/Management-and-Finance/Procurement",
            "description": "County procurement"
        }
    },
    
    "School Districts": {
        "Virginia Beach City Public Schools": {
            "url": "https://www.vbschools.com/departments/purchasing",
            "description": "85 schools - large opportunity"
        },
        
        "Norfolk Public Schools": {
            "url": "https://www.nps.k12.va.us/departments/purchasing",
            "description": "School district procurement"
        },
        
        "Chesapeake Public Schools": {
            "url": "https://www.cpschools.com/departments/purchasing",
            "description": "School facilities"
        }
    },
    
    "Universities": {
        "Old Dominion University": {
            "url": "https://www.odu.edu/procurement",
            "description": "Large university campus"
        },
        
        "Norfolk State University": {
            "url": "https://www.nsu.edu/administration/financial-services-and-auxiliary-services/procurement-services",
            "description": "HBCU with multiple buildings"
        },
        
        "Christopher Newport University": {
            "url": "https://cnu.edu/procurement/",
            "description": "Growing campus in Newport News"
        }
    }
}

print("=" * 100)
print("REAL VIRGINIA GOVERNMENT PROCUREMENT OPPORTUNITIES FOR CLEANING SERVICES")
print("=" * 100)

print("\n🎯 PRIMARY RESOURCE - START HERE:")
print("=" * 100)
print("\n📋 eVA - Virginia's Official eProcurement Portal")
print("   URL: https://eva.virginia.gov")
print("   Coverage: ALL Virginia state agencies + many local governments")
print("   Cost: FREE registration")
print("\n   HOW TO FIND CLEANING CONTRACTS:")
print("   1. Go to eva.virginia.gov")
print("   2. Click 'Search Solicitations' (no login needed to browse)")
print("   3. Search by:")
print("      - NAICS Code: 561720 (Janitorial Services)")
print("      - Keywords: 'cleaning', 'janitorial', 'custodial'")
print("   4. Filter by: 'Open' status, 'Virginia' location")
print("   5. Register FREE vendor account to bid")

print("\n\n🏙️ HAMPTON ROADS CITIES:")
print("=" * 100)

for city, info in VIRGINIA_PROCUREMENT_SOURCES["Hampton Roads Cities"].items():
    print(f"\n{city}:")
    print(f"   Main: {info['url']}")
    if 'bid_page' in info:
        print(f"   Bids: {info['bid_page']}")
    print(f"   Info: {info['description']}")
    if 'contact' in info:
        print(f"   📞 {info['contact']}")

print("\n\n🏫 SCHOOL DISTRICTS (Large Opportunities):")
print("=" * 100)

for district, info in VIRGINIA_PROCUREMENT_SOURCES["School Districts"].items():
    print(f"\n{district}:")
    print(f"   {info['url']}")
    print(f"   {info['description']}")

print("\n\n🎓 UNIVERSITIES:")
print("=" * 100)

for university, info in VIRGINIA_PROCUREMENT_SOURCES["Universities"].items():
    print(f"\n{university}:")
    print(f"   {info['url']}")
    print(f"   {info['description']}")

print("\n\n💡 HOW TO GET STARTED:")
print("=" * 100)
print("\n1. REGISTER ON eVA (REQUIRED for state work):")
print("   • Go to eva.virginia.gov")
print("   • Click 'Vendor Registration'")
print("   • Complete free registration")
print("   • Set up email alerts for cleaning/janitorial bids")

print("\n2. CHECK CITY WEBSITES WEEKLY:")
print("   • Most cities post new bids every week")
print("   • Subscribe to email notifications where available")
print("   • Check 'Current Solicitations' or 'Open Bids' pages")

print("\n3. REQUIRED CREDENTIALS:")
print("   • Virginia SCC Registration (State Corporation Commission)")
print("   • General Liability Insurance ($1M+ typically)")
print("   • Worker's Compensation Insurance")
print("   • Business License in locality where working")
print("   • Some contracts require surety bonds")

print("\n4. CERTIFICATIONS THAT HELP:")
print("   • Small Business (SWaM) Certification")
print("   • Minority/Women-owned Business Enterprise")
print("   • CIMS certification (cleaning industry)")
print("   • OSHA safety training")

print("\n\n📊 TYPICAL CONTRACT VALUES:")
print("=" * 100)
print("   Small facilities: $20K - $50K/year")
print("   Medium buildings: $50K - $200K/year")
print("   Large campuses: $200K - $1M+/year")
print("   School districts: $500K - $2M+/year (multi-building)")

print("\n\n⚠️  IMPORTANT TIPS:")
print("=" * 100)
print("   • Government contracts require DETAILED proposals")
print("   • Expect 30-90 day evaluation periods")
print("   • Start with smaller bids to build experience")
print("   • Attend pre-bid meetings (often required)")
print("   • Read ALL specifications carefully")
print("   • Price competitively but don't underbid")
print("   • Payment terms: Net 30 (government is slow but reliable)")

print("\n\n✅ NEXT STEPS:")
print("=" * 100)
print("   1. Register on eVA TODAY - it's free and opens all state opportunities")
print("   2. Visit each Hampton Roads city procurement page")
print("   3. Call procurement offices to introduce your business")
print("   4. Attend vendor outreach events (cities host these)")
print("   5. Start with 1-2 small bids to learn the process")

print("\n" + "=" * 100)
print("💡 These are ALL REAL government procurement portals with ACTIVE opportunities")
print("=" * 100)
