#!/usr/bin/env python3
"""
Check state procurement portal URLs and fix DNS errors using OpenAI.
"""

import requests
import re
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

# Read the template file
with open('templates/state_procurement_portals.html', 'r') as f:
    content = f.read()

# Extract all URLs
url_pattern = r'href="(https?://[^"]+)"'
urls = re.findall(url_pattern, content)

# Filter to only procurement-related URLs (not Bootstrap, Font Awesome, etc.)
procurement_urls = [url for url in urls if 'bootstrap' not in url and 'fontawesome' not in url and 'cdnjs' not in url and 'jsdelivr' not in url and url.startswith('http')]

print(f"📊 Found {len(procurement_urls)} procurement portal URLs to check\n")

broken_urls = []
dns_errors = []
working_urls = []

for url in procurement_urls:
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            working_urls.append(url)
            print(f"✅ {url}")
        else:
            broken_urls.append((url, response.status_code))
            print(f"❌ {url} - Status: {response.status_code}")
    except requests.exceptions.ConnectionError as e:
        if 'Name or service not known' in str(e) or 'nodename nor servname provided' in str(e):
            dns_errors.append(url)
            print(f"🔴 DNS ERROR: {url}")
        else:
            broken_urls.append((url, 'Connection Error'))
            print(f"❌ {url} - Connection Error")
    except requests.exceptions.Timeout:
        broken_urls.append((url, 'Timeout'))
        print(f"⏱️ {url} - Timeout")
    except Exception as e:
        broken_urls.append((url, str(e)[:50]))
        print(f"❌ {url} - {str(e)[:50]}")

print(f"\n\n📊 SUMMARY:")
print(f"✅ Working: {len(working_urls)}")
print(f"❌ Broken: {len(broken_urls)}")
print(f"🔴 DNS Errors: {len(dns_errors)}")

if dns_errors:
    print(f"\n\n🔴 DNS ERROR URLS (Need OpenAI Fix):")
    for url in dns_errors:
        print(f"  • {url}")

if broken_urls:
    print(f"\n\n❌ OTHER BROKEN URLS:")
    for url, error in broken_urls:
        print(f"  • {url} - {error}")
