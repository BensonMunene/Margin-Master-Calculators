from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import numpy as np
import os
import json
import datetime
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import base64
from io import BytesIO

from calculator.models import StockData, DividendData

# Load data function that uses database models instead of CSV files
def load_data():
    try:
        # Load SPY price data from database
        spy_data = StockData.objects.filter(symbol='SPY').order_by('date')
        if not spy_data.exists():
            print("SPY price data not found in database")
            spy_df = None
        else:
            # Convert queryset to dataframe
            spy_df = pd.DataFrame(list(spy_data.values('date', 'open_price', 'high', 'low', 'close', 'volume')))
            spy_df.rename(columns={'open_price': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            spy_df.set_index('date', inplace=True)
        
        # Load VTI price data from database
        vti_data = StockData.objects.filter(symbol='VTI').order_by('date')
        if not vti_data.exists():
            print("VTI price data not found in database")
            vti_df = None
        else:
            # Convert queryset to dataframe
            vti_df = pd.DataFrame(list(vti_data.values('date', 'open_price', 'high', 'low', 'close', 'volume')))
            vti_df.rename(columns={'open_price': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
            vti_df.set_index('date', inplace=True)
        
        # Load SPY dividend data from database
        spy_dividends_data = DividendData.objects.filter(symbol='SPY').order_by('date')
        if not spy_dividends_data.exists():
            print("SPY dividend data not found in database")
            spy_dividends_df = None
        else:
            # Convert queryset to dataframe
            spy_dividends_df = pd.DataFrame(list(spy_dividends_data.values('date', 'amount')))
            spy_dividends_df.rename(columns={'amount': 'Dividends'}, inplace=True)
            spy_dividends_df.set_index('date', inplace=True)
        
        # Load VTI dividend data from database
        vti_dividends_data = DividendData.objects.filter(symbol='VTI').order_by('date')
        if not vti_dividends_data.exists():
            print("VTI dividend data not found in database")
            vti_dividends_df = None
        else:
            # Convert queryset to dataframe
            vti_dividends_df = pd.DataFrame(list(vti_dividends_data.values('date', 'amount')))
            vti_dividends_df.rename(columns={'amount': 'Dividends'}, inplace=True)
            vti_dividends_df.set_index('date', inplace=True)
        
        return spy_df, spy_dividends_df, vti_df, vti_dividends_df
    except Exception as e:
        print(f"Error loading data from database: {e}")
        return None, None, None, None

# Function to calculate margin metrics
def calculate_margin_metrics(investment_amount, leverage, current_price, account_type, position_type):
    # Initial calculations
    margin_loan = investment_amount * (leverage - 1)
    cash_investment = investment_amount - margin_loan if margin_loan < 0 else investment_amount
    total_investment = cash_investment + margin_loan if margin_loan > 0 else cash_investment
    shares_purchased = total_investment / current_price if current_price > 0 else 0
    
    # Determine initial and maintenance margin requirements based on account type
    if account_type == "reg_t":
        initial_margin_req = 0.50  # 50% for Reg T
        maintenance_margin_req = 0.25  # 25% for Reg T
    else:  # Portfolio margin
        initial_margin_req = 0.15  # 15% for Portfolio Margin (simplified)
        maintenance_margin_req = 0.10  # 10% for Portfolio Margin (simplified)
    
    # Calculate margin call price
    if leverage > 1:
        # For long positions
        if position_type == "long":
            margin_call_price = (total_investment - cash_investment / (maintenance_margin_req)) / shares_purchased if shares_purchased > 0 else 0
            margin_call_drop = ((current_price - margin_call_price) / current_price) * 100 if current_price > 0 else 0
        # For short positions (simplified)
        else:
            margin_call_price = current_price * (1 + (leverage - 1) / maintenance_margin_req) if current_price > 0 else 0
            margin_call_drop = ((margin_call_price - current_price) / current_price) * 100 if current_price > 0 else 0
    else:
        margin_call_price = 0
        margin_call_drop = 0
    
    return {
        'margin_loan': margin_loan,
        'cash_investment': cash_investment,
        'total_investment': total_investment,
        'shares_purchased': shares_purchased,
        'initial_margin_req': initial_margin_req * 100,  # Convert to percentage
        'maintenance_margin_req': maintenance_margin_req * 100,  # Convert to percentage
        'margin_call_price': margin_call_price,
        'margin_call_drop': margin_call_drop,
    }

# Function to calculate scenarios
def compute_margin_scenarios(investment_amount, margin_loan, cash_investment, interest_rate, holding_period, bull_gain, bear_loss):
    # Bull scenario calculations
    bull_investment_return = investment_amount * (bull_gain / 100)
    bull_interest_cost = (margin_loan * interest_rate / 100) * (holding_period / 12)
    bull_net_return = bull_investment_return - bull_interest_cost
    bull_roi = (bull_net_return / cash_investment) * 100 if cash_investment > 0 else 0
    bull_annualized_roi = bull_roi * (12 / holding_period) if holding_period > 0 else 0
    
    # Bear scenario calculations
    bear_investment_return = -investment_amount * (bear_loss / 100)
    bear_interest_cost = (margin_loan * interest_rate / 100) * (holding_period / 12)
    bear_net_return = bear_investment_return - bear_interest_cost
    bear_roi = (bear_net_return / cash_investment) * 100 if cash_investment > 0 else 0
    bear_annualized_roi = bear_roi * (12 / holding_period) if holding_period > 0 else 0
    
    return {
        'bull_investment_return': bull_investment_return,
        'bull_interest_cost': bull_interest_cost,
        'bull_net_return': bull_net_return,
        'bull_roi': bull_roi,
        'bull_annualized_roi': bull_annualized_roi,
        'bear_investment_return': bear_investment_return,
        'bear_interest_cost': bear_interest_cost,
        'bear_net_return': bear_net_return,
        'bear_roi': bear_roi,
        'bear_annualized_roi': bear_annualized_roi,
    }

# Create Plotly candlestick chart
def plot_candlestick(df, title, symbol='Stock'):
    # Resample data to monthly for better visualization
    df_resampled = df.resample('M').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    })
    
    # Define colors for a premium look
    up_color = '#2ecc71'  # Vibrant green
    down_color = '#e74c3c'  # Rich red
    
    # Create figure with candlestick
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df_resampled.index,
        open=df_resampled['Open'],
        high=df_resampled['High'],
        low=df_resampled['Low'],
        close=df_resampled['Close'],
        increasing_line=dict(color=up_color, width=1),
        decreasing_line=dict(color=down_color, width=1),
        whiskerwidth=0.5,
        line=dict(width=1),
        name='Price'
    ))
    
    # Configure layout for a premium look
    fig.update_layout(
        title=f'{title} ({symbol})',
        xaxis={
            'title': 'Date',
            'rangeslider': {'visible': False},
            'type': 'date'
        },
        yaxis={
            'title': 'Price (USD)',
            'tickformat': '$,.2f',
        },
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#ffffff',
    )
    
    return pio.to_html(fig, full_html=False)

