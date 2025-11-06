"""
Add Virginia eVA procurement opportunities manually to the database
Based on data from https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp
"""

import sqlite3
from datetime import datetime

DB_PATH = 'leads.db'

# Virginia eVA opportunities (manually curated from the website)
eva_opportunities = [
    {
        'title': 'Future Procurement - Delivered Aggregate-Martinsville',
        'agency': 'Virginia Department of Transportation',
        'location': 'Martinsville, Virginia',
        'value': 0,
        'deadline': '11/12/2025',
        'description': 'FPR 106313 - Delivered aggregate materials for VDOT Martinsville operations.\nEstimated Issue Date: 11/12/25\nCategory: FPR Supplies\nBuyer: Patty Harvey (patty.harvey@vdot.virginia.gov) | 540-375-3570',
        'naics_code': '',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Future Procurement - Delivered Stock Stone for Franklin Co AHQs',
        'agency': 'Virginia Department of Transportation',
        'location': 'Franklin County, Virginia',
        'value': 0,
        'deadline': '01/28/2026',
        'description': 'FPR 106312 - Delivered stock stone materials for Franklin County Area Headquarters.\nEstimated Issue Date: 1/28/26\nCategory: FPR Supplies\nBuyer: Michelle Braxton (Michelle2.Braxton@vdot.virginia.gov) | 540-378-5089',
        'naics_code': '',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'AUTO LIFT INSPECTIONS AND REPAIR SERVICES',
        'agency': 'Virginia Department of Transportation',
        'location': 'Virginia',
        'value': 0,
        'deadline': '12/24/2025',
        'description': 'FPR 106068 - Auto lift inspection and repair services for VDOT facilities.\nEstimated Issue Date: 12/24/25\nCategory: FPR Non-Professional Services\nBuyer: Rebecca Coburn (rebecca.coburn@VDOT.Virginia.gov) | 540-332-9161',
        'naics_code': '811310',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Future Procurement - Painting Services for the Salem District',
        'agency': 'Virginia Department of Transportation',
        'location': 'Salem, Virginia',
        'value': 0,
        'deadline': '01/08/2026',
        'description': 'FPR 104858 - Professional painting services for VDOT Salem District facilities and structures.\nEstimated Issue Date: 1/8/26\nCategory: FPR Non-Professional Services\nBuyer: Michelle Braxton (Michelle2.Braxton@vdot.virginia.gov) | 540-378-5089',
        'naics_code': '238320',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Pest Control Service',
        'agency': 'Virginia Department of Transportation',
        'location': 'Virginia',
        'value': 0,
        'deadline': '11/03/2025',
        'description': 'FPR 102538 - Pest control services for VDOT facilities across Virginia.\nEstimated Issue Date: 11/3/25\nCategory: FPR Non-Professional Services\nBuyer: Chelsa Taylor (chelsa.taylor@vdot.virginia.gov) | 276-696-3337',
        'naics_code': '561710',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Future Procurement - Conference Facility & Lodging Services',
        'agency': 'Department of Elections',
        'location': 'Virginia',
        'value': 0,
        'deadline': '11/09/2025',
        'description': 'FPR 104948 - Conference facility and lodging services for Virginia Department of Elections.\nEstimated Issue Date: 11/9/25\nCategory: FPR Non-Professional Services\nBuyer: Rebecca Mahone (rebecca.mahone@dgs.virginia.gov) | 804-432-5612',
        'naics_code': '721110',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Hired Equipment w/Operator',
        'agency': 'Virginia Department of Transportation',
        'location': 'Virginia',
        'value': 7500000,
        'deadline': '11/30/2025',
        'description': 'FPR 103614 - Hired equipment with operator services for VDOT operations.\nEstimated Issue Date: 11/30/25\nEstimated Price Range: $5,000,000.00 - $9,999,999.99\nCategory: FPR Non-Professional Services\nBuyer: Kim Dobra (kim.dobra@vdot.virginia.gov) | 804-773-1304',
        'naics_code': '532412',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Traffic Control - Structure & Bridge',
        'agency': 'Virginia Department of Transportation',
        'location': 'Virginia',
        'value': 0,
        'deadline': '12/31/2025',
        'description': 'FPR 103340 - Traffic control services for structure and bridge operations.\nEstimated Issue Date: 12/31/25\nCategory: FPR Non-Professional Services\nBuyer: Patty Harvey (patty.harvey@vdot.virginia.gov) | 540-375-3570',
        'naics_code': '561990',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'FUTURE PROCUREMENT - AUTO LIFT INSPECTION AND REPAIR SERVICES',
        'agency': 'Virginia Department of Transportation',
        'location': 'Virginia',
        'value': 0,
        'deadline': '12/10/2025',
        'description': 'FPR 102909 - Auto lift inspection and repair services for VDOT facilities.\nEstimated Issue Date: 12/10/25\nCategory: FPR Non-Professional Services\nBuyer: Rebecca Coburn (rebecca.coburn@VDOT.Virginia.gov) | 540-332-9161',
        'naics_code': '811310',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'FAM-25-039 Future Procurement - Regional Post Permanency Consortia Services',
        'agency': 'Department of Social Services',
        'location': 'Virginia',
        'value': 3000000,
        'deadline': '11/17/2025',
        'description': 'FPR 99625-3 - Regional post permanency consortia services for Virginia DSS.\nEstimated Issue Date: 11/17/25\nEstimated Price Range: $1,000,000.00 - $4,999,999.99\nCategory: FPR Tech Non-Professional Services\nBuyer: Amanda Howell (amanda.howell@dss.virginia.gov) | 804-726-7390',
        'naics_code': '624110',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Furnish & Install CCTV Surveillance System with Subscription Package',
        'agency': 'Science Museum of Virginia',
        'location': 'Richmond, Virginia',
        'value': 0,
        'deadline': 'Not specified',
        'description': 'FPR 103822 - Furnish and install CCTV surveillance system with subscription package for the Science Museum of Virginia.\nCategory: FPR Small Priority Tech Equipment\nBuyer: Science Museum Procurement',
        'naics_code': '238210',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'FAM-25-038 Comprehensive Child Welfare Information System (CCWIS)',
        'agency': 'Department of Social Services',
        'location': 'Virginia',
        'value': 30000000,
        'deadline': '04/06/2026',
        'description': 'FPR 85740-2 - Design, development, and implementation RFP for Comprehensive Child Welfare Information System.\nEstimated Issue Date: 4/6/26\nEstimated Price Range: $10,000,000.00 - $49,999,999.99\nCategory: FPR Tech Non-Professional Services\nBuyer: Amanda Howell (amanda.howell@dss.virginia.gov) | 804-726-7390',
        'naics_code': '541512',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'CVS-26-011 211 Virginia',
        'agency': 'Department of Social Services',
        'location': 'Virginia',
        'value': 0,
        'deadline': '06/01/2026',
        'description': 'FPR 105510-1 - 211 Virginia helpline and information services.\nEstimated Issue Date: 6/1/26\nCategory: FPR Tech Non-Professional Services\nBuyer: Michael Jackson (michael.jackson@dss.virginia.gov) | 804-726-8083',
        'naics_code': '561422',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    },
    {
        'title': 'Future Procurement - Merchant Card Services',
        'agency': 'Department of Treasury',
        'location': 'Richmond, Virginia',
        'value': 0,
        'deadline': 'Not specified',
        'description': 'FPR 103026 - Merchant card services for Virginia Department of Treasury.\nCategory: FPR Non-Professional Services\nBuyer: Vernita Boone (vernita.boone@trs.virginia.gov) | 804-845-6439',
        'naics_code': '522320',
        'website_url': 'https://mvendor.cgieva.com/Vendor/public/AllOpportunities.jsp?doccddesc=Future%20Procurement%20(FPR)'
    }
]

