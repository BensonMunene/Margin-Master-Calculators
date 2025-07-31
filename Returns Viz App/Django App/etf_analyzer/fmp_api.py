import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache


class FMPDataProvider:
    """Financial Modeling Prep API data provider for fetching historical stock/ETF data"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'FMP_API_KEY', None)
        if not self.api_key:
            raise ValueError("FMP API key not configured")
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def validate_ticker(self, ticker):
        """Validate if a ticker exists and is available"""
        ticker = ticker.upper().strip()
        
        # Check cache first
        cache_key = f"ticker_valid_{ticker}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            # Use the search endpoint to validate ticker
            url = f"{self.base_url}/search-ticker"
            params = {
                "query": ticker,
                "limit": 10,
                "apikey": self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if exact ticker match exists
            is_valid = any(item.get('symbol', '').upper() == ticker for item in data)
            
            # Cache the result for 1 hour
            cache.set(cache_key, is_valid, 3600)
            
            return is_valid
            
        except Exception as e:
            print(f"Error validating ticker {ticker}: {e}")
            return False
    
    def get_available_date_range(self, ticker):
        """Get the available date range for a ticker (first and last available dates)"""
        ticker = ticker.upper().strip()
        
        # Check cache first
        cache_key = f"ticker_date_range_{ticker}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            # Get a small sample of historical data to determine date range
            url = f"{self.base_url}/historical-price-full/{ticker}"
            params = {
                "apikey": self.api_key,
                "serietype": "line"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'historical' not in data or not data['historical']:
                return None
            
            # Get the date range
            historical = data['historical']
            dates = [entry['date'] for entry in historical]
            
            if not dates:
                return None
            
            # Convert to datetime and get min/max years
            date_objects = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
            min_date = min(date_objects)
            max_date = max(date_objects)
            
            result = {
                'start_year': min_date.year,
                'end_year': max_date.year,
                'start_date': min_date.strftime('%Y-%m-%d'),
                'end_date': max_date.strftime('%Y-%m-%d'),
                'total_years': max_date.year - min_date.year + 1
            }
            
            # Cache for 24 hours (date ranges don't change often)
            cache.set(cache_key, result, 86400)
            
            return result
            
        except Exception as e:
            print(f"Error getting date range for {ticker}: {e}")
            return None

    def get_ticker_info(self, ticker):
        """Get basic information about a ticker"""
        ticker = ticker.upper().strip()
        
        cache_key = f"ticker_info_{ticker}"
        cached_info = cache.get(cache_key)
        if cached_info:
            return cached_info
        
        try:
            # Get company profile
            url = f"{self.base_url}/profile/{ticker}"
            params = {"apikey": self.api_key}
            
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
                
                # Cache for 24 hours
                cache.set(cache_key, info, 86400)
                return info
                
        except Exception as e:
            print(f"Error getting ticker info for {ticker}: {e}")
        
        return None
    
    def fetch_historical_data(self, ticker, start_date=None, end_date=None):
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
        
        # Check cache
        cache_key = f"historical_{ticker}_{start_str}_{end_str}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            df = pd.DataFrame(cached_data)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            return df
        
        try:
            # Fetch historical data
            url = f"{self.base_url}/historical-price-full/{ticker}"
            params = {
                "from": start_str,
                "to": end_str,
                "apikey": self.api_key
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
            
            # Cache for 1 hour - reset index to preserve date column
            df_cache = df.reset_index()
            cache.set(cache_key, df_cache.to_dict('records'), 3600)
            
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
        
        # Add year column - ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df['year'] = df.index.year
        
        # Calculate annual returns by compounding daily returns
        annual_returns = df.groupby('year')['daily_return'].apply(
            lambda x: (1 + x).prod() - 1
        )
        
        # Convert to percentage
        annual_returns = annual_returns * 100
        
        # Ensure the index is named 'year' and is integer type
        annual_returns.index.name = 'year'
        annual_returns.index = annual_returns.index.astype(int)
        
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
        
        for ticker in tickers:
            try:
                ticker = ticker.upper().strip()
                returns = self.calculate_annual_returns(ticker, start_year, end_year)
                results[ticker] = returns
            except Exception as e:
                errors[ticker] = str(e)
        
        # Convert to DataFrame
        if results:
            df = pd.DataFrame(results)
            return df, errors
        else:
            return pd.DataFrame(), errors