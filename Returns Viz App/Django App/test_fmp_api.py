#!/usr/bin/env python
"""Test script for FMP API integration"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'returns_viz.settings')
django.setup()

from etf_analyzer.fmp_api import FMPDataProvider
from etf_analyzer.utils import create_cagr_matrix
import pandas as pd

def test_fmp_api():
    """Test the FMP API integration"""
    print("Testing FMP API integration...")
    
    try:
        # Initialize FMP provider
        fmp = FMPDataProvider()
        print("[OK] FMP provider initialized")
        
        # Test ticker validation
        ticker = "VOO"
        is_valid = fmp.validate_ticker(ticker)
        print(f"[OK] Ticker {ticker} validation: {is_valid}")
        
        # Get ticker info
        info = fmp.get_ticker_info(ticker)
        print(f"[OK] Ticker info: {info}")
        
        # Fetch historical data
        print(f"\nFetching historical data for {ticker}...")
        hist_data = fmp.fetch_historical_data(ticker)
        print(f"[OK] Historical data shape: {hist_data.shape}")
        print(f"[OK] Date range: {hist_data.index.min()} to {hist_data.index.max()}")
        print(f"[OK] Index type: {type(hist_data.index)}")
        print(f"[OK] Index dtype: {hist_data.index.dtype}")
        
        # Calculate annual returns
        print(f"\nCalculating annual returns...")
        annual_returns = fmp.calculate_annual_returns(ticker)
        print(f"[OK] Annual returns shape: {annual_returns.shape}")
        print(f"[OK] Annual returns index type: {type(annual_returns.index)}")
        print(f"[OK] Annual returns index dtype: {annual_returns.index.dtype}")
        print(f"[OK] Annual returns sample (first 5 years):")
        print(annual_returns.head())
        
        # Test CAGR matrix calculation
        print(f"\nTesting CAGR matrix calculation...")
        start_year = 2020
        end_year = 2024
        
        # Filter returns
        filtered_returns = annual_returns.loc[start_year:end_year]
        print(f"[OK] Filtered returns shape: {filtered_returns.shape}")
        print(f"[OK] Filtered years: {filtered_returns.index.tolist()}")
        
        # Create CAGR matrix
        cagr_matrix = create_cagr_matrix(annual_returns, start_year, end_year)
        print(f"[OK] CAGR matrix shape: {cagr_matrix.shape}")
        print(f"[OK] CAGR matrix sample:")
        print(cagr_matrix)
        
    except Exception as e:
        print(f"[ERROR] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fmp_api()