# Function to plot dividend bars
def plot_dividend_bars(df, title, symbol='Stock'):
    if 'Dividends' not in df.columns:
        return "<p>No dividend data available</p>"
    
    # Data preparation
    df_plot = df.copy()
    df_plot['Year'] = df_plot.index.year
    df_plot['Quarter'] = (df_plot.index.month - 1) // 3 + 1
    df_plot['YearQuarter'] = df_plot['Year'].astype(str) + '-Q' + df_plot['Quarter'].astype(str)
    
    # Group by year and quarter
    quarterly_dividends = df_plot.groupby(['Year', 'Quarter'])['Dividends'].sum().reset_index()
    quarterly_dividends['YearQuarter'] = quarterly_dividends['Year'].astype(str) + '-Q' + quarterly_dividends['Quarter'].astype(str)
    
    # Create bar chart
    fig = px.bar(
        quarterly_dividends,
        x='YearQuarter',
        y='Dividends',
        title=f'{title} Quarterly Dividends ({symbol})',
        labels={'Dividends': 'Dividend Amount ($)', 'YearQuarter': 'Year-Quarter'},
        color='Dividends',
        color_continuous_scale='Viridis',
    )
    
    fig.update_layout(
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#ffffff',
    )
    
    return pio.to_html(fig, full_html=False)

