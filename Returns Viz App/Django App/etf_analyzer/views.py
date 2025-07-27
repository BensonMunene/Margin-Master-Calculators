from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
import numpy as np
from .utils import create_cagr_matrix, create_cagr_heatmap
from .fmp_api import FMPDataProvider
from .performance_metrics import calculate_performance_metrics
import plotly.io as pio
import io
from django.conf import settings


def index(request):
    """Main view for the ETF CAGR Analysis dashboard"""
    context = {
        'time_periods': {
            "Recent Decade (2014-2025)": {"start": 2014, "end": 2025},
            "Post-Crisis (2010-2025)": {"start": 2010, "end": 2025},
            "Modern Era (2000-2025)": {"start": 2000, "end": 2025},
            "Full Period": {"start": "min", "end": "max"},
            "Custom": {"start": "custom", "end": "custom"}
        }
    }
    return render(request, 'etf_analyzer/index.html', context)


def validate_ticker(request):
    """API endpoint to validate a ticker symbol"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticker = data.get('ticker', '').strip()
            
            if not ticker:
                return JsonResponse({'valid': False, 'error': 'Please enter a ticker symbol'})
            
            # Initialize FMP provider
            fmp = FMPDataProvider()
            
            # Validate ticker
            is_valid = fmp.validate_ticker(ticker)
            
            if is_valid:
                # Get additional info about the ticker
                ticker_info = fmp.get_ticker_info(ticker)
                return JsonResponse({
                    'valid': True,
                    'ticker': ticker.upper(),
                    'info': ticker_info
                })
            else:
                return JsonResponse({
                    'valid': False,
                    'error': f'Ticker "{ticker}" not found. Please enter a valid stock or ETF symbol.'
                })
                
        except Exception as e:
            return JsonResponse({'valid': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def get_data(request):
    """API endpoint to get ticker data and generate heatmap"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticker = data.get('ticker', '').strip().upper()
            start_year = int(data.get('start_year'))
            end_year = int(data.get('end_year'))
            
            if not ticker:
                return JsonResponse({'error': 'Please enter a ticker symbol'}, status=400)
            
            # Initialize FMP provider
            fmp = FMPDataProvider()
            
            # Validate ticker first
            if not fmp.validate_ticker(ticker):
                return JsonResponse({
                    'error': f'Invalid ticker: "{ticker}". Please enter a valid stock or ETF symbol.'
                }, status=400)
            
            # Get ticker info
            ticker_info = fmp.get_ticker_info(ticker)
            
            # Calculate annual returns
            try:
                annual_returns = fmp.calculate_annual_returns(ticker)
                
                # Debug: Check the type and structure
                if not isinstance(annual_returns.index, pd.Index):
                    return JsonResponse({'error': 'Invalid data structure returned from API'}, status=500)
                
                    
            except ValueError as e:
                return JsonResponse({'error': str(e)}, status=400)
            except Exception as e:
                import traceback
                print(f"Error calculating returns: {traceback.format_exc()}")
                return JsonResponse({'error': f'Error calculating returns: {str(e)}'}, status=500)
            
            # Get available years
            available_years = annual_returns.index.tolist()
            if not available_years:
                return JsonResponse({
                    'error': f'No historical data available for {ticker}'
                }, status=400)
            
            min_year = min(available_years)
            max_year = max(available_years)
            
            # Adjust years if "Full Period" was selected
            if data.get('period') == 'Full Period':
                start_year = min_year
                end_year = max_year
            
            # Validate year range
            if start_year >= end_year:
                return JsonResponse({'error': 'Start year must be less than end year!'}, status=400)
            
            # Auto-adjust to available data range instead of rejecting
            actual_start_year = max(start_year, min_year)
            actual_end_year = min(end_year, max_year)
            
            # Filter available data using actual range
            available_data = annual_returns.loc[actual_start_year:actual_end_year]
            if available_data.empty:
                return JsonResponse({
                    'error': f'No data available for {ticker}'
                }, status=400)
            
            # Generate CAGR matrix
            # Ensure annual_returns is a Series with integer year index
            if isinstance(annual_returns, pd.Series):
                # Make sure index is integer type
                if not pd.api.types.is_integer_dtype(annual_returns.index):
                    try:
                        annual_returns.index = annual_returns.index.astype(int)
                    except:
                        return JsonResponse({'error': 'Invalid year data in returns'}, status=500)
            else:
                return JsonResponse({'error': 'Invalid returns data structure'}, status=500)
                
            cagr_matrix = create_cagr_matrix(annual_returns, actual_start_year, actual_end_year)
            
            # Create heatmap
            heatmap_fig = create_cagr_heatmap(cagr_matrix, ticker, actual_start_year, actual_end_year)
            heatmap_json = pio.to_json(heatmap_fig)
            
            # Calculate statistics
            single_year_data = {year: cagr_matrix.loc[year, year] for year in cagr_matrix.index 
                               if not pd.isna(cagr_matrix.loc[year, year])}
            
            stats = {}
            if single_year_data:
                best_year_value = max(single_year_data.values())
                best_year = [year for year, value in single_year_data.items() if value == best_year_value][0]
                worst_year_value = min(single_year_data.values())
                worst_year = [year for year, value in single_year_data.items() if value == worst_year_value][0]
                
                stats['best_single_year'] = {'value': best_year_value, 'year': best_year}
                stats['worst_single_year'] = {'value': worst_year_value, 'year': worst_year}
            
            # 10-year CAGR if available
            if end_year - 9 >= start_year:
                ten_year_start = end_year - 9
                if ten_year_start in cagr_matrix.index:
                    ten_year_cagr = cagr_matrix.loc[end_year, ten_year_start]
                    stats['ten_year_cagr'] = {
                        'value': ten_year_cagr,
                        'start': ten_year_start,
                        'end': end_year
                    }
            
            # Full period CAGR
            if start_year in cagr_matrix.index and end_year in cagr_matrix.index:
                full_period_cagr = cagr_matrix.loc[end_year, start_year]
                period_years = end_year - start_year + 1
                stats['full_period_cagr'] = {
                    'value': full_period_cagr,
                    'years': period_years,
                    'start': start_year,
                    'end': end_year
                }
            
            # Calculate comprehensive performance metrics
            try:
                # Get daily returns for the actual available period
                daily_returns = fmp.get_daily_returns(ticker, actual_start_year, actual_end_year)
                
                # Get S&P 500 benchmark data for relative metrics
                benchmark_returns = None
                try:
                    if ticker.upper() != 'SPY':  # Don't benchmark SPY against itself
                        benchmark_returns = fmp.get_daily_returns('SPY', actual_start_year, actual_end_year)
                        # Align the dates
                        aligned_data = pd.DataFrame({
                            'asset': daily_returns,
                            'benchmark': benchmark_returns
                        }).dropna()
                        daily_returns = aligned_data['asset']
                        benchmark_returns = aligned_data['benchmark']
                except Exception as e:
                    print(f"Could not get benchmark data: {e}")
                    benchmark_returns = None
                
                # Calculate performance metrics
                performance_metrics = calculate_performance_metrics(daily_returns, benchmark_returns)
                
                # Convert numpy types to native Python types for JSON serialization
                def convert_numpy_types(obj):
                    if isinstance(obj, (np.integer, np.int32, np.int64)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float32, np.float64)):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif pd.isna(obj) or obj is None:
                        return None
                    return obj
                
                # Apply conversion to all metrics
                for key, value in performance_metrics.items():
                    performance_metrics[key] = convert_numpy_types(value)
                
                # Format the metrics for display
                performance_overview = {
                    'return_metrics': {
                        'cagr': performance_metrics['cagr'],
                        'total_return': performance_metrics['total_return'],
                        'best_year': performance_metrics['best_year'],
                        'best_year_date': performance_metrics['best_year_date'],
                        'worst_year': performance_metrics['worst_year'],
                        'worst_year_date': performance_metrics['worst_year_date'],
                        'win_rate': performance_metrics['win_rate'],
                        'average_up_year': performance_metrics['average_up_year'],
                        'average_down_year': performance_metrics['average_down_year']
                    },
                    'risk_metrics': {
                        'volatility': performance_metrics['volatility'],
                        'maximum_drawdown': performance_metrics['maximum_drawdown'],
                        'recovery_days': performance_metrics['recovery_days'],
                        'var_5': performance_metrics['var_5'],
                        'cvar_5': performance_metrics['cvar_5'],
                        'pain_index': performance_metrics['pain_index'],
                        'ulcer_index': performance_metrics['ulcer_index']
                    },
                    'risk_adjusted_metrics': {
                        'sharpe_ratio': performance_metrics['sharpe_ratio'],
                        'sortino_ratio': performance_metrics['sortino_ratio'],
                        'calmar_ratio': performance_metrics['calmar_ratio']
                    },
                    'distribution_metrics': {
                        'skewness': performance_metrics['skewness'],
                        'kurtosis': performance_metrics['kurtosis']
                    },
                    'relative_metrics': {
                        'beta': performance_metrics['beta'],
                        'alpha': performance_metrics['alpha'],
                        'r_squared': performance_metrics['r_squared'],
                        'treynor_ratio': performance_metrics['treynor_ratio'],
                        'information_ratio': performance_metrics['information_ratio']
                    },
                    'period_info': {
                        'num_years': performance_metrics['num_years'],
                        'num_observations': performance_metrics['num_observations'],
                        'start_year': actual_start_year,
                        'end_year': actual_end_year
                    }
                }
                
            except Exception as e:
                print(f"Error calculating performance metrics: {e}")
                performance_overview = None
            
            # Check if date range was adjusted
            date_adjusted = (actual_start_year != start_year) or (actual_end_year != end_year)
            adjustment_message = None
            if date_adjusted:
                adjustment_message = f"Analysis adjusted to available data range: {actual_start_year}-{actual_end_year}"
            
            return JsonResponse({
                'heatmap': json.loads(heatmap_json),
                'stats': stats,
                'performance_overview': performance_overview,
                'available_years': {'min': min_year, 'max': max_year},
                'ticker_info': ticker_info,
                'date_adjusted': date_adjusted,
                'adjustment_message': adjustment_message,
                'actual_start_year': actual_start_year,
                'actual_end_year': actual_end_year
            })
            
        except Exception as e:
            import traceback
            error_details = {
                'error': f'An error occurred: {str(e)}',
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            print(f"Error in get_data: {error_details}")
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def download_matrix(request):
    """Download CAGR matrix as CSV"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ticker = data.get('ticker', '').strip().upper()
            start_year = int(data.get('start_year'))
            end_year = int(data.get('end_year'))
            
            if not ticker:
                return JsonResponse({'error': 'Please provide a ticker symbol'}, status=400)
            
            # Initialize FMP provider
            fmp = FMPDataProvider()
            
            # Get annual returns and generate matrix
            annual_returns = fmp.calculate_annual_returns(ticker)
            
            # Ensure proper index type
            if not pd.api.types.is_integer_dtype(annual_returns.index):
                annual_returns.index = annual_returns.index.astype(int)
                
            cagr_matrix = create_cagr_matrix(annual_returns, start_year, end_year)
            
            # Convert to CSV
            display_matrix = cagr_matrix.round(2).fillna('')
            display_matrix_reversed = display_matrix.iloc[::-1]
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="PearsonCreek_{ticker}_CAGR_Matrix_{start_year}_{end_year}.csv"'
            
            display_matrix_reversed.to_csv(response)
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def download_annual_returns(request):
    """Download annual returns data as CSV"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_year = int(data.get('start_year'))
            end_year = int(data.get('end_year'))
            tickers = data.get('tickers', [])
            
            if not tickers:
                return JsonResponse({'error': 'Please provide at least one ticker'}, status=400)
            
            # Initialize FMP provider
            fmp = FMPDataProvider()
            
            # Get returns for all requested tickers
            all_returns = {}
            for ticker in tickers:
                try:
                    ticker = ticker.strip().upper()
                    returns = fmp.calculate_annual_returns(ticker)
                    # Ensure proper index type
                    if not pd.api.types.is_integer_dtype(returns.index):
                        returns.index = returns.index.astype(int)
                    all_returns[ticker] = returns
                except Exception as e:
                    print(f"Error getting returns for {ticker}: {e}")
                    pass
            
            if not all_returns:
                return JsonResponse({'error': 'No data available for the requested tickers'}, status=400)
            
            # Create DataFrame
            df = pd.DataFrame(all_returns)
            annual_display = df.loc[start_year:end_year]
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="PearsonCreek_Annual_Returns_{start_year}_{end_year}.csv"'
            
            annual_display.to_csv(response)
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def search_tickers(request):
    """Search for tickers by query"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 1:
            return JsonResponse({'results': []})
        
        try:
            # Initialize FMP provider
            fmp = FMPDataProvider()
            
            # Search for tickers
            url = f"{fmp.base_url}/search-ticker"
            params = {
                "query": query,
                "limit": 10,
                "apikey": fmp.api_key
            }
            
            import requests
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Format results
            results = []
            for item in data:
                results.append({
                    'symbol': item.get('symbol'),
                    'name': item.get('name'),
                    'exchange': item.get('stockExchange', '')
                })
            
            return JsonResponse({'results': results})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)