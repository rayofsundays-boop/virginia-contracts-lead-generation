#!/usr/bin/env python3
"""
Route Audit Script - Tests all buttons and links for internal errors
"""
import requests
from urllib.parse import urljoin
import sys

# Base URL for the Flask app
BASE_URL = "http://127.0.0.1:8080"

# List of all public routes to test
ROUTES_TO_TEST = [
    # Main pages
    ('/', 'Home Page'),
    ('/home', 'Home Alt'),
    ('/about', 'About Page'),
    ('/contact', 'Contact Page'),
    
    # Authentication pages
    ('/register', 'Registration Page'),
    ('/signin', 'Sign In Page'),
    ('/auth', 'Auth Page'),
    
    # Contract pages
    ('/contracts', 'Contracts Main'),
    ('/quick-wins', 'Quick Wins (CRITICAL)'),
    ('/supply-contracts', 'Supply Contracts Alt'),
    ('/educational-contracts', 'Educational Contracts'),
    ('/industry-days', 'Industry Days'),
    ('/federal-contracts', 'Federal Contracts'),
    ('/commercial-contracts', 'Commercial Contracts'),
    
    # City pages
    ('/city/Hampton', 'Hampton City Page'),
    ('/city/Norfolk', 'Norfolk City Page'),
    ('/city/Virginia Beach', 'Virginia Beach Page'),
    ('/city/Newport News', 'Newport News Page'),
    ('/city/Williamsburg', 'Williamsburg Page'),
    
    # Tools and Resources
    ('/toolbox', 'Resource Toolbox'),
    ('/proposal-support', 'Proposal Support'),
    ('/branding-materials', 'Branding Materials'),
    ('/consultations', 'Consultations'),
    ('/proposal-templates', 'Proposal Templates'),
    ('/ai-assistant', 'AI Assistant'),
    ('/pricing-calculator', 'Pricing Calculator'),
    ('/capability-statement', 'Capability Statement'),
    ('/procurement-lifecycle', 'Procurement Lifecycle'),
    
    # User pages  
    ('/subscription', 'Subscription Page'),
    ('/credits', 'Credits Page (DUPLICATE ROUTE)'),
    ('/payment', 'Payment Page'),
    
    # Legal
    ('/terms', 'Terms of Service'),
    ('/privacy', 'Privacy Policy'),
    
    # Other
    ('/partnerships', 'Partnerships'),
    ('/customer-reviews', 'Customer Reviews'),
    ('/survey', 'Survey Page'),
    ('/landing', 'Landing Page'),
]

# Protected routes (require login - expect redirect)
PROTECTED_ROUTES = [
    ('/customer-dashboard', 'Customer Dashboard'),
    ('/user-profile', 'User Profile'),
    ('/saved-leads', 'Saved Leads'),
    ('/customer-leads', 'Customer Leads'),
]

# Admin routes (require admin - expect redirect)
ADMIN_ROUTES = [
    ('/admin', 'Admin Dashboard'),
    ('/admin-panel', 'Admin Panel'),
    ('/admin-enhanced', 'Enhanced Admin'),
    ('/admin-login', 'Admin Login'),
]

def test_route(route, description):
    """Test a single route and return status"""
    try:
        url = urljoin(BASE_URL, route)
        response = requests.get(url, allow_redirects=False, timeout=5)
        
        # Check status code
        if response.status_code == 500:
            return f"❌ INTERNAL ERROR: {description} ({route})"
        elif response.status_code == 404:
            return f"⚠️  NOT FOUND: {description} ({route})"
        elif response.status_code in [200, 302, 301]:
            return f"✅ OK: {description} ({route}) - Status {response.status_code}"
        else:
            return f"⚡ UNEXPECTED: {description} ({route}) - Status {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return f"🔌 CONNECTION FAILED: {description} ({route}) - Server not running?"
    except requests.exceptions.Timeout:
        return f"⏱️  TIMEOUT: {description} ({route})"
    except Exception as e:
        return f"💥 ERROR: {description} ({route}) - {str(e)}"

def main():
    print("=" * 80)
    print("FLASK ROUTE AUDIT - Virginia Contracts Lead Generation")
    print("=" * 80)
    print(f"\nTesting base URL: {BASE_URL}")
    print("Please ensure Flask server is running on port 5000\n")
    
    errors = []
    warnings = []
    success = []
    
    # Test public routes
    print("\n" + "=" * 80)
    print("TESTING PUBLIC ROUTES")
    print("=" * 80)
    for route, description in ROUTES_TO_TEST:
        result = test_route(route, description)
        print(result)
        if "❌" in result:
            errors.append(result)
        elif "⚠️" in result:
            warnings.append(result)
        elif "✅" in result:
            success.append(result)
    
    # Test protected routes
    print("\n" + "=" * 80)
    print("TESTING PROTECTED ROUTES (Should redirect to login)")
    print("=" * 80)
    for route, description in PROTECTED_ROUTES:
        result = test_route(route, description)
        print(result)
        if "❌" in result:
            errors.append(result)
        elif "⚠️" in result:
            warnings.append(result)
            
    # Test admin routes
    print("\n" + "=" * 80)
    print("TESTING ADMIN ROUTES (Should redirect or show login)")
    print("=" * 80)
    for route, description in ADMIN_ROUTES:
        result = test_route(route, description)
        print(result)
        if "❌" in result:
            errors.append(result)
        elif "⚠️" in result:
            warnings.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {len(success)}")
    print(f"⚠️  Warnings: {len(warnings)}")
    print(f"❌ Errors (500): {len(errors)}")
    
    if errors:
        print("\n🚨 CRITICAL ISSUES FOUND:")
        print("-" * 80)
        for error in errors:
            print(error)
    
    if warnings:
        print("\n⚠️  WARNINGS (404 Not Found):")
        print("-" * 80)
        for warning in warnings:
            print(warning)
    
    print("\n" + "=" * 80)
    print("KNOWN ISSUES TO FIX:")
    print("=" * 80)
    print("1. Duplicate /credits route (lines 6517 & 6808) - May cause conflicts")
    print("2. Check all url_for('quick_wins') references - Route exists but verify template rendering")
    print("\nAudit complete!")
    print("=" * 80)
    
    # Return exit code based on errors
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