# Views
def index(request):
    """Main page view with the margin calculator"""
    # Load ETF data
    spy_df, spy_dividends_df, vti_df, vti_dividends_df = load_data()
    
    # Set default values for the calculator
    context = {
        'current_price': spy_df['Close'].iloc[-1] if spy_df is not None else 450.0,
        'investment_amount': 10000,
        'account_types': [('reg_t', 'Reg T Margin'), ('portfolio', 'Portfolio Margin')],
        'position_types': [('long', 'Long Position'), ('short', 'Short Position')],
        'leverage_options': [
            {'value': 1.0, 'label': '1.0x (0% margin, 100% cash)'},
            {'value': 1.5, 'label': '1.5x (33% margin, 67% cash)'},
            {'value': 2.0, 'label': '2.0x (50% margin, 50% cash)'},
            {'value': 3.0, 'label': '3.0x (67% margin, 33% cash)'},
            {'value': 4.0, 'label': '4.0x (75% margin, 25% cash)'},
        ],
        'interest_rate': 5.5,
        'holding_period': 12,
        'bull_gain': 20,
        'bear_loss': 20,
        'tab': 'calculator',  # Default active tab
    }
    
    return render(request, 'calculator/index.html', context)

def calculate_margin(request):
    """API endpoint for margin calculations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            investment_amount = float(data.get('investment_amount', 10000))
            leverage = float(data.get('leverage', 1.0))
            current_price = float(data.get('current_price', 450.0))
            account_type = data.get('account_type', 'reg_t')
            position_type = data.get('position_type', 'long')
            interest_rate = float(data.get('interest_rate', 5.5))
            holding_period = float(data.get('holding_period', 12))
            bull_gain = float(data.get('bull_gain', 20))
            bear_loss = float(data.get('bear_loss', 20))
            
            # Calculate margin metrics
            metrics = calculate_margin_metrics(
                investment_amount, leverage, current_price, account_type, position_type
            )
            
            # Calculate scenarios
            scenarios = compute_margin_scenarios(
                investment_amount, metrics['margin_loan'], metrics['cash_investment'],
                interest_rate, holding_period, bull_gain, bear_loss
            )
            
            # Additional calculations
            daily_interest_cost = (metrics['margin_loan'] * interest_rate / 100) / 365
            annual_interest_cost = metrics['margin_loan'] * interest_rate / 100
            breakeven_price = current_price + (annual_interest_cost / metrics['shares_purchased'] / (holding_period / 12)) if metrics['shares_purchased'] > 0 else 0
            
            # Combine results
            result = {
                **metrics,
                **scenarios,
                'daily_interest_cost': daily_interest_cost,
                'annual_interest_cost': annual_interest_cost,
                'breakeven_price': breakeven_price,
            }
            
            return JsonResponse({'success': True, 'data': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def calculate_scenarios(request):
    """API endpoint for scenario calculations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            investment_amount = float(data.get('investment_amount', 10000))
            margin_loan = float(data.get('margin_loan', 0))
            cash_investment = float(data.get('cash_investment', 10000))
            interest_rate = float(data.get('interest_rate', 5.5))
            holding_period = float(data.get('holding_period', 12))
            bull_gain = float(data.get('bull_gain', 20))
            bear_loss = float(data.get('bear_loss', 20))
            
            scenarios = compute_margin_scenarios(
                investment_amount, margin_loan, cash_investment,
                interest_rate, holding_period, bull_gain, bear_loss
            )
            
            return JsonResponse({'success': True, 'data': scenarios})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def market_overview(request):
    """Market overview page"""
    spy_df, spy_dividends_df, vti_df, vti_dividends_df = load_data()
    
    context = {
        'tab': 'market_overview',
        'spy_chart': plot_candlestick(spy_df, 'S&P 500 ETF', 'SPY') if spy_df is not None else None,
        'vti_chart': plot_candlestick(vti_df, 'Total Stock Market ETF', 'VTI') if vti_df is not None else None,
    }
    
    return render(request, 'calculator/market_overview.html', context)

