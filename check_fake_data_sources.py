#!/usr/bin/env python3
"""
Check for fake data scripts and patterns
"""

import os

print("=" * 80)
print("🔍 CHECKING FOR FAKE DATA GENERATION SCRIPTS")
print("=" * 80)

scripts_to_check = {
    'add_supplier_requests.py': 'Generates synthetic supplier requests',
    'populate_federal_contracts.py': 'Populates federal contracts',
    'quick_populate.py': 'Quick population script',
    'remove_demo_data.py': 'Demo data removal script'
}

found_scripts = []

for script, description in scripts_to_check.items():
    if os.path.exists(script):
        print(f"\n⚠️  FOUND: {script}")
        print(f"    Purpose: {description}")
        
        # Check for fake data patterns
        with open(script, 'r') as f:
            content = f.read()
            
            if 'vacontractshub.com/supplier-requests' in content:
                print("    ❌ Contains fake URL: vacontractshub.com/supplier-requests")
            if '555' in content or 'fake' in content.lower() or 'synthetic' in content.lower():
                print("    ❌ Contains fake data patterns")
            if 'sqlite3.connect' in content or 'DB_PATH' in content:
                print("    ⚠️  Directly modifies SQLite database")
                
        found_scripts.append(script)
    else:
        print(f"✅ Not found: {script}")

print("\n" + "=" * 80)
print("📝 CHECKING app.py FOR AUTO-POPULATE CODE")
print("=" * 80)

if os.path.exists('app.py'):
    with open('app.py', 'r') as f:
        lines = f.readlines()
        
    # Find populate_supply_contracts function
    in_populate_func = False
    has_synthetic_data = False
    line_num = 0
    
    for i, line in enumerate(lines, 1):
        if 'def populate_supply_contracts' in line:
            in_populate_func = True
            line_num = i
            print(f"\n✅ Found populate_supply_contracts function at line {i}")
        
        if in_populate_func:
            if 'supplier_requests = [' in line:
                has_synthetic_data = True
                print(f"⚠️  WARNING: Found synthetic data array at line {i}")
                print("    This generates fake supplier requests!")
            
            if 'vacontractshub.com/supplier-requests' in line:
                print(f"❌ FAKE URL found at line {i}: vacontractshub.com/supplier-requests")
            
            # Check if function ends
            if line.startswith('def ') and i > line_num + 5:
                break
    
    # Check for startup auto-populate
    for i, line in enumerate(lines, 1):
        if 'populate_supply_contracts(force=False)' in line and '#' not in line.split('populate_supply_contracts')[0]:
            print(f"\n⚠️  Auto-populate called at line {i} on app startup")

print("\n" + "=" * 80)
print("🛠️  RECOMMENDED FIXES")
print("=" * 80)

if found_scripts:
    print("\n1️⃣  RENAME/DISABLE FAKE DATA SCRIPTS:")
    for script in found_scripts:
        print(f"    mv {script} {script}.disabled")

print("\n2️⃣  ON RENDER PRODUCTION:")
print("    - Go to Render Dashboard → Your Web Service")
print("    - Click 'Shell' tab")
print("    - Run: python3 delete_fake_supply_contracts.py")
print("    - Type 'DELETE' to confirm")

print("\n3️⃣  SET ENVIRONMENT VARIABLE:")
print("    - Go to Render Dashboard → Your Web Service")
print("    - Go to 'Environment' tab")
print("    - Add: SAM_GOV_API_KEY = your_api_key_from_sam.gov")
print("    - Click 'Save Changes'")

print("\n4️⃣  RESTART APP:")
print("    - Render will auto-restart after env var change")
print("    - OR manually click 'Manual Deploy' → 'Clear build cache & deploy'")

print("\n5️⃣  VERIFY:")
print("    - Visit: https://your-app.onrender.com/quick-wins")
print("    - Should show ~100 REAL nationwide opportunities")
print("    - All URLs should be sam.gov/opp/...")

print("\n" + "=" * 80)
