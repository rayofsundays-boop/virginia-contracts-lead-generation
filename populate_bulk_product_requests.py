#!/usr/bin/env python3
"""
Populate bulk_product_requests table with real buyer data from buyers_complete_fixed.csv
"""

import sqlite3
import csv
from datetime import datetime, timedelta
import random

# Connect to database
conn = sqlite3.connect('leads.db')
cursor = conn.cursor()

# Create bulk_product_requests table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS bulk_product_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        location TEXT,
        contact_name TEXT,
        contact_email TEXT,
        contact_phone TEXT,
        product_category TEXT NOT NULL,
        specific_products TEXT,
        quantity INTEGER,
        unit_measure TEXT,
        estimated_value TEXT,
        urgency TEXT DEFAULT 'this_month',
        delivery_date TEXT,
        category TEXT NOT NULL,
        special_requirements TEXT,
        website_url TEXT,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("✅ Created bulk_product_requests table")

# Read buyers CSV
buyers = []
with open('buyers_complete_fixed.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        buyers.append(row)

print(f"📊 Found {len(buyers)} buyers in CSV")

# Map categories to specific product needs
product_needs = {
    'Healthcare': {
        'products': ['Medical-grade disinfectants', 'Hospital sanitizers', 'Sterile cleaning supplies', 'EPA-registered cleaners'],
        'category': 'Cleaning Chemicals',
        'requirements': 'Must meet healthcare regulations and EPA standards'
    },
    'Education': {
        'products': ['Floor care products', 'Restroom supplies', 'Multi-surface cleaners', 'Paper products'],
        'category': 'Janitorial Supplies',
        'requirements': 'Child-safe products, bulk quantities for multiple facilities'
    },
    'Hospitality': {
        'products': ['Housekeeping chemicals', 'Laundry supplies', 'Room amenities', 'Disinfectants'],
        'category': 'Hospitality Supplies',
        'requirements': 'High-quality, guest-safe products with pleasant scents'
    },
    'Facilities Management': {
        'products': ['Industrial cleaners', 'Floor wax and polish', 'HVAC cleaning supplies', 'Maintenance chemicals'],
        'category': 'Facility Maintenance',
        'requirements': 'Commercial-grade products for large facilities'
    },
    'Airport': {
        'products': ['High-traffic floor care', 'Restroom supplies', 'Glass cleaners', 'Deodorizers'],
        'category': 'Commercial Cleaning',
        'requirements': '24/7 availability, fast-drying formulas'
    },
    'Retail': {
        'products': ['Display cleaners', 'Floor maintenance', 'Shopping cart sanitizers', 'Window cleaners'],
        'category': 'Retail Supplies',
        'requirements': 'Non-toxic, quick-drying, odorless preferred'
    },
    'Manufacturing': {
        'products': ['Industrial degreasers', 'Heavy-duty cleaners', 'Safety equipment', 'Spill containment'],
        'category': 'Industrial Supplies',
        'requirements': 'OSHA compliant, heavy-duty formulations'
    },
    'Senior Care': {
        'products': ['Gentle sanitizers', 'Odor control', 'Infection control products', 'Soft surface cleaners'],
        'category': 'Healthcare Supplies',
        'requirements': 'Elderly-safe, hypoallergenic products'
    }
}

# Urgency levels
urgencies = ['immediate', 'this_week', 'this_month', 'flexible']
urgency_weights = [10, 20, 40, 30]  # More realistic distribution

# Select diverse buyers from different states and categories
selected_buyers = []
states_covered = set()
categories_covered = set()

# Prioritize Virginia buyers
va_buyers = [b for b in buyers if 'VA' in b.get('location', '')]
print(f"🎯 Found {len(va_buyers)} Virginia buyers")

# Add Virginia buyers first
for buyer in va_buyers[:8]:
    selected_buyers.append(buyer)
    states_covered.add('VA')
    categories_covered.add(buyer.get('product_category', ''))

# Add buyers from other states for diversity
for buyer in buyers:
    if len(selected_buyers) >= 25:
        break
    
    state = buyer.get('location', '').split(',')[-1].strip()
    category = buyer.get('product_category', '')
    
    # Add if we haven't covered this state yet or need more diversity
    if state not in states_covered or len(selected_buyers) < 20:
        selected_buyers.append(buyer)
        states_covered.add(state)
        categories_covered.add(category)

print(f"✅ Selected {len(selected_buyers)} buyers from {len(states_covered)} states")
print(f"📋 Categories: {', '.join(sorted(categories_covered))}")

# Insert bulk product requests
inserted = 0
for buyer in selected_buyers:
    category = buyer.get('product_category', 'Facilities Management')
    product_info = product_needs.get(category, product_needs['Facilities Management'])
    
    # Random quantity based on organization size
    estimated_val = buyer.get('estimated_value', '$500,000')
    if '$5,000,000' in estimated_val:
        quantity = random.randint(5000, 15000)
    elif '$2,000,000' in estimated_val:
        quantity = random.randint(2000, 8000)
    else:
        quantity = random.randint(500, 3000)
    
    # Delivery date (1-90 days from now)
    days_ahead = random.randint(15, 90)
    delivery_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # Pick urgency
    urgency = random.choices(urgencies, weights=urgency_weights)[0]
    
    # Specific products (pick 1-3 items)
    num_products = random.randint(1, 3)
    specific_products = ', '.join(random.sample(product_info['products'], num_products))
    
    cursor.execute("""
        INSERT INTO bulk_product_requests 
        (company_name, location, contact_name, contact_email, contact_phone,
         product_category, specific_products, quantity, unit_measure, estimated_value,
         urgency, delivery_date, category, special_requirements, website_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        buyer.get('agency', 'Unknown Agency'),
        buyer.get('location', ''),
        buyer.get('contact_name', 'Procurement Office'),
        buyer.get('contact_email', ''),
        buyer.get('contact_phone', ''),
        category,
        specific_products,
        quantity,
        'units',
        buyer.get('estimated_value', '$500,000 - $2,000,000'),
        urgency,
        delivery_date,
        product_info['category'],
        product_info['requirements'],
        buyer.get('website_url', ''),
        'open'
    ))
    inserted += 1

conn.commit()
conn.close()

print(f"\n✅ Successfully inserted {inserted} bulk product requests")
print(f"🎯 States covered: {', '.join(sorted(states_covered))}")
print(f"📦 Product categories: {', '.join(sorted(categories_covered))}")
print("\n🚀 Ready to view at: http://127.0.0.1:8080/bulk-products")
