import streamlit as st

# Custom CSS for the entire application
def load_css():
    return """
    <style>
        /* Main container styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Header styling */
        h1, h2, h3 {
            font-family: 'Arial', sans-serif;
            font-weight: 600;
            color: #2c3e50;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
        }
        h2 {
            font-size: 1.8rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            color: #34495e;
        }
        h3 {
            font-size: 1.3rem;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            color: #34495e;
        }
        
        
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;  /* Increased spacing between tabs */
        }
        .stTabs [data-baseweb="tab"] {
            height: 3.5rem;  /* Taller tabs */
            white-space: pre-wrap;
            border-radius: 6px 6px 0 0;  /* Slightly more rounded corners */
            padding: 0.7rem 1.5rem;  /* More padding */
            font-weight: 700;  /* Bolder text */
            font-size: 1.99rem;  /* Larger text */
            letter-spacing: 0.5px;  /* Better letter spacing */
            transition: all 0.2s ease;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
            color: #34495e;  /* Default tab color */
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #f8f9fa;
            transform: translateY(-2px);
        }
        .stTabs [aria-selected="true"] {
            background-color: #3498db !important;
            color: white !important;
            transform: translateY(-3px);
            font-weight: 800;  /* Extra bold when selected */
            box-shadow: 0 -3px 7px rgba(0,0,0,0.1);
        }
        /* Custom tab colors */
        .stTabs [data-baseweb="tab"]:nth-child(1) {
            border-top: 3px solid #27ae60;  /* Green for Market Overview */
        }
        .stTabs [data-baseweb="tab"]:nth-child(2) {
            border-top: 3px solid #2980b9;  /* Blue for Price Analysis */
        }
        .stTabs [data-baseweb="tab"]:nth-child(3) {
            border-top: 3px solid #e67e22;  /* Orange for Dividend Analysis */
        }
        .stTabs [data-baseweb="tab"]:nth-child(4) {
            border-top: 3px solid #8e44ad;  /* Purple for Margin Calculator */
        }
        .stTabs [data-baseweb="tab"]:nth-child(5) {
            border-top: 3px solid #e91e63;  /* Pink for Kelly Criterion */
        }
        .stTabs [data-baseweb="tab"]:nth-child(6) {
            border-top: 3px solid #009688;  /* Teal for Historical Backtest */
        }
        /* Selected tab colors */
        .stTabs [data-baseweb="tab"]:nth-child(1)[aria-selected="true"] {
            background-color: #27ae60 !important;
        }
        .stTabs [data-baseweb="tab"]:nth-child(2)[aria-selected="true"] {
            background-color: #2980b9 !important;
        }
        .stTabs [data-baseweb="tab"]:nth-child(3)[aria-selected="true"] {
            background-color: #e67e22 !important;
        }
        .stTabs [data-baseweb="tab"]:nth-child(4)[aria-selected="true"] {
            background-color: #8e44ad !important;
        }
        .stTabs [data-baseweb="tab"]:nth-child(5)[aria-selected="true"] {
            background-color: #e91e63 !important;
        }
        .stTabs [data-baseweb="tab"]:nth-child(6)[aria-selected="true"] {
            background-color: #009688 !important;
        }
        
        /* Table styling */
        .dataframe {
            border-collapse: collapse;
            width: 100%;
            font-family: 'Arial', sans-serif;
            font-size: 0.9rem;
        }
        .dataframe th {
            background-color: #f8f9fa;
            color: #2c3e50;
            font-weight: 600;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            padding: 0.75rem;
        }
        .dataframe td {
            border-bottom: 1px solid #e9ecef;
            padding: 0.75rem;
        }
        .dataframe tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .dataframe tr:hover {
            background-color: #e9ecef;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #3498db;
            color: white;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: none;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #2980b9;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        /* Loading animation */
        .stSpinner {
            text-align: center;
            max-width: 50%;
            margin: 0 auto;
        }
        
        /* Info/Alert boxes */
        .stAlert {
            border-radius: 4px;
        }
        
        /* Footer styling */
        footer {
            border-top: 1px solid #e9ecef;
            margin-top: 2rem;
            padding-top: 1rem;
            text-align: center;
            font-size: 0.8rem;
            color: #6c757d;
        }
        
        /* Pearson Creek header styling */
        .pearson-header {
            background-color: rgba(52, 73, 94, 0.9);
            color: white;
            text-align: center;
            padding: 15px 10px;
            border-radius: 8px;
            margin-right: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            width: 300px;
        }
        .pearson-title {
            font-family: 'Arial', sans-serif;
            font-weight: 700;
            font-size: 1.5rem;
            letter-spacing: 2px;
            margin: 0;
            line-height: 1.2;
            text-transform: uppercase;
        }
        .pearson-subtitle {
            font-family: 'Arial', sans-serif;
            font-weight: 400;
            font-size: 0.9rem;
            margin: 5px 0 0 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .pearson-border {
            height: 2px;
            background-color: white;
            margin: 8px 20px;
        }
    </style>
    """

# Pearson Creek Capital Management header
def pearson_creek_header():
    return """
    <div style="background: linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.75)), url('https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80'); 
        background-size: cover; background-position: center; width: 300px; color: white; 
        text-align: center; padding: 20px 15px; border-radius: 10px; 
        margin-right: 20px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
        
        <div style="height: 1px; background-color: white; width: 80%; margin: 0 auto 12px auto;"></div>
        
        <h1 style="font-family: 'Arial', sans-serif; font-weight: 700; font-size: 1.5rem; 
            letter-spacing: 3px; margin: 0; line-height: 1.2; text-transform: uppercase;">
            PEARSON<br>CREEK
        </h1>
        
        <p style="font-family: 'Arial', sans-serif; font-weight: 400; font-size: 0.8rem; 
            margin: 8px 0 0 0; letter-spacing: 1.5px; text-transform: uppercase;">
            CAPITAL MANAGEMENT LLC
        </p>
        
        <div style="height: 1px; background-color: white; width: 80%; margin: 12px auto 0 auto;"></div>
    </div>
    """

