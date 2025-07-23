"""
FMP API Data Provider Module
Fetches stock prices, dividends, and economic data from Financial Modeling Prep API
Formats data to match existing DataFrame structures used in Margin App
"""

import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Tuple
import time

class FMPDataProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api"
        
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request with error handling and rate limiting"""
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            time.sleep(0.1)  # Rate limiting
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return {}
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_current_price(_self, ticker: str) -> Optional[float]:
        """Fetch current closing price for ticker"""
        endpoint = f"/v3/quote/{ticker.upper()}"
        data = _self._make_request(endpoint)
        
        if data and len(data) > 0:
            return data[0].get('price', None)
        return None
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_historical_prices(_self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical price data and format to match existing structure"""
        endpoint = f"/v3/historical-price-full/{ticker.upper()}"
        params = {
            'from': start_date,
            'to': end_date
        }
        
        data = _self._make_request(endpoint, params)
        
        if not data or 'historical' not in data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data['historical'])
        
        if df.empty:
            return pd.DataFrame()
        
        # Format to match existing structure
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Rename columns to match existing format
        column_mapping = {
            'date': 'Date',
            'open': 'Open',
            'high': 'High', 
            'low': 'Low',
            'close': 'Close',
            'adjClose': 'Adj Close',
            'volume': 'Volume'
        }
        
        df = df.rename(columns=column_mapping)
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        df.set_index('Date', inplace=True)
        
        return df
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour  
    def fetch_historical_dividends(_self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical dividend data and format to match existing structure"""
        endpoint = f"/v3/historical-price-full/stock_dividend/{ticker.upper()}"
        
        data = _self._make_request(endpoint)
        
        if not data or 'historical' not in data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data['historical'])
        
        if df.empty:
            return pd.DataFrame()
        
        # Format to match existing structure
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
        
        # Rename columns to match existing format
        df = df.rename(columns={
            'date': 'Date',
            'dividend': 'Dividends'
        })
        
        df = df[['Date', 'Dividends']]
        df.set_index('Date', inplace=True)
        
        return df
    
    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def fetch_fed_funds_rate(_self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch Federal Funds Rate data and format to match existing structure"""
        # Try Economic Indicators API first
        endpoint = "/v4/economic"
        params = {
            'name': 'FEDFUNDS',
            'from': start_date,
            'to': end_date
        }
        
        data = _self._make_request(endpoint, params)
        
        # If FEDFUNDS doesn't work, try other possible names
        if not data:
            for fed_name in ['FED_FUNDS_RATE', 'FEDERAL_FUNDS_RATE', 'EFFR']:
                params['name'] = fed_name
                data = _self._make_request(endpoint, params)
                if data:
                    break
        
        # Fallback to Treasury rates if Fed Funds not available
        if not data:
            endpoint = "/v4/treasury"
            params = {
                'from': start_date,
                'to': end_date
            }
            data = _self._make_request(endpoint, params)
            
            if data:
                # Use 3-month treasury as proxy for fed funds rate
                df = pd.DataFrame(data)
                if not df.empty and 'month3' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                    df = df.rename(columns={
                        'date': 'Date',
                        'month3': 'FedFunds (%)'
                    })
                    df['FedFunds + 1.5%'] = df['FedFunds (%)'] + 1.5
                    df = df[['Date', 'FedFunds (%)', 'FedFunds + 1.5%']]
                    df.set_index('Date', inplace=True)
                    return df
        
        if not data:
            # Create empty DataFrame with expected structure
            return pd.DataFrame(columns=['Date', 'FedFunds (%)', 'FedFunds + 1.5%']).set_index('Date')
        
        # Process economic data
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=['Date', 'FedFunds (%)', 'FedFunds + 1.5%']).set_index('Date')
        
        df['date'] = pd.to_datetime(df['date'])  
        df = df.sort_values('date')
        
        # Rename and format
        df = df.rename(columns={
            'date': 'Date',
            'value': 'FedFunds (%)'
        })
        
        df['FedFunds + 1.5%'] = df['FedFunds (%)'] + 1.5
        df = df[['Date', 'FedFunds (%)', 'FedFunds + 1.5%']]
        df.set_index('Date', inplace=True)
        
        return df
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate if ticker exists"""
        endpoint = f"/v3/quote/{ticker.upper()}"
        data = self._make_request(endpoint)
        return bool(data and len(data) > 0 and data[0].get('symbol'))
    
    def get_combined_data(self, ticker: str, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Get all data types for a ticker in existing format"""
        prices = self.fetch_historical_prices(ticker, start_date, end_date)
        dividends = self.fetch_historical_dividends(ticker, start_date, end_date)
        fed_funds = self.fetch_fed_funds_rate(start_date, end_date)
        
        return prices, dividends, fed_funds

# Global instance with API key
FMP_API_KEY = "f2IedVpstXz7qOfWiHl86s8BzVdQBMSC"
fmp_provider = FMPDataProvider(FMP_API_KEY)