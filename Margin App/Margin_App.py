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
    app_footer, navigation_explanation
)
from historical_backtest import show_historical_backtest

# Set page configuration
st.set_page_config(
    page_title="Margin Analytics Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cache CSS loading to prevent re-rendering on every interaction
@st.cache_data
def get_enhanced_css():
    return load_css()

# Load professional CSS
st.markdown(get_enhanced_css(), unsafe_allow_html=True)

# Professional app header
st.markdown(app_header(), unsafe_allow_html=True)

# Initialize session state for tab management
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Define directory paths
local_dir = r"D:\Benson\aUpWork\Ben Ruff\Implementation\Data"
github_dir = ("Data")

# Choose which directory to use (True for local, False for GitHub)
use_local = False
data_dir = local_dir if use_local else github_dir

# Define default date range
end_date = datetime.datetime.now()
start_date = datetime.datetime(2010, 1, 1)

# Optimized data loading function with better caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data(data_path):
    try:
        # Load data files
        spy_df = pd.read_csv(os.path.join(data_path, "SPY.csv"))
        spy_dividends_df = pd.read_csv(os.path.join(data_path, "SPY Dividends.csv"))
        vti_df = pd.read_csv(os.path.join(data_path, "VTI.csv"))
        vti_dividends_df = pd.read_csv(os.path.join(data_path, "VTI Dividends.csv"))
        
        # Convert 'Date' columns to datetime and set as index more efficiently
        for df in [spy_df, spy_dividends_df, vti_df, vti_dividends_df]:
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
        return spy_df, spy_dividends_df, vti_df, vti_dividends_df
    except Exception as e:
        st.error(f"Data loading error: {e}")
        st.error("Please ensure data files are available in the specified directory")
        return None, None, None, None

# Professional margin calculations
@st.cache_data
def calculate_margin_metrics(investment_amount, leverage, current_price, account_type, position_type):
    """Professional margin calculation engine"""
    cash_investment = investment_amount / leverage
    margin_loan = investment_amount - cash_investment
    shares_purchased = investment_amount / current_price if current_price > 0 else 0
    
    # Calculate maintenance margin
    if account_type == 'reg_t':
        maintenance_margin_pct = 25 if position_type == 'Long' else 30
    else:  # portfolio margin
        maintenance_margin_pct = 15 if position_type == 'Long' else 20
    
    maintenance_margin_dollar = (maintenance_margin_pct / 100) * investment_amount
    
    # Calculate margin call price
    margin_call_price = 0
    margin_call_drop = 0
    if leverage > 1 and shares_purchased > 0:
        equity_ratio = (100 - maintenance_margin_pct) / 100
        margin_call_price = (margin_loan / shares_purchased) / equity_ratio
        if margin_call_price > 0 and margin_call_price < current_price:
            margin_call_drop = ((current_price - margin_call_price) / current_price) * 100
    
    return {
        'cash_investment': cash_investment,
        'margin_loan': margin_loan,
        'shares_purchased': shares_purchased,
        'maintenance_margin_pct': maintenance_margin_pct,
        'maintenance_margin_dollar': maintenance_margin_dollar,
        'margin_call_price': margin_call_price,
        'margin_call_drop': margin_call_drop
    }

# Professional metric cards
@st.cache_data
def generate_professional_metric_card(label, value, change=None, format_type="currency"):
    """Generate professional metric cards"""
    if format_type == "currency":
        formatted_value = f"${value:,.0f}"
    elif format_type == "percentage":
        formatted_value = f"{value:.2f}%"
    elif format_type == "number":
        formatted_value = f"{value:,.2f}"
    else:
        formatted_value = str(value)
    
    change_class = ""
    change_display = ""
    if change is not None:
        if change > 0:
            change_class = "positive"
            change_display = f"+{change:.2f}%"
        elif change < 0:
            change_class = "negative"
            change_display = f"{change:.2f}%"
        else:
            change_class = "neutral"
            change_display = "0.00%"
    
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{formatted_value}</div>
        {f'<div class="metric-change {change_class}">{change_display}</div>' if change is not None else ''}
    </div>
    """

# Professional investment breakdown
@st.cache_data
def generate_investment_breakdown(investment_amount, cash_investment, margin_loan):
    return f"""
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">Portfolio Composition</div>
            <div class="card-subtitle">Capital Structure Analysis</div>
        </div>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Cash Investment</div>
                <div class="metric-value">${cash_investment:,.0f}</div>
                <div class="metric-change neutral">Your Capital</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Margin Loan</div>
                <div class="metric-value">${margin_loan:,.0f}</div>
                <div class="metric-change neutral">Borrowed Capital</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Position</div>
                <div class="metric-value">${investment_amount:,.0f}</div>
                <div class="metric-change neutral">Market Exposure</div>
            </div>
        </div>
        <p class="typography-body">
            Your capital provides the foundation for leveraged exposure. Margin loan amplifies position size 
            but introduces additional risk through interest costs and potential margin calls.
        </p>
    </div>
    """

# Load data
spy_df, spy_dividends_df, vti_df, vti_dividends_df = load_data(data_dir)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.account_type = 'reg_t'
    st.session_state.leverage_reg_t = 2.0
    st.session_state.initial_margin_reg_t = 50.0
    st.session_state.leverage_portfolio = 4.0
    st.session_state.initial_margin_portfolio = 25.0
    st.session_state.initialized = True

# Check if data loaded successfully
if spy_df is not None and vti_df is not None:
    
    # Professional Tab Navigation
    tab_labels = [
        "Margin Calculator",
        "Historical Backtest", 
        "Market Overview",
        "Price Analysis",
        "Dividend Analysis"
    ]
    
    # Initialize selected tab in session state
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = tab_labels[0]
    
    if 'tab_index' not in st.session_state:
        st.session_state.tab_index = 0
    
    # Professional navigation container
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    # Tab selector using radio buttons
    current_tab_index = tab_labels.index(st.session_state.selected_tab)
    
    selected_tab = st.radio(
        "Platform Navigation",
        tab_labels,
        index=current_tab_index,
        horizontal=True,
        key="tab_selector",
        label_visibility="collapsed"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Update session state if tab changed
    if selected_tab != st.session_state.selected_tab:
        st.session_state.selected_tab = selected_tab
        st.session_state.tab_index = tab_labels.index(selected_tab)
        st.rerun()
    
    # Display content based on selected tab
    if st.session_state.selected_tab == "Margin Calculator":
        # Professional Margin Calculator Interface
        st.markdown(margin_calculator_explanation(), unsafe_allow_html=True)
        
        # Create professional layout
        input_col, results_col = st.columns([1, 1], gap="large")
        
        with input_col:
            st.markdown("""
            <div class="professional-card">
                <div class="card-header">
                    <div class="card-title">Position Parameters</div>
                    <div class="card-subtitle">Configure trading parameters</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Account type selection
            st.markdown('<div class="input-group">', unsafe_allow_html=True)
            st.markdown('<div class="input-label">Account Type</div>', unsafe_allow_html=True)
            
            account_col1, account_col2 = st.columns(2)
            
            with account_col1:
                if st.button(
                    "Reg-T Account",
                    use_container_width=True,
                    key="reg_t_btn"
                ):
                    st.session_state.account_type = 'reg_t'
            
            with account_col2:
                if st.button(
                    "Portfolio Margin Account", 
                    use_container_width=True,
                    key="portfolio_btn"
                ):
                    st.session_state.account_type = 'portfolio'
            
            account_type = st.session_state.account_type
            
            # Display selected account
            if account_type == 'reg_t':
                st.success("Reg-T Account Selected: Standard margin account with 2:1 maximum leverage")
                max_leverage = 2.0
                default_leverage = 2.0
                default_initial_margin = 50.0
            else:
                st.success("Portfolio Margin Account Selected: Advanced account with up to 7:1 leverage")
                max_leverage = 7.0
                default_leverage = 4.0
                default_initial_margin = 25.0
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ETF and Position selection
            etf_col1, etf_col2, etf_col3 = st.columns(3)
            
            with etf_col1:
                st.markdown('<div class="input-label">Instrument</div>', unsafe_allow_html=True)
                etf_selection = st.selectbox(
                    "Select ETF",
                    ["SPY", "VTI"],
                    help="Choose the ETF instrument for analysis",
                    label_visibility="collapsed"
                )
            
            # Get current market price
            if etf_selection == "SPY" and not spy_df.empty:
                current_market_price = spy_df['Close'].iloc[-1]
                selected_df = spy_df
            elif etf_selection == "VTI" and not vti_df.empty:
                current_market_price = vti_df['Close'].iloc[-1]
                selected_df = vti_df
            else:
                current_market_price = 0
                selected_df = pd.DataFrame()
            
            with etf_col2:
                st.markdown('<div class="input-label">Price Override</div>', unsafe_allow_html=True)
                custom_price = st.number_input(
                    "Price Override",
                    min_value=0.01,
                    value=float(current_market_price) if current_market_price > 0 else 100.0,
                    step=0.01,
                    help="Override market price for scenario analysis",
                    label_visibility="collapsed",
                    format="%.2f"
                )
                current_price = custom_price
            
            with etf_col3:
                st.markdown('<div class="input-label">Position Type</div>', unsafe_allow_html=True)
                position_type = st.selectbox(
                    "Position Type",
                    ["Long", "Short"],
                    index=0,
                    help="Long (buy) or Short (sell) position",
                    label_visibility="collapsed"
                )
            
            # Price information
            if abs(custom_price - current_market_price) < 0.01:
                st.info(f"Using Market Price: ${current_price:.2f}")
            else:
                st.info(f"Using Custom Price: ${current_price:.2f}")
            
            # Investment amount
            st.markdown('<div class="input-group">', unsafe_allow_html=True)
            st.markdown('<div class="input-label">Position Size</div>', unsafe_allow_html=True)
            investment_amount = st.number_input(
                "Position Size",
                min_value=1000,
                value=100000000,
                step=1000,
                help="Total position size including leverage",
                label_visibility="collapsed"
            )
            st.markdown('<div class="input-description">Total market exposure including borrowed funds</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Leverage configuration
            if account_type == 'reg_t':
                leverage_options = [1.0, 1.5, 2.0]
                initial_margin_options = [100.0, 66.67, 50.0]
                default_leverage_index = 2
            else:
                leverage_options = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
                initial_margin_options = [100.0, 66.67, 50.0, 40.0, 33.33, 28.57, 25.0, 22.22, 20.0, 18.18, 16.67, 15.38, 14.29]
                default_leverage_index = 6
            
            # Initialize session state for selected indices
            if f'leverage_index_{account_type}' not in st.session_state:
                st.session_state[f'leverage_index_{account_type}'] = default_leverage_index
            if f'margin_index_{account_type}' not in st.session_state:
                st.session_state[f'margin_index_{account_type}'] = default_leverage_index
            
            # Leverage selection
            st.markdown('<div class="input-group">', unsafe_allow_html=True)
            st.markdown('<div class="input-label">Leverage Ratio</div>', unsafe_allow_html=True)
            leverage_index = st.selectbox(
                "Leverage",
                range(len(leverage_options)),
                index=st.session_state[f'leverage_index_{account_type}'],
                format_func=lambda x: f"{leverage_options[x]:.1f}x",
                help="Position leverage multiplier",
                label_visibility="collapsed",
                key=f"leverage_select_{account_type}"
            )
            
            if leverage_index != st.session_state[f'leverage_index_{account_type}']:
                st.session_state[f'leverage_index_{account_type}'] = leverage_index
                st.session_state[f'margin_index_{account_type}'] = leverage_index
                st.rerun()
            
            leverage = leverage_options[leverage_index]
            st.markdown('<div class="input-description">Capital multiplication factor</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Initial margin
            st.markdown('<div class="input-group">', unsafe_allow_html=True)
            st.markdown('<div class="input-label">Initial Margin Requirement</div>', unsafe_allow_html=True)
            margin_index = st.selectbox(
                "Initial Margin",
                range(len(initial_margin_options)),
                index=st.session_state[f'margin_index_{account_type}'],
                format_func=lambda x: f"{initial_margin_options[x]:.2f}%",
                help="Required capital percentage",
                label_visibility="collapsed",
                key=f"margin_select_{account_type}"
            )
            
            if margin_index != st.session_state[f'margin_index_{account_type}']:
                st.session_state[f'margin_index_{account_type}'] = margin_index
                st.session_state[f'leverage_index_{account_type}'] = margin_index
                st.rerun()
            
            initial_margin = initial_margin_options[margin_index]
            st.markdown('<div class="input-description">Minimum equity requirement</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Advanced parameters
            with st.expander("Advanced Risk Parameters", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    interest_rate = st.slider(
                        "Annual Interest Rate (%)",
                        min_value=1.0,
                        max_value=10.0,
                        value=5.5,
                        step=0.1,
                        help="Cost of borrowing on margin"
                    )
                    
                with col_b:
                    holding_period = st.slider(
                        "Expected Holding Period (months)",
                        min_value=1,
                        max_value=60,
                        value=24,
                        help="Position duration for cost analysis"
                    )
        
        with results_col:
            st.markdown("""
            <div class="professional-card">
                <div class="card-header">
                    <div class="card-title">Risk Analytics</div>
                    <div class="card-subtitle">Position analysis & exposure metrics</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Calculate metrics
            metrics = calculate_margin_metrics(
                investment_amount, leverage, current_price, account_type, position_type
            )
            
            # Investment breakdown
            st.markdown(generate_investment_breakdown(
                investment_amount, metrics['cash_investment'], metrics['margin_loan']
            ), unsafe_allow_html=True)
            
            if current_price > 0:
                # Key metrics
                daily_interest_cost = (metrics['margin_loan'] * interest_rate / 100) / 365
                annual_interest_cost = metrics['margin_loan'] * interest_rate / 100
                breakeven_price = current_price + (annual_interest_cost / metrics['shares_purchased'] / (holding_period / 12)) if metrics['shares_purchased'] > 0 else 0
                
                # Professional metrics grid
                st.markdown(f"""
                <div class="professional-card">
                    <div class="card-header">
                        <div class="card-title">Position Metrics</div>
                    </div>
                    <div class="metrics-grid">
                        {generate_professional_metric_card("Shares Purchased", metrics['shares_purchased'], format_type="number")}
                        {generate_professional_metric_card("Daily Interest Cost", daily_interest_cost)}
                        {generate_professional_metric_card("Breakeven Price", breakeven_price)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Maintenance margin analysis
                st.markdown(f"""
                <div class="professional-card">
                    <div class="card-header">
                        <div class="card-title">Margin Requirements</div>
                        <div class="card-subtitle">Regulatory compliance thresholds</div>
                    </div>
                    <div class="metrics-grid">
                        {generate_professional_metric_card("Maintenance Margin %", metrics['maintenance_margin_pct'], format_type="percentage")}
                        {generate_professional_metric_card("Maintenance Margin $", metrics['maintenance_margin_dollar'])}
                    </div>
                    <p class="typography-body">
                        Minimum equity threshold of ${metrics['maintenance_margin_dollar']:,.0f} must be maintained 
                        to avoid margin call liquidation. Monitor position closely as market moves against you.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Interest cost analysis
                monthly_interest = (metrics['margin_loan'] * interest_rate / 100) / 12
                annual_interest = metrics['margin_loan'] * interest_rate / 100
                custom_period_interest = (metrics['margin_loan'] * interest_rate / 100) * (holding_period / 12)
                
                st.markdown(f"""
                <div class="professional-card">
                    <div class="card-header">
                        <div class="card-title">Cost Structure</div>
                        <div class="card-subtitle">Interest cost projections</div>
                    </div>
                    <div class="metrics-grid">
                        {generate_professional_metric_card("Monthly Interest", monthly_interest)}
                        {generate_professional_metric_card("Annual Interest", annual_interest)}
                        {generate_professional_metric_card(f"Custom Period ({holding_period}m)", custom_period_interest)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Risk assessment
                if leverage > 1 and metrics['margin_call_price'] > 0 and metrics['margin_call_price'] < current_price:
                    if metrics['margin_call_drop'] < 15:
                        risk_level, risk_class = "Critical Risk", "risk-high"
                    elif metrics['margin_call_drop'] < 25:
                        risk_level, risk_class = "Elevated Risk", "risk-medium"
                    else:
                        risk_level, risk_class = "Manageable Risk", "risk-low"
                    
                    st.markdown(f"""
                    <div class="risk-indicator {risk_class}">
                        <div class="card-title">{risk_level}</div>
                        <p class="typography-body">
                            <strong>Margin Call Trigger:</strong> ${metrics['margin_call_price']:.2f}<br>
                            <strong>Price Drop Tolerance:</strong> {metrics['margin_call_drop']:.1f}%
                        </p>
                        <div class="command-bar">
                            <span class="command-prompt">$</span>
                            <span class="command-text">liquidation_risk --price_drop={metrics['margin_call_drop']:.1f}% --trigger=${metrics['margin_call_price']:.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="risk-indicator risk-low">
                        <div class="card-title">No Leverage Risk</div>
                        <p class="typography-body">Position not using leverage - no margin call risk present.</p>
                    </div>
                    """, unsafe_allow_html=True)

    elif st.session_state.selected_tab == "Historical Backtest":
        # Historical Backtest with professional interface
        show_historical_backtest()
    
    elif st.session_state.selected_tab == "Market Overview":
        # Professional Market Overview
        st.markdown(market_overview_explanation(), unsafe_allow_html=True)
        
        # Summary statistics
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("""
            <div class="professional-card">
                <div class="card-header">
                    <div class="card-title">S&P 500 ETF (SPY)</div>
                    <div class="card-subtitle">Large-cap equity exposure</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not spy_df.empty:
                latest_price = spy_df['Close'].iloc[-1]
                price_change = spy_df['Close'].iloc[-1] - spy_df['Close'].iloc[0]
                pct_change = (price_change / spy_df['Close'].iloc[0] * 100) if spy_df['Close'].iloc[0] != 0 else 0
                
                st.markdown(f"""
                <div class="metrics-grid">
                    {generate_professional_metric_card("Current Price", latest_price)}
                    {generate_professional_metric_card("Total Return", pct_change, format_type="percentage")}
                    {generate_professional_metric_card("52W High", spy_df['High'].max())}
                    {generate_professional_metric_card("52W Low", spy_df['Low'].min())}
                    {generate_professional_metric_card("Avg Volume", spy_df['Volume'].mean(), format_type="number")}
                    {generate_professional_metric_card("Total Dividends", spy_dividends_df['Dividends'].sum())}
                </div>
                """, unsafe_allow_html=True)
         
        with col2:
            st.markdown("""
            <div class="professional-card">
                <div class="card-header">
                    <div class="card-title">Total Market ETF (VTI)</div>
                    <div class="card-subtitle">Broad market equity exposure</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not vti_df.empty:
                latest_price = vti_df['Close'].iloc[-1]
                price_change = vti_df['Close'].iloc[-1] - vti_df['Close'].iloc[0]
                pct_change = (price_change / vti_df['Close'].iloc[0] * 100) if vti_df['Close'].iloc[0] != 0 else 0
                
                st.markdown(f"""
                <div class="metrics-grid">
                    {generate_professional_metric_card("Current Price", latest_price)}
                    {generate_professional_metric_card("Total Return", pct_change, format_type="percentage")}
                    {generate_professional_metric_card("52W High", vti_df['High'].max())}
                    {generate_professional_metric_card("52W Low", vti_df['Low'].min())}
                    {generate_professional_metric_card("Avg Volume", vti_df['Volume'].mean(), format_type="number")}
                    {generate_professional_metric_card("Total Dividends", vti_dividends_df['Dividends'].sum())}
                </div>
                """, unsafe_allow_html=True)
        
    elif st.session_state.selected_tab == "Price Analysis":
        # Professional Price Analysis
        st.markdown(price_analysis_explanation(), unsafe_allow_html=True)
        
        # Date range selector
        st.markdown("""
        <div class="professional-card">
            <div class="card-header">
                <div class="card-title">Analysis Period</div>
                <div class="card-subtitle">Configure time range for technical analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            price_start_date = st.date_input("Start Date", value=start_date, key="price_start")
        with col2:
            price_end_date = st.date_input("End Date", value=end_date, key="price_end")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            price_apply_btn = st.button("Apply Filter", use_container_width=True, key="price_apply")
        
        # Filter data
        if not spy_df.empty:
            spy_price_filtered = spy_df.loc[price_start_date:price_end_date]
        else:
            spy_price_filtered = spy_df
            
        if not vti_df.empty:
            vti_price_filtered = vti_df.loc[price_start_date:price_end_date]
        else:
            vti_price_filtered = vti_df
        
        # SPY chart
        st.markdown("""
        <div class="professional-card">
            <div class="card-header">
                <div class="card-title">S&P 500 ETF Price Action</div>
                <div class="card-subtitle">Technical analysis & price discovery</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not spy_price_filtered.empty:
            fig = plot_candlestick(spy_price_filtered, 'SPY Price Analysis', 'SPY')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No SPY data available for selected period")
        
        # VTI chart
        st.markdown("""
        <div class="professional-card">
            <div class="card-header">
                <div class="card-title">Total Market ETF Price Action</div>
                <div class="card-subtitle">Broad market technical analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not vti_price_filtered.empty:
            fig = plot_candlestick(vti_price_filtered, 'VTI Price Analysis', 'VTI')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No VTI data available for selected period")
        
    elif st.session_state.selected_tab == "Dividend Analysis":
        # Professional Dividend Analysis
        st.markdown(dividend_analysis_explanation(), unsafe_allow_html=True)
        
        # Date range selector
        st.markdown("""
        <div class="professional-card">
            <div class="card-header">
                <div class="card-title">Analysis Period</div>
                <div class="card-subtitle">Configure time range for dividend analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            div_start_date = st.date_input("Start Date", value=start_date, key="div_start")
        with col2:
            div_end_date = st.date_input("End Date", value=end_date, key="div_end")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            div_apply_btn = st.button("Apply Filter", use_container_width=True, key="div_apply")
        
        # Filter dividend data
        if not spy_dividends_df.empty:
            spy_div_filtered = spy_dividends_df.loc[div_start_date:div_end_date]
        else:
            spy_div_filtered = spy_dividends_df
            
        if not vti_dividends_df.empty:
            vti_div_filtered = vti_dividends_df.loc[div_start_date:div_end_date]
        else:
            vti_div_filtered = vti_dividends_df
        
        # SPY dividends
        st.markdown("""
        <div class="professional-card">
            <div class="card-header">
                <div class="card-title">S&P 500 ETF Dividend Flow</div>
                <div class="card-subtitle">Income distribution analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not spy_div_filtered.empty:
            fig = plot_dividend_bars_mpl(spy_div_filtered, 'SPY Dividend Analysis', 'SPY')
            if fig is not None:
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("No SPY dividend data available for selected period")
        
        # VTI dividends
        st.markdown("""
        <div class="professional-card">
            <div class="card-header">
                <div class="card-title">Total Market ETF Dividend Flow</div>
                <div class="card-subtitle">Broad market income analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not vti_div_filtered.empty:
            fig = plot_dividend_bars_mpl(vti_div_filtered, 'VTI Dividend Analysis', 'VTI')
            if fig is not None:
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("No VTI dividend data available for selected period")
    
    # Professional footer
    st.markdown(app_footer(), unsafe_allow_html=True)
    
else:
    # Professional error handling
    st.markdown("""
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">System Error</div>
            <div class="card-subtitle">Data loading failure</div>
        </div>
        <p class="typography-body">
            Failed to load market data. Please verify data path configuration and ensure 
            all required data files are present in the specified directory.
        </p>
        <div class="command-bar">
            <span class="command-prompt">$</span>
            <span class="command-text">data.path --directory={data_dir}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">Required Files</div>
        </div>
        <p class="typography-body">
            The following data files must be present:
        </p>
        <ul class="typography-body">
            <li>SPY.csv - S&P 500 ETF price data</li>
            <li>SPY Dividends.csv - S&P 500 ETF dividend data</li>
            <li>VTI.csv - Total Market ETF price data</li>
            <li>VTI Dividends.csv - Total Market ETF dividend data</li>
        </ul>
    </div>
    """, unsafe_allow_html=True) 