def add_opportunities_to_db():
    """Add opportunities to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    print("=" * 60)
    print("📊 ADDING VIRGINIA eVA OPPORTUNITIES TO DATABASE")
    print("=" * 60)
    
    for opp in eva_opportunities:
        try:
            # Check if opportunity already exists
            cursor.execute('''
                SELECT id FROM contracts 
                WHERE title = ? AND agency = ?
            ''', (opp['title'], opp['agency']))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE contracts SET
                        location = ?, value = ?, deadline = ?, 
                        description = ?, naics_code = ?, website_url = ?
                    WHERE id = ?
                ''', (
                    opp['location'], opp['value'], opp['deadline'], 
                    opp['description'], opp['naics_code'], opp['website_url'],
                    existing[0]
                ))
                updated_count += 1
                print(f"🔄 Updated: {opp['title'][:60]}")
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO contracts (
                        title, agency, location, value, deadline, 
                        description, naics_code, website_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    opp['title'], opp['agency'], opp['location'], 
                    opp['value'], opp['deadline'], opp['description'], 
                    opp['naics_code'], opp['website_url']
                ))
                added_count += 1
                print(f"✅ Added: {opp['title'][:60]}")
                
        except Exception as e:
            print(f"❌ Error with '{opp['title'][:40]}': {e}")
            skipped_count += 1
            continue
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print(f"✅ Added: {added_count} new opportunities")
    print(f"🔄 Updated: {updated_count} existing opportunities")
    if skipped_count > 0:
        print(f"⏭️  Skipped: {skipped_count} opportunities (errors)")
    print(f"📊 Total: {added_count + updated_count + skipped_count} processed")
    print("=" * 60)

if __name__ == "__main__":
    add_opportunities_to_db()
