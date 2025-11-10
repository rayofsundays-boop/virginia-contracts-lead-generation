#!/usr/bin/env python3
"""
Customize product categories for cleaning industry specificity
"""

import sqlite3

# Connect to database
conn = sqlite3.connect('leads.db')
cursor = conn.cursor()

# Define new cleaning-focused category mapping
category_mapping = {
    'Facility Maintenance': 'Floor Care & Maintenance',
    'Janitorial Supplies': 'Janitorial Supplies',
    'Hospitality Supplies': 'Hospitality & Lodging',
    'Commercial Cleaning': 'Commercial Building Supplies',
    'Cleaning Chemicals': 'Disinfectants & Sanitizers',
    'Retail Supplies': 'Retail & Shopping Centers',
    'Industrial Supplies': 'Industrial & Manufacturing',
    'Healthcare Supplies': 'Healthcare & Medical'
}

# Get current requests
cursor.execute('SELECT id, category, product_category FROM bulk_product_requests')
requests = cursor.fetchall()

print(f"📊 Updating {len(requests)} product requests...\n")

# Update each category
updates = {}
for req_id, old_category, product_category in requests:
    new_category = category_mapping.get(old_category, old_category)
    
    # Track updates
    if old_category != new_category:
        updates[old_category] = updates.get(old_category, 0) + 1
    
    cursor.execute(
        'UPDATE bulk_product_requests SET category = ? WHERE id = ?',
        (new_category, req_id)
    )

# Also update specific_products to be more detailed based on industry
cursor.execute('SELECT id, product_category, specific_products FROM bulk_product_requests')
products = cursor.fetchall()

product_enhancements = {
    'Healthcare': [
        'EPA-registered disinfectants',
        'Hospital-grade sanitizers', 
        'Bloodborne pathogen cleanup kits',
        'Medical waste disposal supplies',
        'Sterile microfiber cleaning cloths',
        'Anti-microbial floor cleaners'
    ],
    'Education': [
        'Child-safe floor cleaners',
        'Bulk paper towel dispensers',
        'Classroom disinfecting wipes',
        'Cafeteria sanitizing solutions',
        'Playground equipment cleaners',
        'Locker room deodorizers'
    ],
    'Hospitality': [
        'Room turnover cleaning kits',
        'Linen & laundry chemicals',
        'Lobby floor polish',
        'Guest bathroom amenities',
        'Kitchen degreasing supplies',
        'Carpet extraction chemicals'
    ],
    'Facilities Management': [
        'High-traffic floor wax',
        'HVAC coil cleaners',
        'Parking garage pressure wash detergents',
        'Elevator interior cleaners',
        'Window washing systems',
        'Restroom fixture descalers'
    ],
    'Airport': [
        'Fast-drying floor cleaners',
        'TSA-compliant cleaning chemicals',
        'Runway de-icing agents',
        'Terminal glass cleaners',
        'Baggage claim area sanitizers',
        'Food court cleaning supplies'
    ],
    'Retail': [
        'Shopping cart sanitizing stations',
        'Display case cleaners',
        'Anti-static floor treatments',
        'Dressing room deodorizers',
        'Checkout counter disinfectants',
        'Parking lot sweeping compounds'
    ],
    'Manufacturing': [
        'Industrial-strength degreasers',
        'Safety equipment cleaners',
        'Warehouse floor coatings',
        'Machine maintenance chemicals',
        'Oil spill containment supplies',
        'Locker room cleaning kits'
    ],
    'Senior Care': [
        'Hypoallergenic surface cleaners',
        'Odor-neutralizing products',
        'Non-slip floor treatments',
        'Dining area sanitizers',
        'Resident room cleaners',
        'Common area disinfectants'
    ],
    'Corrections': [
        'High-security cleaning supplies',
        'Non-toxic floor cleaners',
        'Facility-wide disinfectants',
        'Kitchen sanitation chemicals',
        'Shower room cleaners',
        'Heavy-duty mops and buckets'
    ],
    'Port': [
        'Marine-grade cleaning chemicals',
        'Salt-resistant cleaners',
        'Warehouse floor degreasers',
        'Loading dock sanitizers',
        'Container washing detergents',
        'Office area cleaning supplies'
    ],
    'Real Estate': [
        'Tenant turnover cleaning kits',
        'Common area maintenance supplies',
        'Lobby floor polish',
        'Elevator cleaning products',
        'Parking structure cleaners',
        'Property management chemicals'
    ]
}

enhanced_count = 0
for req_id, prod_category, current_products in products:
    if prod_category in product_enhancements:
        # Replace generic products with industry-specific ones
        import random
        new_products = random.sample(product_enhancements[prod_category], min(3, len(product_enhancements[prod_category])))
        new_products_str = ', '.join(new_products)
        
        cursor.execute(
            'UPDATE bulk_product_requests SET specific_products = ? WHERE id = ?',
            (new_products_str, req_id)
        )
        enhanced_count += 1

conn.commit()

# Show results
print("✅ Category Updates:")
for old_cat, count in updates.items():
    new_cat = category_mapping[old_cat]
    print(f"  {old_cat} → {new_cat} ({count} requests)")

print(f"\n✅ Enhanced {enhanced_count} product descriptions with industry-specific items")

# Show final distribution
cursor.execute('SELECT category, COUNT(*) FROM bulk_product_requests GROUP BY category ORDER BY COUNT(*) DESC')
final_categories = cursor.fetchall()
print("\n📦 Final Category Distribution:")
for cat, count in final_categories:
    print(f"  {cat}: {count} requests")

conn.close()

print("\n🚀 Categories customized! Refresh: http://127.0.0.1:8080/bulk-products")
