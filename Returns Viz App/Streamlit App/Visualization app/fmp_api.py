import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import Optional, Dict, Tuple


class FMPDataProvider:
    """Financial Modeling Prep API data provider for fetching historical stock/ETF data"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or st.secrets.get("FMP_API_KEY", None)
        if not self.api_key:
            raise ValueError("FMP API key not configured. Please add FMP_API_KEY to .streamlit/secrets.toml")
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def validate_ticker(_self, ticker):
        """Validate if a ticker exists and is available"""
        ticker = ticker.upper().strip()
        
        try:
            # Use the search endpoint to validate ticker
            url = f"{_self.base_url}/search-ticker"
            params = {
                "query": ticker,
                "limit": 10,
                "apikey": _self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if exact ticker match exists
            is_valid = any(item.get('symbol', '').upper() == ticker for item in data)
            
            return is_valid
            
        except Exception as e:
            st.error(f"Error validating ticker {ticker}: {e}")
            return False
    
    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def get_ticker_info(_self, ticker):
        """Get basic information about a ticker"""
        ticker = ticker.upper().strip()
        
        try:
            # Get company profile
            url = f"{_self.base_url}/profile/{ticker}"
            params = {"apikey": _self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                info = {
                    'symbol': data[0].get('symbol'),
                    'name': data[0].get('companyName'),
                    'exchange': data[0].get('exchangeShortName'),
                    'industry': data[0].get('industry'),
                    'sector': data[0].get('sector'),
                    'description': data[0].get('description', '')[:200] + '...' if data[0].get('description') else ''
                }
                
                return info
                
        except Exception as e:
            st.error(f"Error getting ticker info for {ticker}: {e}")
        
        return None
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_historical_data(_self, ticker, start_date=None, end_date=None):
        """Fetch historical daily price data for a ticker"""
        ticker = ticker.upper().strip()
        
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = pd.to_datetime(end_date)
            
        if not start_date:
            start_date = end_date - timedelta(days=365 * 25)  # 25 years of data
        else:
            start_date = pd.to_datetime(start_date)
        
        # Format dates for API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        try:
            # Fetch historical data
            url = f"{_self.base_url}/historical-price-full/{ticker}"
            params = {
                "from": start_str,
                "to": end_str,
                "apikey": _self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'historical' not in data or not data['historical']:
                raise ValueError(f"No historical data available for {ticker}")
            
            # Convert to DataFrame
            df = pd.DataFrame(data['historical'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df.set_index('date', inplace=True)
            
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Ticker '{ticker}' not found")
            else:
                raise ValueError(f"API error: {e}")
        except Exception as e:
            raise ValueError(f"Error fetching data for {ticker}: {str(e)}")
    
    def calculate_annual_returns(self, ticker, start_year=None, end_year=None):
        """Calculate annual returns for a ticker"""
        # Fetch historical data
        df = self.fetch_historical_data(ticker)
        
        if df.empty:
            raise ValueError(f"No data available for {ticker}")
        
        # Calculate daily returns using adjusted close
        df['daily_return'] = df['adjClose'].pct_change()
        
        # Remove any NaN values
        df = df.dropna(subset=['daily_return'])
        
        # Add year column
        df['year'] = df.index.year
        
        # Calculate annual returns by compounding daily returns
        annual_returns = df.groupby('year')['daily_return'].apply(
            lambda x: (1 + x).prod() - 1
        )
        
        # Convert to percentage
        annual_returns = annual_returns * 100
        
        # Filter years if specified
        if start_year:
            annual_returns = annual_returns[annual_returns.index >= start_year]
        if end_year:
            annual_returns = annual_returns[annual_returns.index <= end_year]
        
        return annual_returns.round(2)
    
    def get_daily_returns(self, ticker, start_year=None, end_year=None):
        """Get daily returns for performance metrics calculation"""
        # Fetch historical data
        df = self.fetch_historical_data(ticker)
        
        if df.empty:
            raise ValueError(f"No data available for {ticker}")
        
        # Calculate daily returns using adjusted close
        daily_returns = df['adjClose'].pct_change().dropna()
        
        # Filter by years if specified
        if start_year or end_year:
            if start_year:
                daily_returns = daily_returns[daily_returns.index.year >= start_year]
            if end_year:
                daily_returns = daily_returns[daily_returns.index.year <= end_year]
        
        return daily_returns
    
    def get_multiple_tickers_returns(self, tickers, start_year=None, end_year=None):
        """Get annual returns for multiple tickers"""
        results = {}
        errors = {}
        
        # Add progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers):
            try:
                ticker = ticker.upper().strip()
                status_text.text(f"Fetching data for {ticker}...")
                returns = self.calculate_annual_returns(ticker, start_year, end_year)
                results[ticker] = returns
            except Exception as e:
                errors[ticker] = str(e)
            
            # Update progress
            progress_bar.progress((i + 1) / len(tickers))
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Convert to DataFrame
        if results:
            df = pd.DataFrame(results)
            return df, errors
        else:
            return pd.DataFrame(), errors