#!/usr/bin/env python
"""Test the API endpoint directly"""

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

def test_api_endpoint():
    """Test the get_data API endpoint"""
    print("Testing API endpoint...")
    
    client = Client()
    
    # Test data
    test_data = {
        'ticker': 'VOO',
        'period': 'Custom',
        'start_year': 2020,
        'end_year': 2024
    }
    
    print(f"Sending request with data: {test_data}")
    
    # Make POST request
    response = client.post(
        '/api/get-data/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("[OK] Request successful")
        print(f"Available years: {data.get('available_years', {})}")
        print(f"Stats: {data.get('stats', {})}")
        print(f"Comparison tickers: {list(data.get('comparison', {}).keys())}")
    else:
        print(f"[ERROR] Request failed")
        print(f"Response: {response.content.decode()}")

if __name__ == "__main__":
    test_api_endpoint()