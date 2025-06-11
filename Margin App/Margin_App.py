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
from historical_backtest import show_historical_backtest

# Set page configuration
st.set_page_config(
    page_title="ETF Margin Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cache CSS loading to prevent re-rendering on every interaction
@st.cache_data
def get_enhanced_css():
    return load_css() + """
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
    
    /* Parameter explanation cards */
    .param-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 2px solid #e9ecef;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
    }
    
    .param-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        border-color: #3498db;
    }
    
    .param-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .param-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #3498db;
        margin: 0.5rem 0;
    }
    
    .param-description {
        font-size: 0.9rem;
        color: #6c757d;
        line-height: 1.4;
        margin: 0;
    }
    
    .leverage-card {
        background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
        border: 2px solid #27ae60;
    }
    
    .investment-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #f1f8fe 100%);
        border: 2px solid #2196f3;
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
        
        .param-card {
            padding: 1rem;
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

# Load cached CSS
st.markdown(get_enhanced_css(), unsafe_allow_html=True)

# Cache app header to prevent re-rendering
@st.cache_data
def get_app_header():
    return app_header()

# App header with Pearson Creek logo
st.markdown(get_app_header(), unsafe_allow_html=True)

# Initialize session state for tab management
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0  # Default to first tab (Margin Calculator)

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
            df.sort_index(inplace=True)  # Ensure sorted for faster filtering
            
        return spy_df, spy_dividends_df, vti_df, vti_dividends_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None

# Cache margin calculations to prevent recalculation on every slider change
@st.cache_data
def calculate_margin_metrics(investment_amount, leverage, current_price, account_type, position_type):
    """Optimized margin calculation function"""
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

# Cache scenario calculations
@st.cache_data
def calculate_scenarios(investment_amount, margin_loan, cash_investment, interest_rate, holding_period, bull_gain, bear_loss):
    """Optimized scenario calculation function"""
    # Bull scenario
    bull_value = investment_amount * (1 + bull_gain/100)
    bull_interest_cost = (margin_loan * interest_rate/100) * (holding_period/12)
    bull_profit = bull_value - investment_amount - bull_interest_cost
    bull_roi = (bull_profit / cash_investment) * 100 if cash_investment > 0 else 0
    
    # Neutral scenario
    neutral_interest_cost = (margin_loan * interest_rate/100) * (holding_period/12)
    neutral_profit = -neutral_interest_cost
    neutral_roi = (neutral_profit / cash_investment) * 100 if cash_investment > 0 else 0
    
    # Bear scenario
    bear_value = investment_amount * (1 - bear_loss/100)
    bear_interest_cost = (margin_loan * interest_rate/100) * (holding_period/12)
    bear_loss_total = investment_amount - bear_value + bear_interest_cost
    bear_roi = -(bear_loss_total / cash_investment) * 100 if cash_investment > 0 else 0
    
    return {
        'bull': {'profit': bull_profit, 'roi': bull_roi},
        'neutral': {'profit': neutral_profit, 'roi': neutral_roi},
        'bear': {'loss': bear_loss_total, 'roi': bear_roi}
    }

# Optimized HTML generation functions
@st.cache_data
def generate_investment_card(investment_amount):
    return f"""
    <div class="param-card investment-card" style="padding: 1rem; margin: 0.5rem 0;">
        <div class="param-title" style="font-size: 1rem;">
            💰 Investment Amount
        </div>
        <div class="param-value" style="font-size: 1.1rem;">${investment_amount:,.0f}</div>
        <div class="param-description" style="font-size: 0.85rem;">
            This is the total position size you want to control, including both your own cash and borrowed funds. 
            A larger investment amount increases both potential profits and risks.
        </div>
    </div>
    """

@st.cache_data
def generate_leverage_card(leverage):
    margin_percentage = ((leverage - 1) / leverage) * 100
    return f"""
    <div class="param-card leverage-card" style="padding: 1rem; margin: 0.5rem 0;">
        <div class="param-title" style="font-size: 1rem;">
            ⚡ Leverage
        </div>
        <div class="param-value" style="font-size: 1.1rem;">{leverage:.1f}x ({margin_percentage:.1f}% borrowed)</div>
        <div class="param-description" style="font-size: 0.85rem;">
            Leverage multiplies your buying power. {leverage:.1f}x leverage means you control {leverage:.1f} times 
            your cash investment. Higher leverage amplifies both gains and losses significantly.
        </div>
    </div>
    """

# Load data with optimized caching
spy_df, spy_dividends_df, vti_df, vti_dividends_df = load_data(data_dir)

# Initialize session state more efficiently
if 'initialized' not in st.session_state:
    st.session_state.account_type = 'reg_t'
    st.session_state.leverage_reg_t = 2.0
    st.session_state.initial_margin_reg_t = 50.0
    st.session_state.leverage_portfolio = 4.0
    st.session_state.initial_margin_portfolio = 25.0
    st.session_state.initialized = True

# Check if data loaded successfully
if spy_df is not None and vti_df is not None:
    
    # --- Custom Tab Implementation for Streamlit 1.45.1 ---
    tab_labels = [
        "🧮 Margin Calculator",
        "📊 Historical Backtest",
        "📈 Market Overview",
        "💹 Price Analysis",
        "💰 Dividend Analysis",
        "🎲 Kelly Criterion"
    ]
    
    # Initialize selected tab in session state
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = tab_labels[0]
    
    # Initialize tab index for proper state tracking
    if 'tab_index' not in st.session_state:
        st.session_state.tab_index = 0
    
    # Add custom CSS for beautiful tab styling
    st.markdown("""
    <style>
        /* Hide the default radio button circles */
        div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        
        /* Style the radio button container */
        div[role="radiogroup"] {
            background: transparent;
            padding: 1rem 0;
            margin: 0;
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        /* Style each radio button label as an independent box */
        div[role="radiogroup"] > label {
            background: linear-gradient(145deg, #ffffff, #f0f0f0);
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 1rem 2rem !important;
            margin: 0 !important;
            transition: all 0.3s ease;
            color: #555 !important;
            font-weight: 600 !important;
            font-size: 1.05rem !important;
            text-align: center;
            min-width: 180px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            position: relative;
            overflow: hidden;
        }
        
        /* Individual color schemes for each tab */
        /* Margin Calculator - Blue/Purple */
        div[role="radiogroup"] > label:nth-child(1) {
            background: linear-gradient(145deg, #e6f2ff, #f0e6ff);
            border-color: #b3d9ff;
            color: #4a5568 !important;
        }
        
        /* Historical Backtest - Green */
        div[role="radiogroup"] > label:nth-child(2) {
            background: linear-gradient(145deg, #e6ffe6, #f0fff0);
            border-color: #b3ffb3;
            color: #2d5016 !important;
        }
        
        /* Market Overview - Orange/Gold */
        div[role="radiogroup"] > label:nth-child(3) {
            background: linear-gradient(145deg, #fff9e6, #ffe6cc);
            border-color: #ffd9b3;
            color: #7c4e00 !important;
        }
        
        /* Price Analysis - Cyan/Blue */
        div[role="radiogroup"] > label:nth-child(4) {
            background: linear-gradient(145deg, #e6ffff, #e6f7ff);
            border-color: #b3e6ff;
            color: #005a7c !important;
        }
        
        /* Dividend Analysis - Teal/Green */
        div[role="radiogroup"] > label:nth-child(5) {
            background: linear-gradient(145deg, #e6fff5, #e6ffe6);
            border-color: #b3ffd9;
            color: #00664d !important;
        }
        
        /* Kelly Criterion - Purple/Pink */
        div[role="radiogroup"] > label:nth-child(6) {
            background: linear-gradient(145deg, #ffe6f7, #f3e6ff);
            border-color: #ffb3e6;
            color: #66004d !important;
        }
        
        /* Add gradient overlay on hover */
        div[role="radiogroup"] > label::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }
        
        /* Hover effects with color-specific shadows */
        div[role="radiogroup"] > label:nth-child(1):hover {
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            border-color: #667eea;
        }
        
        div[role="radiogroup"] > label:nth-child(2):hover {
            box-shadow: 0 8px 25px rgba(52, 211, 153, 0.3);
            border-color: #34d399;
        }
        
        div[role="radiogroup"] > label:nth-child(3):hover {
            box-shadow: 0 8px 25px rgba(251, 191, 36, 0.3);
            border-color: #fbbf24;
        }
        
        div[role="radiogroup"] > label:nth-child(4):hover {
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
            border-color: #3b82f6;
        }
        
        div[role="radiogroup"] > label:nth-child(5):hover {
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
            border-color: #10b981;
        }
        
        div[role="radiogroup"] > label:nth-child(6):hover {
            box-shadow: 0 8px 25px rgba(217, 70, 239, 0.3);
            border-color: #d946ef;
        }
        
        div[role="radiogroup"] > label:hover {
            transform: translateY(-3px);
        }
        
        div[role="radiogroup"] > label:hover::before {
            opacity: 0.1;
        }
        
        /* Selected tab styling - maintains purple gradient */
        div[role="radiogroup"] > label[data-checked="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: 2px solid transparent;
            color: white !important;
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        /* Tab container separator - more subtle */
        hr {
            margin: 1rem 0 2rem 0 !important;
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, #e0e0e0 50%, transparent 100%);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            div[role="radiogroup"] > label {
                min-width: 140px;
                padding: 0.8rem 1.2rem !important;
                font-size: 0.95rem !important;
            }
        }
        
        /* Add subtle animation to tabs */
        @keyframes tabFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-2px); }
        }
        
        div[role="radiogroup"] > label {
            animation: tabFloat 3s ease-in-out infinite;
            animation-delay: calc(var(--tab-index) * 0.1s);
        }
        
        /* Set animation delays for each tab */
        div[role="radiogroup"] > label:nth-child(1) { --tab-index: 0; }
        div[role="radiogroup"] > label:nth-child(2) { --tab-index: 1; }
        div[role="radiogroup"] > label:nth-child(3) { --tab-index: 2; }
        div[role="radiogroup"] > label:nth-child(4) { --tab-index: 3; }
        div[role="radiogroup"] > label:nth-child(5) { --tab-index: 4; }
        div[role="radiogroup"] > label:nth-child(6) { --tab-index: 5; }
        
        /* Pause animation on hover */
        div[role="radiogroup"] > label:hover,
        div[role="radiogroup"] > label[data-checked="true"] {
            animation-play-state: paused;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create tab selector using radio buttons horizontally with improved state management
    current_tab_index = tab_labels.index(st.session_state.selected_tab)
    
    selected_tab = st.radio(
        "Navigation",
        tab_labels,
        index=current_tab_index,
        horizontal=True,
        key="tab_selector",
        label_visibility="collapsed"
    )
    
    # Only update session state if the tab actually changed
    if selected_tab != st.session_state.selected_tab:
        st.session_state.selected_tab = selected_tab
        st.session_state.tab_index = tab_labels.index(selected_tab)
        st.rerun()
    
    st.markdown("---")
    
    # Display content based on selected tab
    if st.session_state.selected_tab == "🧮 Margin Calculator":
        with st.container():
            # Margin calculator tab - now first and optimized
            st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
            
            st.header("🧮 Advanced Margin Calculator")
            
            # Add explanatory text
            st.markdown(margin_calculator_explanation(), unsafe_allow_html=True)
            
            # Create responsive layout
            input_col, results_col = st.columns([1, 1], gap="large")
            
            with input_col:
                st.subheader("📊 Investment Parameters")
                
                # Account type toggle
                st.markdown("### 🏦 Account Type")
                account_col1, account_col2 = st.columns(2)
                
                with account_col1:
                    if st.button(
                        "🏛️ Reg-T Account",
                        use_container_width=True,
                        key="reg_t_btn"
                    ):
                        st.session_state.account_type = 'reg_t'
                
                with account_col2:
                    if st.button(
                        "💼 Portfolio Margin Account", 
                        use_container_width=True,
                        key="portfolio_btn"
                    ):
                        st.session_state.account_type = 'portfolio'
                
                account_type = st.session_state.account_type
                
                # Display selected account with checkmark
                if account_type == 'reg_t':
                    st.success("✅ **Reg-T Account Selected**: Standard margin account with 2:1 maximum leverage")
                    max_leverage = 2.0
                    default_leverage = 2.0
                    default_initial_margin = 50.0
                else:
                    st.success("✅ **Portfolio Margin Account Selected**: Advanced account with up to 7:1 leverage")
                    max_leverage = 7.0
                    default_leverage = 4.0
                    default_initial_margin = 25.0
                
                st.markdown("---")
                
                # ETF and Position selection in three columns
                etf_col1, etf_col2, etf_col3 = st.columns(3)
                
                with etf_col1:
                    st.markdown("**Select ETF**")
                    etf_selection = st.selectbox(
                        "Select ETF",
                        ["SPY", "VTI"],
                        help="Choose the ETF you want to analyze",
                        label_visibility="collapsed"
                    )
                
                # Get current market price for selected ETF
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
                    st.markdown("**Input ETF Price**")
                    custom_price = st.number_input(
                        "Input ETF Price",
                        min_value=0.01,
                        value=float(current_market_price) if current_market_price > 0 else 100.0,
                        step=0.01,
                        help="Enter a custom price for analysis",
                        label_visibility="collapsed",
                        format="%.2f"
                    )
                    
                    # Use custom price for calculations
                    current_price = custom_price
                
                with etf_col3:
                    st.markdown("**Select Position**")
                    position_type = st.selectbox(
                        "Select Position",
                        ["Long", "Short"],
                        index=0,
                        help="Choose whether you're buying (long) or selling short",
                        label_visibility="collapsed"
                    )
                
                # Display current price with indication if it's custom or market price
                if abs(custom_price - current_market_price) < 0.01:
                    st.info(f"💲 Current {etf_selection} Price: ${current_price:.2f} (Market Price)")
                else:
                    st.info(f"💲 Using Custom {etf_selection} Price: ${current_price:.2f}")
                
                st.markdown("**Initial Investment Amount ($)**")
                investment_amount = st.number_input(
                    "Initial Investment Amount ($)",
                    min_value=1000,
                    value=100000000,
                    step=1000,
                    help="Total amount you want to invest (including margin)",
                    label_visibility="collapsed"
                )
                
                # Investment Amount Card - cached for performance
                st.markdown(generate_investment_card(investment_amount), unsafe_allow_html=True)
                
                # Define predefined values for different account types
                if account_type == 'reg_t':
                    leverage_options = [1.0, 1.5, 2.0]
                    initial_margin_options = [100.0, 66.67, 50.0]
                    default_leverage_index = 2  # 2.0x leverage (50% margin)
                else:  # portfolio margin
                    leverage_options = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
                    initial_margin_options = [100.0, 66.67, 50.0, 40.0, 33.33, 28.57, 25.0, 22.22, 20.0, 18.18, 16.67, 15.38, 14.29]
                    default_leverage_index = 6  # 4.0x leverage (25% margin)
                
                # Initialize session state for selected indices
                if f'leverage_index_{account_type}' not in st.session_state:
                    st.session_state[f'leverage_index_{account_type}'] = default_leverage_index
                if f'margin_index_{account_type}' not in st.session_state:
                    st.session_state[f'margin_index_{account_type}'] = default_leverage_index
                
                # Leverage parameter
                st.markdown("**Leverage**")
                leverage_index = st.selectbox(
                    "Leverage",
                    range(len(leverage_options)),
                    index=st.session_state[f'leverage_index_{account_type}'],
                    format_func=lambda x: f"{leverage_options[x]:.1f}x",
                    help="Multiplier for your investment",
                    label_visibility="collapsed",
                    key=f"leverage_select_{account_type}"
                )
                
                # Update margin index when leverage changes
                if leverage_index != st.session_state[f'leverage_index_{account_type}']:
                    st.session_state[f'leverage_index_{account_type}'] = leverage_index
                    st.session_state[f'margin_index_{account_type}'] = leverage_index
                    st.rerun()
                
                leverage = leverage_options[leverage_index]
                
                # Leverage Card - cached for performance
                st.markdown(generate_leverage_card(leverage), unsafe_allow_html=True)
                
                # Initial Margin parameter
                st.markdown("**Initial Margin**")
                margin_index = st.selectbox(
                    "Initial Margin",
                    range(len(initial_margin_options)),
                    index=st.session_state[f'margin_index_{account_type}'],
                    format_func=lambda x: f"{initial_margin_options[x]:.2f}%",
                    help="Percentage of position value you must provide upfront",
                    label_visibility="collapsed",
                    key=f"margin_select_{account_type}"
                )
                
                # Update leverage index when margin changes
                if margin_index != st.session_state[f'margin_index_{account_type}']:
                    st.session_state[f'margin_index_{account_type}'] = margin_index
                    st.session_state[f'leverage_index_{account_type}'] = margin_index
                    st.rerun()
                
                initial_margin = initial_margin_options[margin_index]
                
                # Initial Margin Card - using selected values
                st.markdown(f"""
                <div class="param-card" style="background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); border: 2px solid #27ae60; padding: 1rem; margin: 0.5rem 0;">
                    <div class="param-title" style="font-size: 1rem;">📋 Initial Margin</div>
                    <div class="param-value" style="font-size: 1.1rem;">{initial_margin:.2f}%</div>
                    <div class="param-description" style="font-size: 0.85rem;">
                        The percentage of the position value you must provide upfront. Lower initial margin means higher leverage.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Advanced settings in expandable section
                with st.expander("⚙️ Advanced Settings", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        interest_rate = st.slider(
                            "Annual Interest Rate (%)",
                            min_value=1.0,
                            max_value=10.0,
                            value=5.5,
                            step=0.1,
                            help="Cost of borrowing money on margin"
                        )
                        
                    with col_b:
                        holding_period = st.slider(
                            "Expected Holding Period (months)",
                            min_value=1,
                            max_value=60,
                            value=24,
                            help="How long you plan to hold the position"
                        )
                    
                    # Advanced settings parameter cards
                    st.markdown("### ⚙️ Advanced Parameters")
                    
                    adv_col1, adv_col2 = st.columns(2)
                    
                    with adv_col1:
                        st.markdown(f"""
                        <div class="param-card" style="background: linear-gradient(135deg, #ffebee 0%, #fff5f5 100%); border: 2px solid #f44336; padding: 1rem; margin: 0.5rem 0;">
                            <div class="param-title" style="font-size: 1rem;">
                                💸 Interest Rate
                            </div>
                            <div class="param-value" style="font-size: 1.1rem;">{interest_rate}%</div>
                            <div class="param-description" style="font-size: 0.85rem;">
                                Annual cost of borrowing money on margin. This is charged on the borrowed portion of your investment.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with adv_col2:
                        st.markdown(f"""
                        <div class="param-card" style="background: linear-gradient(135deg, #f3e5f5 0%, #faf2fc 100%); border: 2px solid #9c27b0; padding: 1rem; margin: 0.5rem 0;">
                            <div class="param-title" style="font-size: 1rem;">
                                📅 Holding Period
                            </div>
                            <div class="param-value" style="font-size: 1.1rem;">{holding_period} months</div>
                            <div class="param-description" style="font-size: 0.85rem;">
                                Expected time you'll hold the position. Affects total interest costs and scenario analysis.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            with results_col:
                st.subheader("📈 Calculation Results")
                
                # Use cached calculation function
                metrics = calculate_margin_metrics(
                    investment_amount, leverage, current_price, account_type, position_type
                )
                
                # Display key metrics in an elegant format
                st.markdown(f"""
                <div class="metric-container">
                    <h3 style="margin: 0; font-size: 1.2rem;">💰 Investment Breakdown</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.8;">Your Cash</div>
                            <div style="font-size: 1.4rem; font-weight: bold;">${metrics['cash_investment']:,.0f}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.8;">Margin Loan</div>
                            <div style="font-size: 1.4rem; font-weight: bold;">${metrics['margin_loan']:,.0f}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.8;">Buying Power</div>
                            <div style="font-size: 1.4rem; font-weight: bold;">${investment_amount:,.0f}</div>
                        </div>
                    </div>
                    <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.9; line-height: 1.4;">
                        <strong>What this means:</strong> Your Cash is your own money, Margin Loan is borrowed from your broker, 
                        and Buying Power is the total amount of securities you can purchase (Your Cash + Margin Loan).
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if current_price > 0:
                    # Calculate additional metrics for comprehensive analysis
                    daily_interest_cost = (metrics['margin_loan'] * interest_rate / 100) / 365
                    annual_interest_cost = metrics['margin_loan'] * interest_rate / 100
                    breakeven_price = current_price + (annual_interest_cost / metrics['shares_purchased'] / (holding_period / 12)) if metrics['shares_purchased'] > 0 else 0
                    
                    # Three-column metrics display
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    
                    with metric_col1:
                        st.metric(
                            "🔢 Shares Purchasable",
                            f"{metrics['shares_purchased']:,.2f}",
                            f"At ${current_price:.2f}/share"
                        )
                    
                    with metric_col2:
                        st.metric(
                            f"💸 Daily Interest Cost ({interest_rate}% p.a)",
                            f"${daily_interest_cost:,.2f}",
                            f"${daily_interest_cost * 30:,.0f}/month"
                        )
                    
                    with metric_col3:
                        breakeven_change = ((breakeven_price - current_price) / current_price * 100) if current_price > 0 else 0
                        st.metric(
                            "🎯 Breakeven Price",
                            f"${breakeven_price:.2f}",
                            f"{breakeven_change:+.1f}% needed"
                        )
                    
                    # Metrics explanation expandable section
                    with st.expander("💡 Understanding Your Metrics", expanded=False):
                        st.markdown("### 📊 Metric Explanations")
                        
                        exp_col1, exp_col2, exp_col3 = st.columns(3)
                        
                        with exp_col1:
                            st.markdown(f"""
                            <div class="param-card" style="background: linear-gradient(135deg, #e3f2fd 0%, #f1f8fe 100%); border: 2px solid #2196f3; padding: 1rem; margin: 0.5rem 0;">
                                <div class="param-title" style="font-size: 1rem;">
                                    🔢 Shares Purchasable
                                </div>
                                <div class="param-value" style="font-size: 1.1rem;">{metrics['shares_purchased']:,.2f} shares</div>
                                <div class="param-description" style="font-size: 0.85rem;">
                                    This shows how many shares of {etf_selection} you can buy with your total buying power. 
                                    More shares mean higher exposure to price movements, both up and down. This determines 
                                    your position size and profit/loss per dollar of price change.
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with exp_col2:
                            st.markdown(f"""
                            <div class="param-card" style="background: linear-gradient(135deg, #ffebee 0%, #fff5f5 100%); border: 2px solid #f44336; padding: 1rem; margin: 0.5rem 0;">
                                <div class="param-title" style="font-size: 1rem;">
                                    💸 Daily Interest Cost ({interest_rate}% p.a)
                                </div>
                                <div class="param-value" style="font-size: 1.1rem;">${daily_interest_cost:,.2f}/day</div>
                                <div class="param-description" style="font-size: 0.85rem;">
                                    This is what you pay every single day to borrow money for your position. Think of it as 
                                    a daily "rental fee" for using leverage. The longer you hold, the more it costs. 
                                    This cost runs whether your position is profitable or not.
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with exp_col3:
                            st.markdown(f"""
                            <div class="param-card" style="background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); border: 2px solid #27ae60; padding: 1rem; margin: 0.5rem 0;">
                                <div class="param-title" style="font-size: 1rem;">
                                    🎯 Breakeven Price
                                </div>
                                <div class="param-value" style="font-size: 1.1rem;">${breakeven_price:.2f}</div>
                                <div class="param-description" style="font-size: 0.85rem;">
                                    This is the minimum price {etf_selection} needs to reach for you to break even after 
                                    paying all interest costs. Any price above this means profit, below means loss. 
                                    This helps you set realistic price targets and exit strategies.
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Maintenance Margin Card - simplified for performance
                    st.markdown(f"""
                    <div class="metric-container" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 1rem 0;">
                        <h3 style="margin: 0; font-size: 1.2rem;">🛡️ Maintenance Margin</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Percentage</div>
                                <div style="font-size: 1.4rem; font-weight: bold;">{metrics['maintenance_margin_pct']}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Dollar Amount</div>
                                <div style="font-size: 1.4rem; font-weight: bold;">${metrics['maintenance_margin_dollar']:,.0f}</div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.9; line-height: 1.4;">
                            <strong>What this means:</strong> You must keep at least ${metrics['maintenance_margin_dollar']:,.0f} in your account 
                            as equity. If your position loses value and your equity falls below this amount, your broker will 
                            issue a "margin call" requiring you to deposit more money or sell some positions. This protects 
                            both you and the broker from excessive losses.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Interest Costs Card
                    monthly_interest = (metrics['margin_loan'] * interest_rate / 100) / 12
                    annual_interest = metrics['margin_loan'] * interest_rate / 100
                    custom_period_interest = (metrics['margin_loan'] * interest_rate / 100) * (holding_period / 12)
                    
                    st.markdown(f"""
                    <div class="metric-container" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); margin: 1rem 0;">
                        <h3 style="margin: 0; font-size: 1.2rem;">💰 Interest Costs</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Monthly</div>
                                <div style="font-size: 1.4rem; font-weight: bold;">${monthly_interest:,.0f}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Annual</div>
                                <div style="font-size: 1.4rem; font-weight: bold;">${annual_interest:,.0f}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">Custom period ({holding_period} months)</div>
                                <div style="font-size: 1.4rem; font-weight: bold;">${custom_period_interest:,.0f}</div>
                            </div>
                        </div>
                        <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.9; line-height: 1.4;">
                            <strong>What this means:</strong> These are the total interest costs you'll pay over different time periods. 
                            The longer you hold your leveraged position, the more interest you accumulate. Factor these costs 
                            into your profit calculations and exit strategy decisions.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Risk assessment - enhanced with specific format requested
                    if leverage > 1 and metrics['margin_call_price'] > 0 and metrics['margin_call_price'] < current_price:
                        if metrics['margin_call_drop'] < 15:
                            risk_level, risk_color = "🔴 High Risk", "#e74c3c"
                        elif metrics['margin_call_drop'] < 25:
                            risk_level, risk_color = "🟡 Medium Risk", "#f39c12"
                        else:
                            risk_level, risk_color = "🟢 Lower Risk", "#2ecc71"
                        
                        st.markdown(f"""
                        <div class="risk-indicator" style="background: linear-gradient(135deg, {risk_color}20, {risk_color}10); border-left: 4px solid {risk_color};">
                            <h4 style="margin: 0; color: {risk_color};">{risk_level}</h4>
                            <p style="margin: 0.5rem 0 0 0; color: #2c3e50;">
                                <strong>Margin Call at:</strong> ${metrics['margin_call_price']:.2f}<br>
                                <strong>Price Drop Tolerance:</strong> {metrics['margin_call_drop']:.1f}%
                            </p>
                            <div style="margin: 1rem 0; padding: 0.75rem; background: rgba(255,255,255,0.7); border-radius: 8px; border-left: 3px solid {risk_color};">
                                <div style="color: #2c3e50; font-size: 0.95rem;">
                                    A <strong style="color: {risk_color};">{metrics['margin_call_drop']:.1f}%</strong> price drop would trigger a margin call at <strong style="color: {risk_color};">${metrics['margin_call_price']:.2f}</strong> price per share
                                </div>
                                <div style="color: #2c3e50; font-size: 0.95rem; margin-top: 0.8rem; padding: 0.5rem; background: rgba(240,240,240,0.8); border-radius: 6px;">
                                    <strong>📊 Margin Call Scenario:</strong><br>
                                    • <strong>Current Market Value:</strong> ${investment_amount:,.0f} (Your Equity/Cash + Margin Loan)<br>
                                    • <strong>Margin Call Triggered When Market Value Drops To:</strong> <span style="color: {risk_color}; font-weight: bold;">${metrics['shares_purchased'] * metrics['margin_call_price']:,.0f}</span><br>
                                    • <strong>Total Loss at Margin Call:</strong> <span style="color: {risk_color}; font-weight: bold;">${investment_amount - (metrics['shares_purchased'] * metrics['margin_call_price']):,.0f}</span> ({metrics['margin_call_drop']:.1f}% of your position)
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="risk-indicator" style="background: linear-gradient(135deg, #2ecc7120, #2ecc7110); border-left: 4px solid #2ecc71;">
                            <h4 style="margin: 0; color: #2ecc71;">🟢 No Leverage Risk</h4>
                            <p style="margin: 0.5rem 0 0 0; color: #2c3e50;">You're not using leverage, so there's no margin call risk.</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.divider()
            
            # Performance simulation section - coming soon
            st.subheader("🎯 Performance Simulation")
            
            # Coming soon expandable section
            with st.expander("🚀 Coming Soon - Advanced Performance Simulation Tools", expanded=False):
                st.markdown("### 📊 What's Coming")
                
                st.markdown("""
                <p style="font-size: 1.1rem; color: #6c757d; margin-bottom: 1.5rem; line-height: 1.6;">
                    Advanced performance simulation tools are under development to provide sophisticated scenario analysis.
                </p>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 🔧 Planned Features:")
                
                # Create columns for feature cards
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f1f8fe 100%); border: 2px solid #2196f3; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                        <h5 style="color: #1976d2; margin: 0 0 0.5rem 0;">🎲 Monte Carlo Simulations</h5>
                        <p style="color: #6c757d; font-size: 0.9rem; margin: 0;">Run thousands of scenarios to understand potential outcomes and risk distributions.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #fff3e0 0%, #fafafa 100%); border: 2px solid #ff9800; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                        <h5 style="color: #f57c00; margin: 0 0 0.5rem 0;">🛠️ Custom Scenario Builder</h5>
                        <p style="color: #6c757d; font-size: 0.9rem; margin: 0;">Create your own market scenarios with custom parameters and stress tests.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); border: 2px solid #27ae60; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                        <h5 style="color: #27ae60; margin: 0 0 0.5rem 0;">📈 Historical Volatility Modeling</h5>
                        <p style="color: #6c757d; font-size: 0.9rem; margin: 0;">Analyze historical price movements to model future volatility patterns.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f3e5f5 0%, #faf2fc 100%); border: 2px solid #9c27b0; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                    <h5 style="color: #7b1fa2; margin: 0 0 0.5rem 0;">⚖️ Risk-Adjusted Returns</h5>
                    <p style="color: #6c757d; font-size: 0.9rem; margin: 0;">Calculate Sharpe ratios, maximum drawdowns, and other risk metrics.</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                <div style="background: linear-gradient(135deg, #ffebee 0%, #fff5f5 100%); border: 2px solid #f44336; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                    <h5 style="color: #d32f2f; margin: 0 0 0.5rem 0;">📊 Interactive Performance Charts</h5>
                    <p style="color: #6c757d; font-size: 0.9rem; margin: 0;">Visualize performance scenarios with interactive charts showing profit/loss distributions, probability cones, and stress test results.</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                <div style="text-align: center; margin-top: 2rem; padding: 1rem; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 10px; color: white;">
                    <h5 style="margin: 0 0 0.5rem 0;">🗓️ Expected Release</h5>
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 600;">Q2 2025</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.selected_tab == "📊 Historical Backtest":
        with st.container():
            # Historical Backtest tab - now featuring the powerful backtest engine
            show_historical_backtest()
    
    elif st.session_state.selected_tab == "📈 Market Overview":
        with st.container():
            # Market Overview tab - unchanged but with optimized data access
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
        
    elif st.session_state.selected_tab == "💹 Price Analysis":
        with st.container():
            # Price Analysis tab with optimized date filtering
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
            
            # Optimized date filtering using pandas datetime indexing
            if not spy_df.empty:
                spy_price_filtered = spy_df.loc[price_start_date:price_end_date]
            else:
                spy_price_filtered = spy_df
                
            if not vti_df.empty:
                vti_price_filtered = vti_df.loc[price_start_date:price_end_date]
            else:
                vti_price_filtered = vti_df
            
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
        
    elif st.session_state.selected_tab == "💰 Dividend Analysis":
        with st.container():
            # Dividend Analysis tab with optimized date filtering
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
            
            # Optimized dividend data filtering
            if not spy_dividends_df.empty:
                spy_div_filtered = spy_dividends_df.loc[div_start_date:div_end_date]
            else:
                spy_div_filtered = spy_dividends_df
                
            if not vti_dividends_df.empty:
                vti_div_filtered = vti_dividends_df.loc[div_start_date:div_end_date]
            else:
                vti_div_filtered = vti_dividends_df
            
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
        
    elif st.session_state.selected_tab == "🎲 Kelly Criterion":
        with st.container():
            # Kelly Criterion tab
            st.header("🎲 Kelly Criterion")
            
            st.markdown("""
            <div class="card" style="text-align: center; padding: 3rem;">
                <h3 style="color: #667eea; margin-bottom: 1rem;">🚀 Coming Soon!</h3>
                <p style="font-size: 1.2rem; color: #6c757d; margin-bottom: 1.5rem;">
                    Kelly Criterion bet sizing calculator is under development.
                </p>
                <p style="color: #6c757d; line-height: 1.6;">
                    This powerful tool will help you determine optimal position sizing based on:
                </p>
                <ul style="text-align: left; color: #6c757d; max-width: 500px; margin: 1rem auto;">
                    <li>Expected returns and probabilities</li>
                    <li>Win/loss ratios</li>
                    <li>Risk tolerance parameters</li>
                    <li>Portfolio optimization</li>
                    <li>Fractional Kelly calculations</li>
                </ul>
                <div style="margin-top: 2rem; padding: 1rem; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 10px;">
                    <small style="color: #6c757d;">Expected release: Q2 2025</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
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