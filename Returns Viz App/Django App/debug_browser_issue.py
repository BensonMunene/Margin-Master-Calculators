#!/usr/bin/env python
"""Debug why browser might be showing old content"""

import os
import sys
import django
import json

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'returns_viz.settings')
django.setup()

from django.test import Client

def debug_browser_issue():
    """Debug the browser cache issue with MSFT 2020-2025"""
    print("Debugging browser rendering issue...")
    
    client = Client()
    
    # First get the main page
    print("\n1. Getting main page HTML...")
    main_response = client.get('/')
    print(f"Main page status: {main_response.status_code}")
    
    # Check if the HTML contains the Performance Overview section
    html_content = main_response.content.decode('utf-8')
    
    if 'Performance Overview' in html_content:
        print("[OK] Performance Overview section found in HTML")
    else:
        print("[ERROR] Performance Overview section NOT found in HTML")
    
    if 'updatePerformanceOverview' in html_content:
        print("[OK] updatePerformanceOverview function found in HTML")
    else:
        print("[ERROR] updatePerformanceOverview function NOT found in HTML")
    
    if 'ETF Performance Comparison' in html_content:
        print("[ERROR] OLD 'ETF Performance Comparison' still found in HTML")
    else:
        print("[OK] OLD 'ETF Performance Comparison' not found")
    
    # Now test the API call with MSFT 2020-2025
    print("\n2. Testing MSFT 2020-2025 API call...")
    
    test_data = {
        'ticker': 'MSFT',
        'period': 'Custom',
        'start_year': 2020,
        'end_year': 2025
    }
    
    api_response = client.post(
        '/api/get-data/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"API status: {api_response.status_code}")
    
    if api_response.status_code == 200:
        data = api_response.json()
        
        if 'performance_overview' in data and data['performance_overview']:
            print("[OK] Performance overview data present in API response")
            perf = data['performance_overview']
            
            # Check key metrics
            print(f"   CAGR: {perf['return_metrics']['cagr']:.2%}")
            print(f"   Sharpe: {perf['risk_adjusted_metrics']['sharpe_ratio']:.2f}")
            print(f"   Max DD: {perf['risk_metrics']['maximum_drawdown']:.2%}")
        else:
            print("[ERROR] Performance overview data missing from API response")
            
        # Check for any remaining old comparison data
        if 'comparison' in data:
            print("[ERROR] OLD comparison data still in API response")
        else:
            print("[OK] No old comparison data in API response")
            
    else:
        print(f"[ERROR] API call failed: {api_response.content.decode()}")
    
    print(f"\nSummary:")
    print(f"   - HTML template: {'[OK] Updated' if 'Performance Overview' in html_content else '[ERROR] Still old'}")
    print(f"   - API response: {'[OK] Has performance data' if api_response.status_code == 200 else '[ERROR] Failed'}")
    print(f"   - Browser cache: {'[MAYBE] Likely cached' if 'Performance Overview' in html_content else '[UNKNOWN] Unknown'}")
    
    print(f"\nPossible issues:")
    print(f"   1. Browser cache needs to be cleared (Ctrl+F5)")
    print(f"   2. Template cache in Django")
    print(f"   3. Static files not reloaded")
    print(f"   4. JavaScript error preventing update")

if __name__ == "__main__":
    debug_browser_issue()