# Main app header with logo and title
def app_header():
    return """
    <div style="margin-bottom: 1rem; background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.7)), url('https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80'); background-size: cover; background-position: center; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); width: 100%; padding: 40px 20px; text-align: center;">
        <div style="height: 1px; background-color: white; width: 80%; margin: 0 auto 1.5rem auto;"></div>
        <h1 style="margin: 0; color: white; font-size: 3.4rem; letter-spacing: 6px; text-transform: uppercase; font-weight: 700;">PEARSON CREEK</h1>
        <p style="margin: 0.8rem 0 0 0; color: white; font-size: 1.7rem; letter-spacing: 3px; text-transform: uppercase;">CAPITAL MANAGEMENT LLC</p>
        <div style="height: 1px; background-color: white; width: 80%; margin: 1.5rem auto 0 auto;"></div>
    </div>
    <div style="text-align: center; margin: 1.5rem 0;">
        <h2 style="margin: 0; color: #2c3e50; font-size: 2rem;">ETF Analytics App & Margin Calculator</h2>
        <p style="margin: 0.5rem 0 0 0; color: #34495e; font-size: 1.1rem;">Analyze ETF performance trends and calculate optimal margin strategies</p>
    </div>
    """

# Explanation card for date range
def date_range_explanation():
    return """
    <p style="margin-bottom: 1rem; color: #5a6268; font-size: 0.95rem;">
      Select the time period for your ETF analysis. The data range affects all visualizations and calculations.
      Historical data is available from the early 2000s to present.
    </p>
    """

# Explanation for Market Overview tab
def market_overview_explanation():
    return """
    <p style="margin-bottom: 1.5rem; color: #34495e; font-size: 1rem; line-height: 1.5;">
      This dashboard provides a comprehensive overview of key ETF performance metrics. The data below compares 
      the <strong>S&P 500 ETF (SPY)</strong> and the <strong>Total Market ETF (VTI)</strong>, two of the most widely traded 
      ETFs that track broad market indices. These metrics help you understand recent performance trends and make informed 
      investment decisions.
    </p>
    """

# Explanation for Price Analysis tab
def price_analysis_explanation():
    return """
    <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 5px; margin-bottom: 1.5rem; border-left: 4px solid #3498db;">
      <h4 style="margin-top: 0; color: #2c3e50;">Understanding Candlestick Charts</h4>
      <p style="color: #34495e; font-size: 0.95rem; line-height: 1.5;">
        Candlestick charts display price movements over time, with each "candle" representing a time period (monthly in this view).
        <span style="color: #2ecc71;"><strong>Green candles</strong></span> indicate periods where the price closed higher than it opened (bullish), 
        while <span style="color: #e74c3c;"><strong>red candles</strong></span> show periods when the price closed lower (bearish).
        The "wicks" extending from each candle show the highest and lowest prices reached during that period.
      </p>
    </div>
    """

# Explanation for Dividend Analysis tab
def dividend_analysis_explanation():
    return """
    <div style="background: linear-gradient(to right, #f1f9ff, #e9f7fe); padding: 1rem; border-radius: 5px; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
      <h4 style="margin-top: 0; color: #2c3e50;">Dividend Distribution Patterns</h4>
      <p style="color: #34495e; font-size: 0.95rem; line-height: 1.5;">
        Dividends represent cash payments distributed to shareholders from a company's earnings.
        These visualizations show the quarterly dividend payments for each ETF over time.
        <ul style="margin-top: 0.5rem;">
          <li>The height of each bar represents the dividend amount per share</li>
          <li>Each color represents a different year for easy tracking of annual patterns</li>
          <li>Quarterly labels (Q1-Q4) indicate which quarter the dividend was paid</li>
        </ul>
        Analyzing dividend trends can help investors understand the income potential of these ETFs and identify seasonal patterns.
      </p>
    </div>
    """

# Explanation for Margin Calculator tab
def margin_calculator_explanation():
    return """
    <div style="background: linear-gradient(to right, #f8f9fa, #f1f3f5); padding: 1.2rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid #e9ecef;">
      <h4 style="margin-top: 0; color: #2c3e50; border-bottom: 1px solid #dee2e6; padding-bottom: 0.5rem;">Understanding Margin Trading</h4>
      <p style="color: #34495e; font-size: 0.95rem; line-height: 1.6;">
        Margin trading allows investors to borrow money from a broker to purchase securities. This calculator helps you understand:
        <ul style="margin: 0.5rem 0;">
          <li><strong>Buying Power:</strong> How much you can invest using both your cash and borrowed funds</li>
          <li><strong>Leverage Effect:</strong> How margin can amplify both gains and losses</li>
          <li><strong>Margin Requirements:</strong> The minimum amount of equity you need to maintain</li>
        </ul>
        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 0.5rem; margin-top: 0.5rem;">
          <strong>⚠️ Risk Warning:</strong> Margin trading involves higher risk than non-leveraged investing. Losses can exceed your initial investment.
        </div>
      </p>
    </div>
    """

# Footer with information
def app_footer():
    import datetime
    return f"""
    <footer>
        <p>ETF Data Analysis & Margin Calculator | Data sourced from Yahoo Finance</p>
        <p>Last updated: {datetime.datetime.now().strftime("%B %d, %Y")}</p>
    </footer>
    """ 