def price_analysis(request):
    """Price analysis page"""
    spy_df, spy_dividends_df, vti_df, vti_dividends_df = load_data()
    
    # Get the earliest date from the data
    earliest_spy_date = None
    earliest_vti_date = None
    earliest_date = None
    
    if spy_df is not None:
        earliest_spy_date = spy_df.index.min()
    
    if vti_df is not None:
        earliest_vti_date = vti_df.index.min()
    
    # Use the later of the two earliest dates (to ensure both datasets have data)
    if earliest_spy_date is not None and earliest_vti_date is not None:
        earliest_date = max(earliest_spy_date, earliest_vti_date)
    elif earliest_spy_date is not None:
        earliest_date = earliest_spy_date
    elif earliest_vti_date is not None:
        earliest_date = earliest_vti_date
    else:
        # Fallback to a reasonable default if no data is available
        earliest_date = pd.Timestamp('2000-01-01')
    
    # Get start and end dates from request parameters or use defaults
    end_date = pd.Timestamp(datetime.datetime.now().date())
    
    # Check if user provided dates in the request
    if request.GET.get('start_date') and request.GET.get('end_date'):
        try:
            user_start = pd.Timestamp(request.GET.get('start_date'))
            user_end = pd.Timestamp(request.GET.get('end_date'))
            
            # Ensure start date isn't earlier than data
            start_date = max(user_start, earliest_date)
            end_date = user_end
        except:
            # Default to last 5 years if parse error
            start_date = pd.Timestamp(end_date - datetime.timedelta(days=5*365))
            start_date = max(start_date, earliest_date)  # Ensure not earlier than data
    else:
        # Default to last 5 years
        start_date = pd.Timestamp(end_date - datetime.timedelta(days=5*365))
        start_date = max(start_date, earliest_date)  # Ensure not earlier than data
    
    # Filter data by date range if dataframes exist
    spy_filtered = None
    vti_filtered = None
    
    if spy_df is not None:
        try:
            spy_filtered = spy_df[(spy_df.index >= start_date) & (spy_df.index <= end_date)]
        except Exception as e:
            print(f"Error filtering SPY data: {e}")
    
    if vti_df is not None:
        try:
            vti_filtered = vti_df[(vti_df.index >= start_date) & (vti_df.index <= end_date)]
        except Exception as e:
            print(f"Error filtering VTI data: {e}")
    
    context = {
        'tab': 'price_analysis',
        'spy_chart': plot_candlestick(spy_filtered, 'S&P 500 ETF', 'SPY') if spy_filtered is not None else None,
        'vti_chart': plot_candlestick(vti_filtered, 'Total Stock Market ETF', 'VTI') if vti_filtered is not None else None,
        'start_date': start_date,
        'end_date': end_date,
        'earliest_date': earliest_date,  # Pass earliest date to template
    }
    
    return render(request, 'calculator/price_analysis.html', context)

def dividend_analysis(request):
    """Dividend analysis page"""
    spy_df, spy_dividends_df, vti_df, vti_dividends_df = load_data()
    
    context = {
        'tab': 'dividend_analysis',
        'spy_dividend_chart': plot_dividend_bars(spy_dividends_df, 'S&P 500 ETF', 'SPY') if spy_dividends_df is not None else None,
        'vti_dividend_chart': plot_dividend_bars(vti_dividends_df, 'Total Stock Market ETF', 'VTI') if vti_dividends_df is not None else None,
    }
    
    return render(request, 'calculator/dividend_analysis.html', context)

def kelly_criterion(request):
    """Kelly Criterion calculator page"""
    context = {
        'tab': 'kelly_criterion',
    }
    
    return render(request, 'calculator/kelly_criterion.html', context)
