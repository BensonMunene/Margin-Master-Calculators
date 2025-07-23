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
    kelly_criterion_explanation, app_footer
)
from historical_backtest import show_historical_backtest
from fmp_data_provider import fmp_provider

# Set page configuration - professional dark theme
st.set_page_config(
    page_title="Margin Analytics Terminal",
    page_icon="🅼",  # Blue M for Margin Analytics
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load professional CSS
st.markdown(load_css(), unsafe_allow_html=True)

# Professional header
st.markdown(app_header(), unsafe_allow_html=True)

# Initialize session state
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Define directory paths for containerized deployment
data_dir = os.path.join(os.path.dirname(__file__), "Data")

# Define default date rangehh
end_date = datetime.datetime.now()
start_date = datetime.datetime(2010, 1, 1)

# Optimized data loading
@st.cache_data(ttl=3600)
def load_data(data_path):
    try:
        spy_df = pd.read_csv(os.path.join(data_path, "SPY.csv"))
        spy_dividends_df = pd.read_csv(os.path.join(data_path, "SPY Dividends.csv"))
        vti_df = pd.read_csv(os.path.join(data_path, "VTI.csv"))
        vti_dividends_df = pd.read_csv(os.path.join(data_path, "VTI Dividends.csv"))
        
        for df in [spy_df, spy_dividends_df, vti_df, vti_dividends_df]:
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
        return spy_df, spy_dividends_df, vti_df, vti_dividends_df
    except Exception as e:
        st.error(f"DATA LOAD ERROR: {e}")
        return None, None, None, None

# Cache calculations
@st.cache_data
def calculate_margin_metrics(investment_amount, leverage, current_price, account_type, position_type):
    cash_investment = investment_amount / leverage
    margin_loan = investment_amount - cash_investment
    shares_purchased = investment_amount / current_price if current_price > 0 else 0
    
    if account_type == 'reg_t':
        maintenance_margin_pct = 25 if position_type == 'Long' else 30
    else:
        maintenance_margin_pct = 15 if position_type == 'Long' else 20
    
    maintenance_margin_dollar = (maintenance_margin_pct / 100) * investment_amount
    
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
    
    # Professional tab labels - no emojis
    tab_labels = [
        "MARGIN CALCULATOR",
        "HISTORICAL BACKTEST",
        "MARKET OVERVIEW",
        "PRICE ANALYSIS",
        "DIVIDEND ANALYSIS",
        "KELLY CRITERION"
    ]
    
    # Initialize selected tab
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = tab_labels[0]
    
    if 'tab_index' not in st.session_state:
        st.session_state.tab_index = 0
    
    # Create professional tab selector
    current_tab_index = tab_labels.index(st.session_state.selected_tab)
    
    selected_tab = st.radio(
        "Navigation",
        tab_labels,
        index=current_tab_index,
        horizontal=True,
        key="tab_selector",
        label_visibility="collapsed"
    )
    
    if selected_tab != st.session_state.selected_tab:
        st.session_state.selected_tab = selected_tab
        st.session_state.tab_index = tab_labels.index(selected_tab)
        st.rerun()
    
    st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 1rem 0;'></div>", unsafe_allow_html=True)
    
    # Display content based on selected tab
    if st.session_state.selected_tab == "MARGIN CALCULATOR":
        with st.container():
            st.markdown("<h1>MARGIN CALCULATOR</h1>", unsafe_allow_html=True)
            
            st.markdown(margin_calculator_explanation(), unsafe_allow_html=True)
            
            # Margin Call Rules Information
            st.markdown(f"""
            <div class="terminal-card" style="border-color: #ff8c00;">
                <h4 style="color: #ff8c00; margin-bottom: 1rem;">MARGIN CALL RULES</h4>
                <div style="color: #e0e0e0; font-size: 0.9rem;">
                    <strong>REG-T ACCOUNTS:</strong> Margin call occurs when equity falls below 25% of position value (30% for short positions)<br/>
                    <strong>PORTFOLIO MARGIN:</strong> Margin call occurs when equity falls below 15% of position value (20% for short positions)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Understanding Margin Call Mechanics - Simple Text
            st.markdown("### 📘 UNDERSTANDING MARGIN CALL MECHANICS")
            
            st.markdown("""
            **Understanding Margin Call Thresholds:**
            
            A margin call occurs when your account equity (the value of your securities minus what you owe) falls below the required maintenance margin percentage. This is a critical risk management mechanism that protects both you and your broker from excessive losses.
            
            **Mathematical Foundation:**
            
            **1. Account Equity Calculation:**
            """)
            
            st.latex(r"""
            \text{Account Equity} = \text{Market Value of Securities} - \text{Margin Loan}
            """)
            
            st.markdown("""
            **2. Equity Percentage:**
            """)
            
            st.latex(r"""
            \text{Equity \%} = \frac{\text{Account Equity}}{\text{Market Value of Securities}} \times 100
            """)
            
            st.markdown("""
            **3. Margin Call Trigger Condition:**
            """)
            
            st.latex(r"""
            \text{Margin Call occurs when: } \text{Equity \%} < \text{Maintenance Margin \%}
            """)
            
            st.markdown("""
            **4. Margin Call Price Formula:**
            
            For a long position, the margin call price is calculated as:
            """)
            
            st.latex(r"""
            P_{call} = \frac{\text{Margin Loan}}{\text{Number of Shares} \times (1 - \text{Maintenance Margin \%})}
            """)
            
            st.markdown("""
            **5. Alternative Margin Call Price Formula:**
            """)
            
            st.latex(r"""
            P_{call} = P_{purchase} \times \frac{1 - \text{Initial Margin \%}}{1 - \text{Maintenance Margin \%}}
            """)
            
            st.markdown("""
            **6. Maximum Tolerable Price Drop:**
            """)
            
            st.latex(r"""
            \text{Max Drop \%} = \left(1 - \frac{P_{call}}{P_{purchase}}\right) \times 100
            """)
            
            st.markdown("""
            **How It Works:**
            
            When you buy securities on margin, you're essentially borrowing money from your broker using your securities as collateral. If the value of your securities drops significantly, your equity percentage decreases. Once it hits the maintenance threshold, your broker will issue a margin call requiring you to either deposit more funds or sell securities to restore the required equity level.
            
            **Reg-T vs Portfolio Margin Differences:**
            
            Reg-T accounts have higher maintenance requirements (25%/30%) but simpler calculations and are suitable for most retail investors. Portfolio Margin accounts offer lower requirements (15%/20%) but use complex risk-based calculations and require larger account minimums, typically $125,000 or more.
            
            **Practical Example:**
            
            With a $100,000 SPY position using 2:1 leverage in a Reg-T account ($50,000 your cash, $50,000 borrowed), a margin call triggers when your equity falls to $25,000 (25% of $100,000). This happens when SPY drops about 33.3% from your purchase price, as calculated using the formulas above.
            
            **Step-by-Step Calculation:**
            """)
            
            st.latex(r"""
            \begin{align}
            \text{Purchase Price} &= \$400 \\
            \text{Shares Purchased} &= \frac{\$100,000}{\$400} = 250 \text{ shares} \\
            \text{Margin Loan} &= \$50,000 \\
            \text{Maintenance Margin} &= 25\% \\
            \\
            P_{call} &= \frac{\$50,000}{250 \times (1 - 0.25)} \\
            &= \frac{\$50,000}{250 \times 0.75} \\
            &= \frac{\$50,000}{187.5} \\
            &= \$266.67 \\
            \\
            \text{Max Drop \%} &= \left(1 - \frac{\$266.67}{\$400}\right) \times 100 \\
            &= (1 - 0.667) \times 100 \\
            &= 33.3\%
            \end{align}
            """)
            
            st.markdown("""
            **Key Variables:**
            - **P_call**: Price at which margin call occurs
            - **P_purchase**: Original purchase price
            - **Initial Margin %**: Percentage of position funded with cash (50% for Reg-T, 25% for Portfolio Margin)
            - **Maintenance Margin %**: Minimum equity percentage required (25% for Reg-T long, 15% for Portfolio Margin long)
            """)
            
            st.warning("⚠️ **Important:** Margin calls can result in forced liquidation of your positions at unfavorable prices. Always maintain adequate cash reserves and monitor your positions closely.")
            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 1rem 0;'></div>", unsafe_allow_html=True)
            
            # Create professional layout
            input_col, results_col = st.columns([1, 1], gap="large")
            
            with input_col:
                st.markdown("<h2>INVESTMENT PARAMETERS</h2>", unsafe_allow_html=True)
                
                # Account type selection
                st.markdown("<h3>ACCOUNT TYPE</h3>", unsafe_allow_html=True)
                account_col1, account_col2 = st.columns(2)
                
                with account_col1:
                    if st.button(
                        "REG-T ACCOUNT",
                        use_container_width=True,
                        key="reg_t_btn"
                    ):
                        st.session_state.account_type = 'reg_t'
                
                with account_col2:
                    if st.button(
                        "PORTFOLIO MARGIN", 
                        use_container_width=True,
                        key="portfolio_btn"
                    ):
                        st.session_state.account_type = 'portfolio'
                
                account_type = st.session_state.account_type
                
                # Display selected account
                if account_type == 'reg_t':
                    st.success("REG-T ACCOUNT SELECTED: 2:1 MAXIMUM LEVERAGE")
                    max_leverage = 2.0
                    default_leverage = 2.0
                    default_initial_margin = 50.0
                else:
                    st.success("PORTFOLIO MARGIN SELECTED: 7:1 MAXIMUM LEVERAGE")
                    max_leverage = 7.0
                    default_leverage = 4.0
                    default_initial_margin = 25.0
                
                # ETF and Position selection
                etf_col1, etf_col2, etf_col3 = st.columns(3)
                
                with etf_col1:
                    st.markdown("**TICKER SYMBOL**")
                    ticker_input = st.text_input(
                        "Enter Ticker Symbol",
                        value="SPY",
                        help="ENTER STOCK/ETF TICKER SYMBOL",
                        label_visibility="collapsed"
                    ).upper()
                
                # Get current market price from FMP API
                if ticker_input:
                    current_market_price = fmp_provider.fetch_current_price(ticker_input)
                    if current_market_price is None:
                        current_market_price = 0
                        selected_df = pd.DataFrame()
                    else:
                        # Create a simple dataframe for compatibility (not needed for calculations)
                        selected_df = pd.DataFrame({'Close': [current_market_price]})
                else:
                    current_market_price = 0
                    selected_df = pd.DataFrame()
                
                with etf_col2:
                    st.markdown("**PRICE INPUT**")
                    custom_price = st.number_input(
                        "ETF Price",
                        min_value=0.01,
                        value=float(current_market_price) if current_market_price > 0 else 100.0,
                        step=0.01,
                        help="ENTER CUSTOM PRICE",
                        label_visibility="collapsed",
                        format="%.2f"
                    )
                    current_price = custom_price
                
                with etf_col3:
                    st.markdown("**POSITION TYPE**")
                    position_type = st.selectbox(
                        "Position",
                        ["Long", "Short"],
                        index=0,
                        help="LONG OR SHORT POSITION",
                        label_visibility="collapsed"
                    )
                
                # Display current price only if we have valid data
                if current_market_price > 0:
                    if abs(custom_price - current_market_price) < 0.01:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px solid #00a2ff; padding: 1rem; color: #e0e0e0;">
                            <strong style="color: #00a2ff;">CURRENT {ticker_input} PRICE:</strong> ${current_price:.2f} (MARKET)
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px solid #00a2ff; padding: 1rem; color: #e0e0e0;">
                            <strong style="color: #00a2ff;">CUSTOM {ticker_input} PRICE:</strong> ${current_price:.2f}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ **{ticker_input}** is not a valid ticker symbol. Please enter a valid US stock symbol (e.g., TSLA, AAPL, MSFT).")
                
                st.markdown("**INVESTMENT AMOUNT ($)**")
                investment_amount = st.number_input(
                    "Investment Amount",
                    min_value=1000,
                    value=100000000,
                    step=1000,
                    help="TOTAL POSITION SIZE",
                    label_visibility="collapsed"
                )
                
                # Professional investment card
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="data-grid">
                        <div class="data-label">INVESTMENT AMOUNT:</div>
                        <div class="data-value">${investment_amount:,.0f}</div>
                        <div class="data-label">DESCRIPTION:</div>
                        <div style="color: var(--text-secondary); font-size: 0.85rem;">
                            TOTAL POSITION SIZE INCLUDING CASH AND MARGIN
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Leverage options
                if account_type == 'reg_t':
                    leverage_options = [1.0, 1.5, 2.0]
                    initial_margin_options = [100.0, 66.67, 50.0]
                    default_leverage_index = 2
                else:
                    leverage_options = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
                    initial_margin_options = [100.0, 66.67, 50.0, 40.0, 33.33, 28.57, 25.0, 22.22, 20.0, 18.18, 16.67, 15.38, 14.29]
                    default_leverage_index = 6
                
                if f'leverage_index_{account_type}' not in st.session_state:
                    st.session_state[f'leverage_index_{account_type}'] = default_leverage_index
                if f'margin_index_{account_type}' not in st.session_state:
                    st.session_state[f'margin_index_{account_type}'] = default_leverage_index
                
                st.markdown("**LEVERAGE**")
                leverage_index = st.selectbox(
                    "Leverage",
                    range(len(leverage_options)),
                    index=st.session_state[f'leverage_index_{account_type}'],
                    format_func=lambda x: f"{leverage_options[x]:.1f}x",
                    help="LEVERAGE MULTIPLIER",
                    label_visibility="collapsed",
                    key=f"leverage_select_{account_type}"
                )
                
                if leverage_index != st.session_state[f'leverage_index_{account_type}']:
                    st.session_state[f'leverage_index_{account_type}'] = leverage_index
                    st.session_state[f'margin_index_{account_type}'] = leverage_index
                    st.rerun()
                
                leverage = leverage_options[leverage_index]
                
                # Professional leverage card
                margin_percentage = ((leverage - 1) / leverage) * 100
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="data-grid">
                        <div class="data-label">LEVERAGE:</div>
                        <div class="data-value">{leverage:.1f}X</div>
                        <div class="data-label">BORROWED:</div>
                        <div class="data-value">{margin_percentage:.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**INITIAL MARGIN**")
                margin_index = st.selectbox(
                    "Initial Margin",
                    range(len(initial_margin_options)),
                    index=st.session_state[f'margin_index_{account_type}'],
                    format_func=lambda x: f"{initial_margin_options[x]:.2f}%",
                    help="UPFRONT MARGIN REQUIREMENT",
                    label_visibility="collapsed",
                    key=f"margin_select_{account_type}"
                )
                
                if margin_index != st.session_state[f'margin_index_{account_type}']:
                    st.session_state[f'margin_index_{account_type}'] = margin_index
                    st.session_state[f'leverage_index_{account_type}'] = margin_index
                    st.rerun()
                
                initial_margin = initial_margin_options[margin_index]
                
                # Initial margin card
                st.markdown(f"""
                <div class="terminal-card">
                    <div class="data-grid">
                        <div class="data-label">INITIAL MARGIN:</div>
                        <div class="data-value">{initial_margin:.2f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Advanced settings with gray background styling
                st.markdown("""
                <style>
                /* Target the Advanced Settings expander specifically */
                div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
                    background-color: #404040 !important;
                    color: #ffffff !important;
                    padding: 1rem !important;
                    border-radius: 8px !important;
                    margin-top: 0.5rem !important;
                }
                
                /* Style the expander header */
                div[data-testid="stExpander"] summary {
                    background-color: #404040 !important;
                    color: #ffffff !important;
                    border: 1px solid #606060 !important;
                    border-radius: 8px !important;
                    padding: 0.75rem 1rem !important;
                    margin-bottom: 0.5rem !important;
                }
                
                /* Style the expansion arrow */
                div[data-testid="stExpander"] summary svg {
                    color: #ff8c00 !important;
                }
                
                /* Hover effect for expander header */
                div[data-testid="stExpander"] summary:hover {
                    background-color: #505050 !important;
                }
                
                /* Ensure all text inside expander is white */
                div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] * {
                    color: #ffffff !important;
                }
                
                /* Make slider labels orange */
                div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] label {
                    color: #ff8c00 !important;
                    font-weight: 600 !important;
                }
                
                /* Style the terminal-card within the gray expander */
                div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] .terminal-card {
                    background-color: #2a2a2a !important;
                    border: 1px solid #555555 !important;
                    margin-top: 1rem !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                with st.expander("ADVANCED SETTINGS", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        interest_rate = st.slider(
                            "ANNUAL INTEREST RATE (%)",
                            min_value=1.0,
                            max_value=10.0,
                            value=5.5,
                            step=0.1,
                            help="MARGIN INTEREST RATE"
                        )
                        
                    with col_b:
                        holding_period = st.slider(
                            "HOLDING PERIOD (MONTHS)",
                            min_value=1,
                            max_value=60,
                            value=24,
                            help="EXPECTED POSITION DURATION"
                        )
                    
                    st.markdown(f"""
                    <div class="terminal-card">
                        <div class="data-grid">
                            <div class="data-label">INTEREST RATE:</div>
                            <div class="data-value">{interest_rate}% P.A.</div>
                            <div class="data-label">HOLDING PERIOD:</div>
                            <div class="data-value">{holding_period} MONTHS</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with results_col:
                st.markdown("<h2>CALCULATION RESULTS</h2>", unsafe_allow_html=True)
                
                if current_price > 0:
                    # Calculate metrics
                    metrics = calculate_margin_metrics(
                        investment_amount, leverage, current_price, account_type, position_type
                    )
                    
                    # Display investment breakdown
                    st.markdown(f"""
                    <div class="terminal-card">
                        <h3 style="color: var(--accent-orange); margin-bottom: 1rem;">INVESTMENT BREAKDOWN</h3>
                        <div class="data-grid">
                            <div class="data-label">YOUR CASH:</div>
                            <div class="data-value">${metrics['cash_investment']:,.0f}</div>
                            <div class="data-label">MARGIN LOAN:</div>
                            <div class="data-value">${metrics['margin_loan']:,.0f}</div>
                            <div class="data-label">BUYING POWER:</div>
                            <div class="data-value">${investment_amount:,.0f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    # Calculate additional metrics
                    daily_interest_cost = (metrics['margin_loan'] * interest_rate / 100) / 365
                    annual_interest_cost = metrics['margin_loan'] * interest_rate / 100
                    breakeven_price = current_price + (annual_interest_cost / metrics['shares_purchased'] / (holding_period / 12)) if metrics['shares_purchased'] > 0 else 0
                    
                    # Three-column metrics
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    
                    with metric_col1:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                            <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Shares</div>
                            <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['shares_purchased']:,.2f}</div>
                            <div style="color: #a0a0a0; font-size: 0.9rem;">@ ${current_price:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_col2:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                            <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Daily Interest</div>
                            <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${daily_interest_cost:,.2f}</div>
                            <div style="color: #a0a0a0; font-size: 0.9rem;">${daily_interest_cost * 30:,.0f}/MO</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metric_col3:
                        breakeven_change = ((breakeven_price - current_price) / current_price * 100) if current_price > 0 else 0
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                            <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Breakeven</div>
                            <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${breakeven_price:.2f}</div>
                            <div style="color: #a0a0a0; font-size: 0.9rem;">{breakeven_change:+.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Metrics explanation
                    with st.expander("METRIC DETAILS", expanded=False):
                        st.markdown(f"""
                        <div class="terminal-card">
                            <div class="data-grid">
                                <div class="data-label">SHARES PURCHASABLE:</div>
                                <div class="data-value">{metrics['shares_purchased']:,.2f}</div>
                                <div class="data-label">DAILY INTEREST COST:</div>
                                <div class="data-value">${daily_interest_cost:,.2f}</div>
                                <div class="data-label">BREAKEVEN PRICE:</div>
                                <div class="data-value">${breakeven_price:.2f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Maintenance margin
                    st.markdown(f"""
                    <div class="terminal-card">
                        <h3 style="color: var(--accent-orange); margin-bottom: 1rem;">MAINTENANCE MARGIN</h3>
                        <div class="data-grid">
                            <div class="data-label">PERCENTAGE:</div>
                            <div class="data-value">{metrics['maintenance_margin_pct']}%</div>
                            <div class="data-label">DOLLAR AMOUNT:</div>
                            <div class="data-value">${metrics['maintenance_margin_dollar']:,.0f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Interest costs
                    monthly_interest = (metrics['margin_loan'] * interest_rate / 100) / 12
                    annual_interest = metrics['margin_loan'] * interest_rate / 100
                    custom_period_interest = (metrics['margin_loan'] * interest_rate / 100) * (holding_period / 12)
                    
                    st.markdown(f"""
                    <div class="terminal-card">
                        <h3 style="color: var(--accent-orange); margin-bottom: 1rem;">INTEREST COSTS</h3>
                        <div class="data-grid">
                            <div class="data-label">MONTHLY:</div>
                            <div class="data-value">${monthly_interest:,.0f}</div>
                            <div class="data-label">ANNUAL:</div>
                            <div class="data-value">${annual_interest:,.0f}</div>
                            <div class="data-label">{holding_period} MONTHS:</div>
                            <div class="data-value">${custom_period_interest:,.0f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Risk assessment
                    if leverage > 1 and metrics['margin_call_price'] > 0 and metrics['margin_call_price'] < current_price:
                        if metrics['margin_call_drop'] < 15:
                            risk_level, risk_color = "HIGH RISK", "var(--negative-red)"
                        elif metrics['margin_call_drop'] < 25:
                            risk_level, risk_color = "MEDIUM RISK", "var(--warning-yellow)"
                        else:
                            risk_level, risk_color = "LOWER RISK", "var(--positive-green)"
                        
                        st.markdown(f"""
                        <div class="terminal-card" style="border-color: {risk_color};">
                            <h3 style="color: {risk_color}; margin-bottom: 1rem;">{risk_level}</h3>
                            <div class="data-grid">
                                <div class="data-label">MARGIN CALL AT:</div>
                                <div class="data-value" style="color: {risk_color};">${metrics['margin_call_price']:.2f}</div>
                                <div class="data-label">PRICE DROP TOLERANCE:</div>
                                <div class="data-value" style="color: {risk_color};">{metrics['margin_call_drop']:.1f}%</div>
                                <div class="data-label">MARKET VALUE AT CALL:</div>
                                <div class="data-value" style="color: {risk_color};">${metrics['shares_purchased'] * metrics['margin_call_price']:,.0f}</div>
                                <div class="data-label">TOTAL LOSS AT CALL:</div>
                                <div class="data-value" style="color: {risk_color};">${investment_amount - (metrics['shares_purchased'] * metrics['margin_call_price']):,.0f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="terminal-card" style="border-color: var(--positive-green);">
                            <h3 style="color: var(--positive-green); margin-bottom: 1rem;">NO LEVERAGE RISK</h3>
                            <div style="color: var(--text-secondary);">NO MARGIN CALL RISK - NOT USING LEVERAGE</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Detailed Analysis Expander
                    with st.expander("📊 COMPREHENSIVE POSITION ANALYSIS", expanded=False):
                        st.markdown("<h3 style='color: var(--accent-orange); margin-bottom: 1.5rem;'>DETAILED INVESTMENT ANALYSIS & STRATEGIC INSIGHTS</h3>", unsafe_allow_html=True)
                        
                        st.markdown("## COMING SOON")
                else:
                    # Show message when ticker is invalid
                    st.markdown("""
                    <div class="terminal-card" style="border-color: #ff6b6b; background-color: rgba(255, 107, 107, 0.1);">
                        <div style="text-align: center; color: #ff6b6b; margin: 2rem 0;">
                            <div style="font-size: 2rem; margin-bottom: 1rem;">❌</div>
                            <h3 style="color: #ff6b6b; margin-bottom: 1rem;">No calculations available</h3>
                            <div style="color: #fff; margin-bottom: 1rem;">Please enter a valid US stock ticker symbol to see margin analysis.</div>
                            <div style="color: #a0a0a0; font-size: 0.9rem;">
                                Examples: <strong>TSLA</strong>, <strong>AAPL</strong>, <strong>MSFT</strong>, <strong>SPY</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 2rem 0;'></div>", unsafe_allow_html=True)
            
            # Performance simulation section
            st.markdown("<h2>PERFORMANCE SIMULATION</h2>", unsafe_allow_html=True)
            
            with st.expander("COMING SOON - ADVANCED SIMULATION TOOLS", expanded=False):
                st.markdown("""
                <div class="terminal-card">
                    <div class="data-label">PLANNED FEATURES</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 1rem;">
                        - MONTE CARLO SIMULATIONS<br/>
                        - CUSTOM SCENARIO BUILDER<br/>
                        - HISTORICAL VOLATILITY MODELING<br/>
                        - RISK-ADJUSTED RETURNS<br/>
                        - INTERACTIVE PERFORMANCE CHARTS
                    </div>
                    <div style="color: var(--accent-orange); margin-top: 1rem;">EXPECTED RELEASE: Q2 2025</div>
                </div>
                """, unsafe_allow_html=True)

    elif st.session_state.selected_tab == "HISTORICAL BACKTEST":
        with st.container():
            show_historical_backtest()
    
    elif st.session_state.selected_tab == "MARKET OVERVIEW":
        with st.container():
            st.markdown("<h1>MARKET OVERVIEW</h1>", unsafe_allow_html=True)
            
            st.markdown(market_overview_explanation(), unsafe_allow_html=True)
            
            # Fetch SPY and VTI data from FMP API
            with st.spinner("Loading market data..."):
                spy_prices, spy_dividends, _ = fmp_provider.get_combined_data('SPY', '2020-01-01', end_date.strftime('%Y-%m-%d'))
                vti_prices, vti_dividends, _ = fmp_provider.get_combined_data('VTI', '2020-01-01', end_date.strftime('%Y-%m-%d'))
            
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                st.markdown("<h2>S&P 500 ETF (SPY)</h2>", unsafe_allow_html=True)
                if not spy_prices.empty:
                    latest_price = spy_prices['Close'].iloc[-1]
                    price_change = spy_prices['Close'].iloc[-1] - spy_prices['Close'].iloc[0]
                    pct_change = (price_change / spy_prices['Close'].iloc[0] * 100) if spy_prices['Close'].iloc[0] != 0 else 0
                    
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Latest Price</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${latest_price:.2f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">{pct_change:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div class="terminal-card">
                        <div class="data-grid">
                            <div class="data-label">52-WEEK HIGH:</div>
                            <div class="data-value">${:.2f}</div>
                            <div class="data-label">52-WEEK LOW:</div>
                            <div class="data-value">${:.2f}</div>
                            <div class="data-label">AVG VOLUME:</div>
                            <div class="data-value">{:,.0f}</div>
                            <div class="data-label">TOTAL DIVIDENDS:</div>
                            <div class="data-value">${:.2f}</div>
                        </div>
                    </div>
                    """.format(
                        spy_prices['High'].max(),
                        spy_prices['Low'].min(),
                        spy_prices['Volume'].mean(),
                        spy_dividends['Dividends'].sum() if not spy_dividends.empty else 0
                    ), unsafe_allow_html=True)
             
            with col2:
                st.markdown("<h2>TOTAL MARKET ETF (VTI)</h2>", unsafe_allow_html=True)
                if not vti_prices.empty:
                    latest_price = vti_prices['Close'].iloc[-1]
                    price_change = vti_prices['Close'].iloc[-1] - vti_prices['Close'].iloc[0]
                    pct_change = (price_change / vti_prices['Close'].iloc[0] * 100) if vti_prices['Close'].iloc[0] != 0 else 0
                    
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Latest Price</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${latest_price:.2f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">{pct_change:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div class="terminal-card">
                        <div class="data-grid">
                            <div class="data-label">52-WEEK HIGH:</div>
                            <div class="data-value">${:.2f}</div>
                            <div class="data-label">52-WEEK LOW:</div>
                            <div class="data-value">${:.2f}</div>
                            <div class="data-label">AVG VOLUME:</div>
                            <div class="data-value">{:,.0f}</div>
                            <div class="data-label">TOTAL DIVIDENDS:</div>
                            <div class="data-value">${:.2f}</div>
                        </div>
                    </div>
                    """.format(
                        vti_prices['High'].max(),
                        vti_prices['Low'].min(),
                        vti_prices['Volume'].mean(),
                        vti_dividends['Dividends'].sum() if not vti_dividends.empty else 0
                    ), unsafe_allow_html=True)
        
    elif st.session_state.selected_tab == "PRICE ANALYSIS":
        with st.container():
            st.markdown("<h1>PRICE ANALYSIS</h1>", unsafe_allow_html=True)
            st.markdown(price_analysis_explanation(), unsafe_allow_html=True)
            
            # Theme toggle for charts
            st.markdown("<h2>CHART THEME</h2>", unsafe_allow_html=True)
            theme_col1, theme_col2, theme_col3 = st.columns([1, 2, 1])
            with theme_col2:
                use_dark_theme = st.toggle(
                    "Dark Theme Charts",
                    value=True,
                    help="Toggle between dark (Bloomberg-style) and light theme for charts",
                    key="price_chart_theme_toggle"
                )
                
                if use_dark_theme:
                    st.markdown("""
                    <div style="background-color: #0a0a0a; border: 1px solid #00ff00; padding: 0.5rem; color: #00ff00; text-align: center; margin-bottom: 1rem;">
                        <strong>DARK THEME ACTIVE</strong> - Bloomberg Terminal Style
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background-color: #f8f8f8; border: 1px solid #0066cc; padding: 0.5rem; color: #0066cc; text-align: center; margin-bottom: 1rem;">
                        <strong>LIGHT THEME ACTIVE</strong> - Professional Report Style
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<h2>DATE RANGE</h2>", unsafe_allow_html=True)
            st.markdown(date_range_explanation(), unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                price_start_date = st.date_input("START DATE", value=start_date, key="price_start")
            with col2:
                price_end_date = st.date_input("END DATE", value=end_date, key="price_end")
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                price_apply_btn = st.button("APPLY FILTER", use_container_width=True, key="price_apply")
            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 1rem 0;'></div>", unsafe_allow_html=True)
            
            # Fetch data from FMP API for the specified date range
            with st.spinner("Loading price data..."):
                spy_price_data, _, _ = fmp_provider.get_combined_data('SPY', price_start_date.strftime('%Y-%m-%d'), price_end_date.strftime('%Y-%m-%d'))
                vti_price_data, _, _ = fmp_provider.get_combined_data('VTI', price_start_date.strftime('%Y-%m-%d'), price_end_date.strftime('%Y-%m-%d'))
            
            spy_price_filtered = spy_price_data
            vti_price_filtered = vti_price_data
            
            # SPY chart with dark gray background
            st.markdown("""
            <div style="background-color: #404040; color: #ffffff; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h2 style="margin: 0; color: #ffffff; font-weight: 600;">S&P 500 ETF (SPY) PRICE CHART</h2>
            </div>
            """, unsafe_allow_html=True)
            if not spy_price_filtered.empty:
                fig = plot_candlestick(spy_price_filtered, 'S&P 500 ETF', 'SPY', use_dark_theme)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("NO SPY DATA FOR SELECTED RANGE")
            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 1rem 0;'></div>", unsafe_allow_html=True)
            
            # VTI chart with dark gray background
            st.markdown("""
            <div style="background-color: #404040; color: #ffffff; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h2 style="margin: 0; color: #ffffff; font-weight: 600;">TOTAL MARKET ETF (VTI) PRICE CHART</h2>
            </div>
            """, unsafe_allow_html=True)
            if not vti_price_filtered.empty:
                fig = plot_candlestick(vti_price_filtered, 'Total Market ETF', 'VTI', use_dark_theme)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("NO VTI DATA FOR SELECTED RANGE")
        
    elif st.session_state.selected_tab == "DIVIDEND ANALYSIS":
        with st.container():
            st.markdown("<h1>DIVIDEND ANALYSIS</h1>", unsafe_allow_html=True)
            st.markdown(dividend_analysis_explanation(), unsafe_allow_html=True)
            
            st.markdown("<h2>DATE RANGE</h2>", unsafe_allow_html=True)
            st.markdown(date_range_explanation(), unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                div_start_date = st.date_input("START DATE", value=start_date, key="div_start")
            with col2:
                div_end_date = st.date_input("END DATE", value=end_date, key="div_end")
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                div_apply_btn = st.button("APPLY FILTER", use_container_width=True, key="div_apply")
            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 1rem 0;'></div>", unsafe_allow_html=True)
            
            # Fetch dividend data from FMP API for the specified date range
            with st.spinner("Loading dividend data..."):
                _, spy_div_data, _ = fmp_provider.get_combined_data('SPY', div_start_date.strftime('%Y-%m-%d'), div_end_date.strftime('%Y-%m-%d'))
                _, vti_div_data, _ = fmp_provider.get_combined_data('VTI', div_start_date.strftime('%Y-%m-%d'), div_end_date.strftime('%Y-%m-%d'))
            
            spy_div_filtered = spy_div_data
            vti_div_filtered = vti_div_data
            
            # SPY dividends with dark gray background
            st.markdown("""
            <div style="background-color: #404040; color: #ffffff; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h2 style="margin: 0; color: #ffffff; font-weight: 600;">S&P 500 ETF DIVIDENDS (SPY)</h2>
            </div>
            """, unsafe_allow_html=True)
            if not spy_div_filtered.empty:
                fig = plot_dividend_bars_mpl(spy_div_filtered, 'S&P 500 ETF Dividends', 'SPY')
                if fig is not None:
                    st.pyplot(fig, clear_figure=True)
            else:
                st.info("NO SPY DIVIDEND DATA FOR SELECTED RANGE")
            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 1rem 0;'></div>", unsafe_allow_html=True)
            
            # VTI dividends with dark gray background
            st.markdown("""
            <div style="background-color: #404040; color: #ffffff; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <h2 style="margin: 0; color: #ffffff; font-weight: 600;">TOTAL MARKET ETF DIVIDENDS (VTI)</h2>
            </div>
            """, unsafe_allow_html=True)
            if not vti_div_filtered.empty:
                fig = plot_dividend_bars_mpl(vti_div_filtered, 'Total Market ETF Dividends', 'VTI')
                if fig is not None:
                    st.pyplot(fig, clear_figure=True)
            else:
                st.info("NO VTI DIVIDEND DATA FOR SELECTED RANGE")
    
    elif st.session_state.selected_tab == "KELLY CRITERION":
        with st.container():
            st.markdown("<h1>KELLY CRITERION</h1>", unsafe_allow_html=True)
            st.markdown(kelly_criterion_explanation(), unsafe_allow_html=True)
            
            # Coming soon message with professional styling
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 1rem 0;'></div>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style="text-align: center; padding: 3rem 1rem;">
                <h2 style="color: var(--accent-orange); font-size: 2rem; margin-bottom: 1rem;">COMING SOON</h2>
                <p style="color: var(--text-primary); font-size: 1.1rem; margin-bottom: 2rem;">
                    KELLY CRITERION POSITION SIZING CALCULATOR
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                st.markdown("""
                <div class="terminal-card">
                    <h3 style="color: var(--accent-orange); margin-bottom: 1rem;">WHAT IS KELLY CRITERION?</h3>
                    <div style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;">
                        The Kelly Criterion is a mathematical formula used to determine the optimal size of a series of bets or investments. 
                        Developed by John L. Kelly Jr. in 1956, it maximizes the expected logarithm of wealth, leading to the highest 
                        geometric growth rate in the long run.
                    </div>
                    <div style="margin-top: 1rem;">
                        <div class="data-label">FORMULA:</div>
                        <div style="color: var(--accent-amber); font-family: 'IBM Plex Mono'; font-size: 1rem; margin-top: 0.5rem;">
                            f* = (p × b - q) / b
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
                            WHERE:<br/>
                            f* = FRACTION OF CAPITAL TO BET<br/>
                            p = PROBABILITY OF WINNING<br/>
                            q = PROBABILITY OF LOSING (1-p)<br/>
                            b = NET ODDS RECEIVED ON THE BET
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown("""
                <div class="terminal-card">
                    <h3 style="color: var(--accent-orange); margin-bottom: 1rem;">APPLICATION TO MARGIN TRADING</h3>
                    <div style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;">
                        For margin trading with ETFs, we will adapt the Kelly Criterion to account for:
                    </div>
                    <div style="margin-top: 1rem;">
                        <ul style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.8;">
                            <li>EXPECTED RETURNS BASED ON HISTORICAL DATA</li>
                            <li>VOLATILITY AND DOWNSIDE RISK</li>
                            <li>MARGIN INTEREST COSTS</li>
                            <li>DIVIDEND INCOME STREAMS</li>
                            <li>LEVERAGE CONSTRAINTS</li>
                            <li>RISK OF MARGIN CALLS</li>
                        </ul>
                    </div>
                    <div style="margin-top: 1rem; padding: 0.5rem; background-color: var(--bg-tertiary); border: 1px solid var(--warning-yellow);">
                        <div style="color: var(--warning-yellow); font-size: 0.85rem; text-transform: uppercase;">
                            Risk Warning: Kelly Criterion assumes accurate probability estimates
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 2rem 0;'></div>", unsafe_allow_html=True)
            
            # Features preview
            st.markdown("<h2>PLANNED FEATURES</h2>", unsafe_allow_html=True)
            
            features_col1, features_col2, features_col3 = st.columns(3)
            
            with features_col1:
                st.markdown("""
                <div class="terminal-card">
                    <h3 style="color: var(--info-blue); font-size: 1rem;">BASIC KELLY CALCULATOR</h3>
                    <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
                        - WIN/LOSS PROBABILITY INPUTS<br/>
                        - EXPECTED RETURN CALCULATOR<br/>
                        - OPTIMAL POSITION SIZE<br/>
                        - RISK-ADJUSTED RECOMMENDATIONS
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with features_col2:
                st.markdown("""
                <div class="terminal-card">
                    <h3 style="color: var(--info-blue); font-size: 1rem;">ADVANCED ANALYSIS</h3>
                    <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
                        - FRACTIONAL KELLY OPTIONS<br/>
                        - MULTI-ASSET PORTFOLIO SIZING<br/>
                        - DYNAMIC REBALANCING SIGNALS<br/>
                        - MONTE CARLO VALIDATION
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with features_col3:
                st.markdown("""
                <div class="terminal-card">
                    <h3 style="color: var(--info-blue); font-size: 1rem;">MARGIN INTEGRATION</h3>
                    <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
                        - LEVERAGE-ADJUSTED KELLY<br/>
                        - MARGIN COST OPTIMIZATION<br/>
                        - DRAWDOWN PROTECTION<br/>
                        - HISTORICAL BACKTEST VALIDATION
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='border-bottom: 1px solid var(--border-color); margin: 2rem 0;'></div>", unsafe_allow_html=True)
            
            # Implementation timeline
            st.markdown("""
            <div class="terminal-card" style="border-color: var(--accent-orange);">
                <h3 style="color: var(--accent-orange); margin-bottom: 1rem;">IMPLEMENTATION TIMELINE</h3>
                <div class="data-grid">
                    <div class="data-label">PHASE 1 - BASIC CALCULATOR:</div>
                    <div class="data-value">Q1 2025</div>
                    <div class="data-label">PHASE 2 - ADVANCED FEATURES:</div>
                    <div class="data-value">Q2 2025</div>
                    <div class="data-label">PHASE 3 - FULL INTEGRATION:</div>
                    <div class="data-value">Q3 2025</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown(app_footer(), unsafe_allow_html=True)
    
else:
    # Error message
    st.error("DATA LOAD FAILURE. CHECK DATA PATH AND FILE INTEGRITY.")
    st.markdown(f"DATA PATH: {data_dir}")
    
    st.markdown("<h2>REQUIRED FILES</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class="terminal-card">
        <div style="color: var(--text-secondary);">
            - SPY.csv<br/>
            - SPY Dividends.csv<br/>
            - VTI.csv<br/>
            - VTI Dividends.csv<br/><br/>
            REQUIRED COLUMNS: Date, Open, High, Low, Close, Volume<br/>
            DIVIDEND COLUMNS: Date, Dividends
        </div>
    </div>
    """, unsafe_allow_html=True) 