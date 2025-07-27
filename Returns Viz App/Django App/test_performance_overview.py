#!/usr/bin/env python
"""Test the Performance Overview functionality"""

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

def test_performance_overview():
    """Test the performance overview functionality"""
    print("Testing Performance Overview...")
    
    client = Client()
    
    # Test data
    test_data = {
        'ticker': 'QQQ',
        'period': 'Custom',
        'start_year': 2017,
        'end_year': 2023
    }
    
    print(f"Testing {test_data['ticker']} from {test_data['start_year']} to {test_data['end_year']}")
    
    # Make POST request
    response = client.post(
        '/api/get-data/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if 'performance_overview' in data and data['performance_overview']:
            perf = data['performance_overview']
            
            print("\n[OK] Performance Overview received")
            print("\n[Return] Return Metrics:")
            print(f"  CAGR: {perf['return_metrics']['cagr']:.2%}")
            print(f"  Total Return: {perf['return_metrics']['total_return']:.2%}")
            print(f"  Best Year: {perf['return_metrics']['best_year']:.2%} ({perf['return_metrics']['best_year_date']})")
            print(f"  Worst Year: {perf['return_metrics']['worst_year']:.2%} ({perf['return_metrics']['worst_year_date']})")
            print(f"  Win Rate: {perf['return_metrics']['win_rate']:.1%}")
            
            print("\n[Risk] Risk Metrics:")
            print(f"  Volatility: {perf['risk_metrics']['volatility']:.2%}")
            print(f"  Max Drawdown: {perf['risk_metrics']['maximum_drawdown']:.2%}")
            recovery = perf['risk_metrics']['recovery_days']
            recovery_str = f"{recovery} days" if recovery else "Still recovering"
            print(f"  Recovery Time: {recovery_str}")
            print(f"  VaR (5%): {perf['risk_metrics']['var_5']:.2%}")
            
            print("\n[Risk-Adjusted] Risk-Adjusted Metrics:")
            print(f"  Sharpe Ratio: {perf['risk_adjusted_metrics']['sharpe_ratio']:.2f}")
            print(f"  Sortino Ratio: {perf['risk_adjusted_metrics']['sortino_ratio']:.2f}")
            print(f"  Calmar Ratio: {perf['risk_adjusted_metrics']['calmar_ratio']:.2f}")
            
            print("\n[Relative] Relative to S&P 500:")
            beta = perf['relative_metrics']['beta']
            alpha = perf['relative_metrics']['alpha']
            r_squared = perf['relative_metrics']['r_squared']
            
            print(f"  Beta: {beta:.2f}" if beta else "  Beta: N/A")
            print(f"  Alpha: {alpha:.2%}" if alpha else "  Alpha: N/A")
            print(f"  R-Squared: {r_squared:.2f}" if r_squared else "  R-Squared: N/A")
            
            print(f"\n[Period] Period: {perf['period_info']['num_years']:.1f} years, {perf['period_info']['num_observations']} observations")
            
        else:
            print("[ERROR] No performance overview data received")
            
    else:
        print(f"[ERROR] Request failed")
        print(f"Response: {response.content.decode()}")

if __name__ == "__main__":
    test_performance_overview()