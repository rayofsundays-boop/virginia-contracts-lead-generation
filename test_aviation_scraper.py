"""
Quick test of aviation scraper functionality
Tests the scraping logic without running the full scraper
"""

from aviation_scraper import google_search, scrape_page, extract_contact_info, extract_deadline

print("="*70)
print("✈️ AVIATION SCRAPER TEST")
print("="*70)

# Test 1: Google Search
print("\n📡 Test 1: Google Search")
print("Query: 'Washington Dulles IAD MWAA procurement'")
try:
    links = google_search("Washington Dulles IAD MWAA procurement", num_results=2)
    print(f"✅ Found {len(links)} links")
    for i, link in enumerate(links, 1):
        print(f"  {i}. {link[:80]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Contact Extraction
print("\n📧 Test 2: Contact Extraction")
test_text = """
Please contact our procurement office at procurement@airport.com or call (703) 555-1234.
You may also reach John Smith at john.smith@mwaa.com or (571) 123-4567.
"""
try:
    contacts = extract_contact_info(test_text)
    print(f"✅ Extracted contacts:")
    print(f"  Email: {contacts.get('email', 'None')}")
    print(f"  Phone: {contacts.get('phone', 'None')}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Deadline Extraction
print("\n📅 Test 3: Deadline Extraction")
test_deadline_text = """
Proposals are due by 12/31/2025. The deadline for submission is strict.
Please submit your bid before 01-15-2026.
"""
try:
    deadline = extract_deadline(test_deadline_text)
    print(f"✅ Found deadline: {deadline}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Page Scraping (using a real procurement site)
print("\n🌐 Test 4: Page Scraping")
print("Testing with MWAA website...")
try:
    result = scrape_page("https://www.mwaa.com/business-opportunities")
    if result:
        print(f"✅ Opportunity detected!")
        print(f"  Title: {result['title'][:60]}")
        print(f"  Keywords: {', '.join(result['detected_keywords'][:5])}")
        print(f"  URL: {result['url'][:60]}")
    else:
        print("ℹ️ No opportunity keywords detected on this page (expected)")
except Exception as e:
    print(f"⚠️ Error: {e}")

print("\n" + "="*70)
print("✅ TEST COMPLETE")
print("="*70)
print("\nℹ️ To run the full scraper:")
print("  python aviation_scraper.py")
print("\nℹ️ Or use the web interface:")
print("  /aviation-cleaning-leads → Click 'Run Scraper' (admin only)")
