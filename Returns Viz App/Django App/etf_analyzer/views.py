from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
from .utils import load_etf_data, create_cagr_matrix, create_cagr_heatmap
import plotly.io as pio
import io


def index(request):
    """Main view for the ETF CAGR Analysis dashboard"""
    context = {
        'etf_options': ['SPY', 'QQQ', 'DIA', 'VTI'],
        'time_periods': {
            "Recent Decade (2013-2024)": {"start": 2013, "end": 2024},
            "Post-Crisis (2010-2025)": {"start": 2010, "end": 2025},
            "Modern Era (2000-2025)": {"start": 2000, "end": 2025},
            "Full Period": {"start": "min", "end": "max"},
            "Custom": {"start": "custom", "end": "custom"}
        }
    }
    return render(request, 'etf_analyzer/index.html', context)


def get_data(request):
    """API endpoint to get ETF data and generate heatmap"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_etf = data.get('etf', 'SPY')
            start_year = int(data.get('start_year'))
            end_year = int(data.get('end_year'))
            
            # Load data
            annual_returns, combined_data = load_etf_data()
            
            # Get available years
            available_years = annual_returns.index.tolist()
            min_year = min(available_years)
            max_year = max(available_years)
            
            # Adjust years if "Full Period" was selected
            if data.get('period') == 'Full Period':
                start_year = min_year
                end_year = max_year
            
            # Validate year range
            if start_year >= end_year:
                return JsonResponse({'error': 'Start year must be less than end year!'}, status=400)
            
            # Filter available data
            available_data = annual_returns[selected_etf].loc[start_year:end_year]
            if available_data.empty:
                return JsonResponse({'error': f'No data available for {selected_etf} in the period {start_year}-{end_year}'}, status=400)
            
            # Generate CAGR matrix
            cagr_matrix = create_cagr_matrix(annual_returns[selected_etf], start_year, end_year)
            
            # Create heatmap
            heatmap_fig = create_cagr_heatmap(cagr_matrix, selected_etf, start_year, end_year)
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
            
            # ETF comparison
            comparison_data = {}
            for etf in ['SPY', 'QQQ', 'DIA', 'VTI']:
                try:
                    etf_matrix = create_cagr_matrix(annual_returns[etf], start_year, end_year)
                    if start_year in etf_matrix.index and end_year in etf_matrix.index:
                        full_period_cagr = etf_matrix.loc[end_year, start_year]
                        comparison_data[etf] = full_period_cagr
                except:
                    pass
            
            return JsonResponse({
                'heatmap': json.loads(heatmap_json),
                'stats': stats,
                'comparison': comparison_data,
                'available_years': {'min': min_year, 'max': max_year}
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def download_matrix(request):
    """Download CAGR matrix as CSV"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_etf = data.get('etf', 'SPY')
            start_year = int(data.get('start_year'))
            end_year = int(data.get('end_year'))
            
            # Load data and generate matrix
            annual_returns, _ = load_etf_data()
            cagr_matrix = create_cagr_matrix(annual_returns[selected_etf], start_year, end_year)
            
            # Convert to CSV
            display_matrix = cagr_matrix.round(2).fillna('')
            display_matrix_reversed = display_matrix.iloc[::-1]
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="PearsonCreek_{selected_etf}_CAGR_Matrix_{start_year}_{end_year}.csv"'
            
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
            
            # Load data
            annual_returns, _ = load_etf_data()
            annual_display = annual_returns.loc[start_year:end_year]
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="PearsonCreek_Annual_Returns_{start_year}_{end_year}.csv"'
            
            annual_display.to_csv(response)
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
