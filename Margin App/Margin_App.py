import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
from visualizations import plot_candlestick, plot_dividend_bars, plot_dividend_bars_mpl
from UI_Components import (
    load_css, app_header, date_range_explanation, 
    market_overview_explanation, price_analysis_explanation,
    dividend_analysis_explanation, margin_calculator_explanation,
    app_footer
)

# Set page configuration
st.set_page_config(
    page_title="ETF Margin Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load custom CSS with enhanced styling
enhanced_css = load_css() + """
<style>
    /* Enhanced responsive design */
    .main-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    /* Smooth tab transitions */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 15px 15px 0 0;
        margin-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: rgba(255, 255, 255, 0.8);
        font-weight: 600;
        font-size: 1.1rem;
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
        transition: all 0.3s ease;
        border: none;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        color: #ffffff;
        background: rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
    }
    
    /* Enhanced card styling */
    .card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.8);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    }
    
    /* Metric styling */
    .metric-container {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 15px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        transform: scale(1.02);
    }
    
    /* Risk indicator styling */
    .risk-indicator {
        border-radius: 15px;
        padding: 1.2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    /* Animation for loading */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease forwards;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .card {
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            padding: 0.5rem 1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-size: 0.9rem;
            padding: 0.6rem 1rem;
        }
    }
</style>
"""

st.markdown(enhanced_css, unsafe_allow_html=True)

# App header with Pearson Creek logo
st.markdown(app_header(), unsafe_allow_html=True)

# Define directory paths
local_dir = r"D:\Benson\aUpWork\Ben Ruff\Implementation\Data"
github_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data")

# Choose which directory to use (True for local, False for GitHub)
use_local = True
data_dir = local_dir if use_local else github_dir

# Define default date range
end_date = datetime.datetime.now()
start_date = datetime.datetime(2010, 1, 1)

# Load data function
@st.cache_data
def load_data(data_path):
    try:
        # Load data files
        spy_df = pd.read_csv(os.path.join(data_path, "SPY.csv"))
        spy_dividends_df = pd.read_csv(os.path.join(data_path, "SPY Dividends.csv"))
        vti_df = pd.read_csv(os.path.join(data_path, "VTI.csv"))
        vti_dividends_df = pd.read_csv(os.path.join(data_path, "VTI Dividends.csv"))
        
        # Convert 'Date' columns to datetime and set as index
        for df in [spy_df, spy_dividends_df, vti_df, vti_dividends_df]:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
        return spy_df, spy_dividends_df, vti_df, vti_dividends_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None

# Load data with a progress indicator
with st.spinner("🔄 Loading ETF data..."):
    spy_df, spy_dividends_df, vti_df, vti_dividends_df = load_data(data_dir)

# Check if data loaded successfully
if spy_df is not None and vti_df is not None:
    
    # Main content in tabs - Margin Calculator first as requested
    tabs = st.tabs([
        "🧮 Margin Calculator",
        "📊 Market Overview", 
        "📈 Price Analysis", 
        "💰 Dividend Analysis"
    ])
    
    with tabs[0]:
        # Margin calculator tab - now first
        st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
        
        st.header("🧮 Advanced Margin Calculator")
        
        # Add explanatory text
        st.markdown(margin_calculator_explanation(), unsafe_allow_html=True)
        
        # Create responsive layout
        input_col, results_col = st.columns([1, 1], gap="large")
        
        with input_col:
            st.subheader("📊 Investment Parameters")
            
            # ETF selection first
            etf_selection = st.selectbox(
                "Select ETF",
                ["SPY", "VTI"],
                help="Choose the ETF you want to analyze"
            )
            
            # Get current price for selected ETF
            if etf_selection == "SPY" and not spy_df.empty:
                current_price = spy_df['Close'].iloc[-1]
                selected_df = spy_df
            elif etf_selection == "VTI" and not vti_df.empty:
                current_price = vti_df['Close'].iloc[-1]
                selected_df = vti_df
            else:
                current_price = 0
                selected_df = pd.DataFrame()
            
            st.info(f"💲 Current {etf_selection} Price: **${current_price:.2f}**")
            
            investment_amount = st.number_input(
                "Initial Investment Amount ($)",
                min_value=1000,
                value=10000,
                step=1000,
                help="Total amount you want to invest (including margin)"
            )
            
            margin_percentage = st.slider(
                "Margin Percentage (%)",
                min_value=0,
                max_value=100,
                value=50,
                help="Percentage of your position funded with borrowed money"
            )
            
            # Advanced settings in expandable section
            with st.expander("⚙️ Advanced Settings", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    maintenance_margin = st.slider(
                        "Maintenance Margin (%)",
                        min_value=25,
                        max_value=40,
                        value=30,
                        help="Minimum equity percentage required"
                    )
                    
                with col_b:
                    interest_rate = st.slider(
                        "Annual Interest Rate (%)",
                        min_value=1.0,
                        max_value=10.0,
                        value=5.0,
                        step=0.1,
                        help="Cost of borrowing money on margin"
                    )
                
                holding_period = st.slider(
                    "Expected Holding Period (months)",
                    min_value=1,
                    max_value=60,
                    value=12,
                    help="How long you plan to hold the position"
                )
        
        with results_col:
            st.subheader("📈 Calculation Results")
            
            # Calculate basic margin metrics
            cash_investment = investment_amount * (1 - margin_percentage/100)
            margin_loan = investment_amount * (margin_percentage/100)
            shares_purchased = investment_amount / current_price if current_price > 0 else 0
            
            # Display key metrics in an elegant format
            st.markdown(f"""
            <div class="metric-container">
                <h3 style="margin: 0; font-size: 1.2rem;">💰 Investment Breakdown</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                    <div>
                        <div style="font-size: 0.9rem; opacity: 0.8;">Your Cash</div>
                        <div style="font-size: 1.4rem; font-weight: bold;">${cash_investment:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9rem; opacity: 0.8;">Margin Loan</div>
                        <div style="font-size: 1.4rem; font-weight: bold;">${margin_loan:,.0f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if current_price > 0:
                st.metric(
                    "🔢 Shares Purchasable",
                    f"{shares_purchased:.2f}",
                    f"At ${current_price:.2f}/share"
                )
                
                # Calculate margin call price and risk
                if margin_percentage > 0:
                    # More accurate margin call calculation
                    equity_ratio = (100 - maintenance_margin) / 100
                    margin_call_price = (margin_loan / shares_purchased) / equity_ratio
                    
                    if margin_call_price > 0 and margin_call_price < current_price:
                        margin_call_drop = ((current_price - margin_call_price) / current_price) * 100
                        
                        # Risk level assessment
                        if margin_call_drop < 15:
                            risk_level = "🔴 High Risk"
                            risk_color = "#e74c3c"
                        elif margin_call_drop < 25:
                            risk_level = "🟡 Medium Risk"
                            risk_color = "#f39c12"
                        else:
                            risk_level = "🟢 Lower Risk"
                            risk_color = "#2ecc71"
                        
                        st.markdown(f"""
                        <div class="risk-indicator" style="background: linear-gradient(135deg, {risk_color}20, {risk_color}10); border-left: 4px solid {risk_color};">
                            <h4 style="margin: 0; color: {risk_color};">{risk_level}</h4>
                            <p style="margin: 0.5rem 0 0 0; color: #2c3e50;">
                                <strong>Margin Call at:</strong> ${margin_call_price:.2f}<br>
                                <strong>Price Drop Tolerance:</strong> {margin_call_drop:.1f}%
                            </p>
                        </div>
                                                 """, unsafe_allow_html=True)
        
        st.divider()
        
        # Performance simulation section
        st.subheader("🎯 Performance Simulation")
        
        scenario_col1, scenario_col2, scenario_col3 = st.columns(3)
        
        with scenario_col1:
            st.markdown("##### 📈 Bull Scenario")
            bull_gain = st.slider("Price Increase (%)", 5, 50, 20, key="bull")
            bull_value = investment_amount * (1 + bull_gain/100)
            bull_interest_cost = (margin_loan * interest_rate/100) * (holding_period/12)
            bull_profit = bull_value - investment_amount - bull_interest_cost
            bull_roi = (bull_profit / cash_investment) * 100
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2ecc7120, #2ecc7110); padding: 1rem; border-radius: 10px; border-left: 4px solid #2ecc71;">
                <div style="color: #2ecc71; font-weight: bold; font-size: 1.1rem;">+${bull_profit:,.0f}</div>
                <div style="color: #2c3e50; font-size: 0.9rem;">{bull_roi:.1f}% ROI</div>
            </div>
            """, unsafe_allow_html=True)
        
        with scenario_col2:
            st.markdown("##### ➡️ Neutral Scenario")
            neutral_gain = 0
            neutral_interest_cost = (margin_loan * interest_rate/100) * (holding_period/12)
            neutral_profit = -neutral_interest_cost
            neutral_roi = (neutral_profit / cash_investment) * 100
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f39c1220, #f39c1210); padding: 1rem; border-radius: 10px; border-left: 4px solid #f39c12;">
                <div style="color: #f39c12; font-weight: bold; font-size: 1.1rem;">${neutral_profit:,.0f}</div>
                <div style="color: #2c3e50; font-size: 0.9rem;">{neutral_roi:.1f}% ROI</div>
            </div>
            """, unsafe_allow_html=True)
        
        with scenario_col3:
            st.markdown("##### 📉 Bear Scenario")
            bear_loss = st.slider("Price Decrease (%)", 5, 40, 15, key="bear")
            bear_value = investment_amount * (1 - bear_loss/100)
            bear_interest_cost = (margin_loan * interest_rate/100) * (holding_period/12)
            bear_loss_total = investment_amount - bear_value + bear_interest_cost
            bear_roi = -(bear_loss_total / cash_investment) * 100
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e74c3c20, #e74c3c10); padding: 1rem; border-radius: 10px; border-left: 4px solid #e74c3c;">
                <div style="color: #e74c3c; font-weight: bold; font-size: 1.1rem;">-${bear_loss_total:,.0f}</div>
                <div style="color: #2c3e50; font-size: 0.9rem;">{bear_roi:.1f}% ROI</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        # Market Overview tab
        st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
        st.header("📊 Market Overview")
        
        # Add explanatory text
        st.markdown(market_overview_explanation(), unsafe_allow_html=True)
        
        # Summary statistics in two columns
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.subheader("📈 S&P 500 ETF (SPY)")
            # Calculate key metrics
            if not spy_df.empty:
                latest_price = spy_df['Close'].iloc[-1]
                price_change = spy_df['Close'].iloc[-1] - spy_df['Close'].iloc[0]
                pct_change = (price_change / spy_df['Close'].iloc[0] * 100) if spy_df['Close'].iloc[0] != 0 else 0
                
                # Display metrics in a clean format
                st.metric("Latest Price", f"${latest_price:.2f}", f"{pct_change:.2f}%")
                
                # Display key statistics
                st.markdown("**📊 Key Statistics:**")
                stats = {
                    "52-Week High": f"${spy_df['High'].max():.2f}",
                    "52-Week Low": f"${spy_df['Low'].min():.2f}",
                    "Average Volume": f"{spy_df['Volume'].mean():,.0f}",
                    "Total Dividends": f"${spy_dividends_df['Dividends'].sum():.2f}"
                }
                for key, value in stats.items():
                    st.text(f"{key}: {value}")
         
        with col2:
            st.subheader("🏢 Total Market ETF (VTI)")
            # Calculate key metrics
            if not vti_df.empty:
                latest_price = vti_df['Close'].iloc[-1]
                price_change = vti_df['Close'].iloc[-1] - vti_df['Close'].iloc[0]
                pct_change = (price_change / vti_df['Close'].iloc[0] * 100) if vti_df['Close'].iloc[0] != 0 else 0
                
                # Display metrics in a clean format
                st.metric("Latest Price", f"${latest_price:.2f}", f"{pct_change:.2f}%")
                
                # Display key statistics
                st.markdown("**📊 Key Statistics:**")
                stats = {
                    "52-Week High": f"${vti_df['High'].max():.2f}",
                    "52-Week Low": f"${vti_df['Low'].min():.2f}",
                    "Average Volume": f"{vti_df['Volume'].mean():,.0f}",
                    "Total Dividends": f"${vti_dividends_df['Dividends'].sum():.2f}"
                }
                for key, value in stats.items():
                    st.text(f"{key}: {value}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tabs[2]:
        # Price Analysis tab with date range selection
        st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
        
        # Header and date range selector
        st.header("📈 Price Analysis")
        st.markdown(price_analysis_explanation(), unsafe_allow_html=True)
        
        # Date range selector integrated into the same card
        st.subheader("📅 Select Date Range")
        st.markdown(date_range_explanation(), unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            price_start_date = st.date_input("Start Date", value=start_date, key="price_start")
        with col2:
            price_end_date = st.date_input("End Date", value=end_date, key="price_end")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            price_apply_btn = st.button("Apply Filter", use_container_width=True, key="price_apply")
        
        st.divider()
        
        # Convert dates to string format for filtering
        price_start_str = price_start_date.strftime("%Y-%m-%d")
        price_end_str = price_end_date.strftime("%Y-%m-%d")
        
        # Filter data based on selected date range
        spy_price_filtered = spy_df.loc[price_start_str:price_end_str] if not spy_df.empty else spy_df
        vti_price_filtered = vti_df.loc[price_start_str:price_end_str] if not vti_df.empty else vti_df
        
        # Plot SPY candlestick chart
        st.subheader("📊 S&P 500 ETF (SPY) Price Chart")
        if not spy_price_filtered.empty:
            fig = plot_candlestick(spy_price_filtered, 'S&P 500 ETF Candlestick Chart', 'SPY')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No SPY data available for the selected date range.")
        
        st.divider()
        
        # Plot VTI candlestick chart
        st.subheader("🏢 Total Stock Market ETF (VTI) Price Chart")
        if not vti_price_filtered.empty:
            fig = plot_candlestick(vti_price_filtered, 'Total Stock Market ETF Candlestick Chart', 'VTI')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No VTI data available for the selected date range.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tabs[3]:
        # Dividend Analysis tab with date range selection
        st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
        
        # Header and explanatory text
        st.header("💰 Dividend Analysis")
        st.markdown(dividend_analysis_explanation(), unsafe_allow_html=True)
        
        # Date range selector integrated into the same card
        st.subheader("📅 Select Date Range")
        st.markdown(date_range_explanation(), unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            div_start_date = st.date_input("Start Date", value=start_date, key="div_start")
        with col2:
            div_end_date = st.date_input("End Date", value=end_date, key="div_end")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            div_apply_btn = st.button("Apply Filter", use_container_width=True, key="div_apply")
        
        st.divider()
        
        # Convert dates to string format for filtering
        div_start_str = div_start_date.strftime("%Y-%m-%d")
        div_end_str = div_end_date.strftime("%Y-%m-%d")
        
        # Filter dividend data based on selected date range
        spy_div_filtered = spy_dividends_df.loc[div_start_str:div_end_str] if not spy_dividends_df.empty else spy_dividends_df
        vti_div_filtered = vti_dividends_df.loc[div_start_str:div_end_str] if not vti_dividends_df.empty else vti_dividends_df
        
        # Plot SPY dividends with matplotlib
        st.subheader("💵 S&P 500 ETF Dividends (SPY)")
        if not spy_div_filtered.empty:
            fig = plot_dividend_bars_mpl(spy_div_filtered, 'S&P 500 ETF Dividend Payments', 'SPY')
            if fig is not None:
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("No SPY dividend data available for the selected date range.")
        
        st.divider()
        
        # Plot VTI dividends with matplotlib
        st.subheader("💰 Total Stock Market ETF Dividends (VTI)")
        if not vti_div_filtered.empty:
            fig = plot_dividend_bars_mpl(vti_div_filtered, 'Total Stock Market ETF Dividend Payments', 'VTI')
            if fig is not None:
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("No VTI dividend data available for the selected date range.")
    
    # Footer with information
    st.markdown(app_footer(), unsafe_allow_html=True)
    
else:
    # Error message if data loading fails
    st.error("❌ Failed to load data. Please check the data path and ensure all required files are present.")
    st.markdown(f"Looking for data in: {data_dir}")
    
    # Show help information
    st.subheader("🔧 Troubleshooting")
    st.markdown("""
    Please ensure that the following files exist in the data directory:
    - SPY.csv
    - SPY Dividends.csv
    - VTI.csv
    - VTI Dividends.csv
    
    Each file should contain historical price data with columns for Date, Open, High, Low, Close, and Volume.
    Dividend files should contain Date and Dividends columns.
    """) 