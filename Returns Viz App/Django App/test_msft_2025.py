#!/usr/bin/env python
"""Test MSFT 2020-2025 specifically"""

import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'returns_viz.settings')
django.setup()

from django.test import Client

def test_msft_2025():
    """Test MSFT 2020-2025"""
    print("Testing MSFT 2020-2025...")
    
    client = Client()
    
    test_data = {
        'ticker': 'MSFT',
        'period': 'Custom',
        'start_year': 2020,
        'end_year': 2025
    }
    
    print(f"Request: {test_data}")
    
    response = client.post(
        '/api/get-data/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Success!")
        
        if 'performance_overview' in data:
            if data['performance_overview']:
                print("Performance overview exists")
                perf = data['performance_overview']
                print(f"Return metrics keys: {list(perf.get('return_metrics', {}).keys())}")
                print(f"Risk metrics keys: {list(perf.get('risk_metrics', {}).keys())}")
            else:
                print("Performance overview is null/empty")
        else:
            print("No performance_overview key in response")
            
        print(f"Response keys: {list(data.keys())}")
        
    else:
        response_text = response.content.decode()
        print(f"Error: {response_text}")

if __name__ == "__main__":
    test_msft_2025()