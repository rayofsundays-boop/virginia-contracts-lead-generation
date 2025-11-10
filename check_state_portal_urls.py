"""
State Procurement Portals URL Checker and Fixer
Uses OpenAI to find correct URLs for broken state procurement links
"""
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

# Try to import OpenAI
try:
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    OPENAI_AVAILABLE = True
except:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available - will only check URLs without fixing")

# Extract all URLs from state_procurement_portals.html
def extract_urls_from_template():
    """Extract state names and URLs from the template"""
    urls = []
    
    with open('templates/state_procurement_portals.html', 'r') as f:
        content = f.read()
    
    # Find all state cards
    state_pattern = r'<div class="col-md-6 col-lg-4 state-card" data-state="([^"]+)">(.*?)</div>\s*</div>\s*</div>'
    
    matches = re.findall(state_pattern, content, re.DOTALL)
    
    for state_name, card_content in matches:
        # Extract URLs from this card
        url_pattern = r'href="([^"]+)"'
        card_urls = re.findall(url_pattern, card_content)
        
        for url in card_urls:
            if url.startswith('http'):
                urls.append({
                    'state': state_name.title(),
                    'url': url
                })
    
    return urls

def check_url(url, timeout=10):
    """Check if a URL is accessible"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return {
            'status_code': response.status_code,
            'accessible': response.status_code < 400,
            'final_url': response.url
        }
    except requests.exceptions.SSLError:
        # Try without SSL verification
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True, verify=False)
            return {
                'status_code': response.status_code,
                'accessible': response.status_code < 400,
                'final_url': response.url,
                'note': 'SSL certificate issue'
            }
        except Exception as e:
            return {
                'status_code': None,
                'accessible': False,
                'error': str(e)
            }
    except Exception as e:
        return {
            'status_code': None,
            'accessible': False,
            'error': str(e)
        }

def find_correct_url_with_openai(state, broken_url, description="State Portal"):
    """Use OpenAI to find the correct URL"""
    if not OPENAI_AVAILABLE:
        return None
    
    try:
        prompt = f"""I need to find the correct, current URL for {state}'s government procurement portal.

The old/broken URL was: {broken_url}
This is for: {description}

Please search for the official {state} state government procurement/purchasing/bidding website and provide ONLY the correct URL.
Respond with just the URL, nothing else. Make sure it's the official .gov domain if possible.

Format: https://example.gov"""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that finds official government procurement website URLs. Only respond with the URL, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        suggested_url = response.choices[0].message.content.strip()
        
        # Clean up the response
        suggested_url = suggested_url.replace('```', '').strip()
        if not suggested_url.startswith('http'):
            # Try to extract URL from response
            url_match = re.search(r'https?://[^\s<>"]+', suggested_url)
            if url_match:
                suggested_url = url_match.group(0)
            else:
                return None
        
        # Verify the suggested URL works
        check_result = check_url(suggested_url)
        if check_result['accessible']:
            return {
                'url': suggested_url,
                'verified': True
            }
        else:
            return {
                'url': suggested_url,
                'verified': False,
                'note': 'OpenAI suggested but URL not accessible'
            }
            
    except Exception as e:
        print(f"Error using OpenAI for {state}: {e}")
        return None

def main():
    print("=" * 80)
    print("STATE PROCUREMENT PORTALS - URL CHECKER")
    print("=" * 80)
    print()
    
    # Extract URLs
    print("📋 Extracting URLs from template...")
    urls_data = extract_urls_from_template()
    print(f"✓ Found {len(urls_data)} URLs across {len(set([u['state'] for u in urls_data]))} states")
    print()
    
    # Check each URL
    print("🔍 Checking URLs...")
    print()
    
    broken_urls = []
    working_urls = []
    
    for i, data in enumerate(urls_data, 1):
        state = data['state']
        url = data['url']
        
        print(f"[{i}/{len(urls_data)}] {state}: {url}")
        
        result = check_url(url)
        
        if result['accessible']:
            print(f"  ✅ Working (Status: {result['status_code']})")
            working_urls.append(data)
        else:
            error_msg = result.get('error', f"Status: {result['status_code']}")
            print(f"  ❌ BROKEN - {error_msg}")
            broken_urls.append({**data, 'error': error_msg})
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Working URLs: {len(working_urls)}/{len(urls_data)} ({len(working_urls)/len(urls_data)*100:.1f}%)")
    print(f"❌ Broken URLs: {len(broken_urls)}/{len(urls_data)} ({len(broken_urls)/len(urls_data)*100:.1f}%)")
    print()
    
    if broken_urls:
        print("=" * 80)
        print("BROKEN URLS DETAIL")
        print("=" * 80)
        for data in broken_urls:
            print(f"\n🔴 {data['state']}")
            print(f"   URL: {data['url']}")
            print(f"   Error: {data['error']}")
        print()
        
        # Try to fix with OpenAI
        if OPENAI_AVAILABLE:
            print("=" * 80)
            print("ATTEMPTING TO FIX WITH OPENAI")
            print("=" * 80)
            print()
            
            fixes = []
            for data in broken_urls:
                print(f"🤖 Finding correct URL for {data['state']}...")
                
                # Extract description from URL context
                if 'alison' in data['url'].lower():
                    description = "ALISON Bids Portal"
                elif 'iris' in data['url'].lower():
                    description = "IRIS Bids Portal"
                else:
                    description = "State Procurement Portal"
                
                fix = find_correct_url_with_openai(data['state'], data['url'], description)
                
                if fix and fix.get('verified'):
                    print(f"  ✅ Found working URL: {fix['url']}")
                    fixes.append({
                        'state': data['state'],
                        'old_url': data['url'],
                        'new_url': fix['url'],
                        'description': description
                    })
                elif fix:
                    print(f"  ⚠️ Found URL but not verified: {fix['url']}")
                else:
                    print(f"  ❌ Could not find correct URL")
                
                print()
            
            # Print fixes summary
            if fixes:
                print("=" * 80)
                print("SUGGESTED FIXES")
                print("=" * 80)
                print()
                for fix in fixes:
                    print(f"🔧 {fix['state']} - {fix['description']}")
                    print(f"   Old: {fix['old_url']}")
                    print(f"   New: {fix['new_url']}")
                    print()
                
                # Save fixes to file
                with open('state_portal_url_fixes.txt', 'w') as f:
                    f.write("STATE PROCUREMENT PORTAL URL FIXES\n")
                    f.write("=" * 80 + "\n\n")
                    for fix in fixes:
                        f.write(f"State: {fix['state']}\n")
                        f.write(f"Description: {fix['description']}\n")
                        f.write(f"Old URL: {fix['old_url']}\n")
                        f.write(f"New URL: {fix['new_url']}\n")
                        f.write("\n")
                
                print(f"✅ Fixes saved to state_portal_url_fixes.txt")
        else:
            print("⚠️ OpenAI not available - cannot suggest fixes")
            print("   Install openai and set OPENAI_API_KEY to enable automatic fixes")

if __name__ == '__main__':
    main()
