#!/usr/bin/env python3
"""
Script to seed industry_days table on production via admin route
Usage: Run this after deploying to production to populate events
"""

import requests
import sys

def seed_production_events():
    """Seed industry_days events on production"""
    
    # Production URL
    base_url = "https://virginia-contracts-lead-generation.onrender.com"
    
    print("=" * 80)
    print("🌱 SEED INDUSTRY DAYS EVENTS - PRODUCTION")
    print("=" * 80)
    
    # Step 1: You need to be logged in as admin
    print("\n📋 Prerequisites:")
    print("   1. Login to production site as admin")
    print("   2. Copy your session cookie")
    print("   3. Visit the seed URL")
    
    seed_url = f"{base_url}/admin/seed-industry-days"
    
    print(f"\n🔗 Seed URL: {seed_url}")
    print("\n📝 Manual Steps:")
    print("   1. Open browser and go to:")
    print(f"      {base_url}/login")
    print("   2. Login with admin credentials")
    print("   3. Visit seed URL:")
    print(f"      {seed_url}")
    print("   4. Page should show success message or redirect to events page")
    
    print("\n✅ After seeding, visit:")
    print(f"   {base_url}/industry-days-events")
    print("   You should see ~200 events from all 50 states")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    seed_production_events()
