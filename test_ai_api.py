#!/usr/bin/env python3
"""Test AI Assistant API endpoint"""
import requests
import json

# Test locally first
BASE_URL = "http://127.0.0.1:5000"
# Uncomment to test production
# BASE_URL = "https://virginia-contracts-lead-generation.onrender.com"

def test_api():
    print("🔍 Testing AI Assistant API...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test the API endpoint
    url = f"{BASE_URL}/api/ai-assistant-reply"
    payload = {
        "message": "How do I write a proposal?",
        "role": ""
    }
    
    print(f"\n📤 Sending POST to {url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = session.post(
            url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"📄 Response data:")
            print(json.dumps(data, indent=2))
        elif response.status_code == 302:
            print(f"\n⚠️ Redirect (302) - Login required!")
            print(f"Location: {response.headers.get('Location')}")
        elif response.status_code == 401:
            print(f"\n⚠️ Unauthorized (401) - Login required!")
        else:
            print(f"\n❌ Error response:")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("AI ASSISTANT API TEST")
    print("=" * 60)
    test_api()
