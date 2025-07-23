import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time

# Set page configuration
st.set_page_config(
    page_title="ADE Financial Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Bloomberg Terminal-style CSS
st.markdown("""
<style>
    /* Hide Streamlit elements */
    .stDeployButton {display: none;}
    .stDecoration {display: none;}
    .stMainMenu {display: none;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main background - Strong Solid Blue */
    .stApp {
        background: #2d3e91;
        background-attachment: fixed;
        color: #ffffff;
        font-family: 'Courier New', monospace;
        min-height: 100vh;
    }
    
    /* Strong blue pattern overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 20%, rgba(45, 62, 145, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(45, 62, 145, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 40% 70%, rgba(45, 62, 145, 0.2) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }
    
    /* Container styling - Enhanced */
    .main .block-container {
        padding: 1rem 2rem;
        max-width: 100%;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Terminal header - Strong Blue */
    .terminal-header {
        background: #1e2a73;
        color: #ffffff;
        padding: 20px 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 
            0 8px 25px rgba(30, 42, 115, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.15);
    }
    
    .terminal-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
        font-family: 'Arial', sans-serif;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .terminal-subtitle {
        font-size: 1.2rem;
        text-align: center;
        margin: 5px 0 0 0;
        opacity: 0.9;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Control panel - Enhanced Strong Blue */
    .control-panel {
        background: rgba(30, 42, 115, 0.6);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 25px;
        backdrop-filter: blur(15px);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    
    /* Data cards - Strong Blue glass */
    .data-card {
        background: rgba(30, 42, 115, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 18px;
        margin: 12px 0;
        backdrop-filter: blur(10px);
        box-shadow: 
            0 4px 20px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .data-card h3 {
        color: #ffffff;
        margin: 0 0 10px 0;
        font-size: 1.1rem;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    .data-value {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
    }
    
    /* Selectbox styling - Heavy Blue with Perfect Readability */
    .stSelectbox > div > div {
        background: rgba(30, 42, 115, 0.9) !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 10px;
        color: #ffffff !important;
        backdrop-filter: blur(15px);
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stSelectbox > div > div > div {
        background: rgba(30, 42, 115, 0.9) !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* AGGRESSIVE DROPDOWN STYLING - Force Heavy Blue */
    
    /* All dropdown containers */
    .stSelectbox [data-baseweb="select"] {
        background: rgba(20, 30, 85, 0.95) !important;
    }
    
    /* Dropdown menu popup */
    .stSelectbox [data-baseweb="popover"] {
        background: rgba(20, 30, 85, 0.98) !important;
        border: 2px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 10px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* Dropdown list container */
    .stSelectbox [role="listbox"] {
        background: rgba(20, 30, 85, 0.98) !important;
        border: none !important;
    }
    
    /* Individual dropdown options - FORCE STYLING */
    .stSelectbox [role="option"] {
        background: rgba(20, 30, 85, 0.98) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        padding: 10px 15px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Hover state for options */
    .stSelectbox [role="option"]:hover {
        background: rgba(46, 75, 198, 0.9) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Selected option highlighting */
    .stSelectbox [aria-selected="true"] {
        background: rgba(46, 75, 198, 0.8) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Dropdown arrow area */
    .stSelectbox [data-baseweb="select"] > div:last-child {
        background: rgba(20, 30, 85, 0.95) !important;
    }
    
    /* Universal dropdown text forcing */
    .stSelectbox * {
        color: #ffffff !important;
    }
    
    /* Extra aggressive - target all possible dropdown elements */
    div[data-baseweb="popover"] div {
        background: rgba(20, 30, 85, 0.98) !important;
        color: #ffffff !important;
    }
    
    /* Menu items specifically */
    li[role="option"] {
        background: rgba(20, 30, 85, 0.98) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    li[role="option"]:hover {
        background: rgba(46, 75, 198, 0.9) !important;
        color: #ffffff !important;
    }
    
    /* Selectbox arrow and icons */
    .stSelectbox svg {
        fill: #ffffff !important;
    }
    
    /* Metric styling - Enhanced Strong Blue */
    .metric-container {
        background: rgba(30, 42, 115, 0.4) !important;
        border: 2px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 15px;
        padding: 22px;
        text-align: center;
        backdrop-filter: blur(15px);
        box-shadow: 
            0 8px 30px rgba(0, 0, 0, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-3px);
        box-shadow: 
            0 12px 35px rgba(30, 42, 115, 0.5),
            inset 0 2px 0 rgba(255, 255, 255, 0.25);
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        background: rgba(30, 42, 115, 0.5) !important;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #ffffff !important;
        font-family: 'Courier New', monospace;
        text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.5);
    }
    
    .metric-label {
        color: #ffffff !important;
        font-size: 1rem;
        margin-top: 8px;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        opacity: 1;
        letter-spacing: 0.5px;
    }
    
    /* Table styling - Enhanced Strong Blue */
    .stDataFrame {
        background: rgba(30, 42, 115, 0.3) !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        overflow: hidden;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    }
    
    /* Table text white */
    .stDataFrame table, .stDataFrame th, .stDataFrame td {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    .stDataFrame th {
        background: rgba(30, 42, 115, 0.5) !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
    }
    
    /* Loading spinner */
    .stSpinner {
        color: #ffffff !important;
    }
    
    /* Additional text visibility enhancements */
    .stSelectbox label, .stSelectbox span {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
        font-size: 1rem !important;
    }
    
    /* All input field styling - Heavy Blue */
    .stTextInput > div > div > input {
        background: rgba(20, 30, 85, 0.9) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px;
        font-weight: 600;
    }
    
    .stNumberInput > div > div > input {
        background: rgba(20, 30, 85, 0.9) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Slider styling */
    .stSlider > div > div > div > div {
        background: rgba(20, 30, 85, 0.9) !important;
    }
    
    /* Time display - Strong Blue */
    .time-display {
        color: #ffffff;
        font-family: 'Courier New', monospace;
        font-size: 1.1rem;
        text-align: right;
        margin-bottom: 10px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
        background: rgba(30, 42, 115, 0.15);
        padding: 8px 15px;
        border-radius: 8px;
        border-left: 4px solid #ffffff;
    }
    
    /* All text white with enhanced visibility */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        font-weight: bold !important;
    }
    
    /* Streamlit elements - Enhanced white text */
    .stMarkdown {
        color: #ffffff !important;
    }
    
    .stMarkdown p, .stMarkdown div, .stMarkdown span {
        color: #ffffff !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
        font-weight: 500;
    }
    
    /* All general text white */
    * {
        color: #ffffff;
    }
    
    /* Control panel text enhancement */
    .control-panel * {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Control panel section titles - Heavy Blue Background */
    .control-panel h4, .control-panel h5, .control-panel h6 {
        background: rgba(20, 30, 85, 0.7) !important;
        padding: 8px 12px;
        border-radius: 8px;
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
        border-left: 3px solid #ffffff;
        margin-bottom: 8px;
    }
    
    /* Labels and spans */
    label, span, div {
        color: #ffffff !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Enhanced section headers - Strong Blue */
    .stMarkdown h3 {
        background: rgba(30, 42, 115, 0.5) !important;
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 5px solid #ffffff;
        margin: 25px 0 20px 0;
        border: 2px solid rgba(255, 255, 255, 0.3);
        color: #ffffff !important;
        font-weight: bold !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Plotly Chart - Keep Normal White Background */
    .js-plotly-plot, .plotly, .plotly-graph-div {
        background: white !important;
        background-color: white !important;
    }
    
    .plot-container, .svg-container {
        background: white !important;
        background-color: white !important;
    }
    
    /* Ensure Plotly chart area stays white with professional styling */
    .stPlotlyChart > div {
        background: white !important;
        background-color: white !important;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        border: 2px solid rgba(46, 75, 198, 0.2);
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Enhanced chart visibility */
    .js-plotly-plot .plotly .main-svg {
        border-radius: 10px;
    }
    
    /* Plotly modebar styling */
    .modebar {
        background: white !important;
    }
    
    /* Final visibility enhancements */
    .stColumns > div {
        color: #ffffff !important;
    }
    
    .stColumn > div {
        color: #ffffff !important;
    }
    
    /* Ensure all Streamlit elements are white */
    .stText, .stTextInput, .stNumber, .element-container {
        color: #ffffff !important;
    }
    
    /* Column headers and content */
    .stColumn h4, .stColumn h5, .stColumn p, .stColumn span {
        color: #ffffff !important;
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.4);
    }
    
    /* Strong emphasis on section titles */
    strong, b {
        color: #ffffff !important;
        font-weight: 800 !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def generate_dummy_data():
    """Generate realistic dummy financial data for ETFs from 2010-2025"""
    
    etfs = {
        'SPY': {'name': 'SPDR S&P 500 ETF', 'growth_rate': 1.08, 'volatility': 0.15, 'ticker': 'SPY'},
        'QQQ': {'name': 'Invesco QQQ Trust', 'growth_rate': 1.12, 'volatility': 0.20, 'ticker': 'QQQ'},
        'VTI': {'name': 'Vanguard Total Stock Market', 'growth_rate': 1.09, 'volatility': 0.16, 'ticker': 'VTI'},
        'IWM': {'name': 'iShares Russell 2000', 'growth_rate': 1.07, 'volatility': 0.22, 'ticker': 'IWM'},
        'EFA': {'name': 'iShares MSCI EAFE', 'growth_rate': 1.05, 'volatility': 0.18, 'ticker': 'EFA'},
        'VNQ': {'name': 'Vanguard Real Estate', 'growth_rate': 1.06, 'volatility': 0.25, 'ticker': 'VNQ'},
        'GLD': {'name': 'SPDR Gold Shares', 'growth_rate': 1.03, 'volatility': 0.20, 'ticker': 'GLD'}
    }
    
    years = list(range(2010, 2026))  # 2010-2025
    all_data = {}
    
    for etf_symbol, etf_info in etfs.items():
        np.random.seed(hash(etf_symbol) % 2**32)  # Consistent random data per ETF
        
        # Starting values (in millions)
        base_assets = np.random.uniform(10000, 50000)
        base_equity_ratio = np.random.uniform(0.45, 0.65)  # 45-65% equity
        
        assets = []
        equity = []
        liabilities = []
        
        for i, year in enumerate(years):
            # Growth with some randomness
            growth_factor = etf_info['growth_rate'] ** i
            random_factor = np.random.normal(1.0, etf_info['volatility'] * 0.3)
            
            # Calculate assets with growth and volatility
            current_assets = base_assets * growth_factor * random_factor
            
            # Calculate equity ratio (slightly changing over time)
            equity_drift = np.random.normal(0, 0.02)  # Small random walk
            current_equity_ratio = np.clip(base_equity_ratio + equity_drift * i * 0.1, 0.3, 0.8)
            
            # Calculate components
            current_equity = current_assets * current_equity_ratio
            current_liabilities = current_assets - current_equity
            
            assets.append(int(current_assets))
            equity.append(int(current_equity))
            liabilities.append(int(current_liabilities))
        
        all_data[etf_symbol] = {
            'name': etf_info['name'],
            'ticker': etf_info['ticker'],
            'years': years,
            'assets': assets,
            'equity': equity,
            'liabilities': liabilities
        }
    
    return all_data

def create_professional_chart(data, etf_symbol, start_year, end_year):
    """Create a professional, clean chart with harmonious blue color scheme"""
    
    # Filter data based on selected years
    etf_data = data[etf_symbol]
    years = etf_data['years']
    
    start_idx = years.index(start_year)
    end_idx = years.index(end_year) + 1
    
    filtered_years = years[start_idx:end_idx]
    filtered_assets = etf_data['assets'][start_idx:end_idx]
    filtered_equity = etf_data['equity'][start_idx:end_idx]
    filtered_liabilities = etf_data['liabilities'][start_idx:end_idx]
    
    # Create the main chart
    fig = go.Figure()
    
    # Conditional text format based on number of years
    num_years = len(filtered_years)
    if num_years <= 10:
        # Few years: Use normal two-line format
        assets_text = [f'A<br>${x:,.0f}M' for x in filtered_assets]
        equity_text = [f'E<br>${x:,.0f}M' for x in filtered_equity]
        debt_text = [f'D<br>${x:,.0f}M' for x in filtered_liabilities]
    else:
        # Many years: Use compact single-line format
        assets_text = [f'A=${x:,.0f}M' for x in filtered_assets]
        equity_text = [f'E=${x:,.0f}M' for x in filtered_equity]
        debt_text = [f'D=${x:,.0f}M' for x in filtered_liabilities]
    
    # Add Assets bars with professional blue palette
    fig.add_trace(go.Bar(
        name='Assets (A)',
        x=filtered_years,
        y=filtered_assets,
        marker_color='#2E4BC6',  # Professional deep blue
        opacity=0.95,
        text=assets_text,
        textposition='inside',
        textfont=dict(color='white', size=14, family='Arial'),
        hovertemplate='<b>Assets</b><br>Year: %{x}<br>Amount: $%{y:,.0f}M<extra></extra>',
        offsetgroup=1,
        marker=dict(
            line=dict(color='white', width=1),
            pattern=dict(shape='')
        )
    ))
    
    # Add Equity bars with sophisticated navy
    fig.add_trace(go.Bar(
        name='Equity (E)',
        x=filtered_years,
        y=filtered_equity,
        marker_color='#1B2951',  # Sophisticated navy blue
        opacity=0.95,
        text=equity_text,
        textposition='inside',
        textfont=dict(color='white', size=14, family='Arial'),
        hovertemplate='<b>Equity</b><br>Year: %{x}<br>Amount: $%{y:,.0f}M<extra></extra>',
        offsetgroup=2,
        marker=dict(
            line=dict(color='white', width=1),
            pattern=dict(shape='')
        )
    ))
    
    # Add Debt bars with complementary steel blue
    fig.add_trace(go.Bar(
        name='Debt (D)',
        x=filtered_years,
        y=filtered_liabilities,
        marker_color='#4A90C2',  # Complementary steel blue
        opacity=0.95,
        text=debt_text,
        textposition='inside',
        textfont=dict(color='white', size=14, family='Arial'),
        hovertemplate='<b>Debt</b><br>Year: %{x}<br>Amount: $%{y:,.0f}M<extra></extra>',
        base=filtered_equity,  # Stack on top of equity
        offsetgroup=2,
        marker=dict(
            line=dict(color='white', width=1),
            pattern=dict(shape='')
        )
    ))
    
    # Update layout with professional, clean theme
    fig.update_layout(
        title=dict(
            text=f"<b>{etf_symbol} - {etf_data['name']}</b><br><span style='font-size:18px; color:#2E4BC6;'>Assets vs Debt + Equity | A = D + E</span>",
            x=0.5,
            font=dict(size=28, color='#1B2951', family='Arial Black'),
            pad=dict(t=25, b=25)
        ),
        height=750,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333', family='Arial'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='#2E4BC6',
            borderwidth=2,
            font=dict(color='#1B2951', size=14, family='Arial Black'),
            itemsizing='constant',
            itemwidth=30
        ),
        hovermode='x unified',
        barmode='group',
        bargap=0.2,
        bargroupgap=0.15,
        xaxis=dict(
            title=dict(text="<b>Year</b>", font=dict(color='#1B2951', size=16, family='Arial Black')),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(200,200,200,0.5)',
            showline=True,
            linewidth=2,
            linecolor='#2E4BC6',
            tickfont=dict(color='#333333', size=13, family='Arial'),
            tickangle=0,
            tickmode='linear',
            tick0=filtered_years[0],
            dtick=1
        ),
        yaxis=dict(
            title=dict(text="<b>Amount (Millions USD)</b>", font=dict(color='#1B2951', size=16, family='Arial Black')),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(200,200,200,0.5)',
            showline=True,
            linewidth=2,
            linecolor='#2E4BC6',
            tickfont=dict(color='#333333', size=13, family='Arial'),
            tickformat='$,.0f',
            zeroline=True,
            zerolinecolor='rgba(150,150,150,0.8)',
            zerolinewidth=1
        ),
        margin=dict(l=90, r=90, t=120, b=100),
        annotations=[
            dict(
                text="<b>Left: Assets (A)</b> | <b>Right: Stacked Debt (D) + Equity (E)</b><br>Fundamental Equation: <b>A = D + E</b>",
                xref="paper", yref="paper",
                x=0.5, y=-0.12,
                xanchor='center', yanchor='top',
                font=dict(size=14, color='#1B2951', family='Arial'),
                showarrow=False
            )
        ],
        showlegend=True
    )
    
    return fig

def create_metrics_dashboard(data, etf_symbol, start_year, end_year):
    """Create metrics dashboard"""
    etf_data = data[etf_symbol]
    years = etf_data['years']
    
    start_idx = years.index(start_year)
    end_idx = years.index(end_year) + 1
    
    avg_assets = np.mean(etf_data['assets'][start_idx:end_idx])
    avg_equity = np.mean(etf_data['equity'][start_idx:end_idx])
    avg_liabilities = np.mean(etf_data['liabilities'][start_idx:end_idx])
    
    equity_ratio = (avg_equity / avg_assets) * 100
    debt_ratio = (avg_liabilities / avg_assets) * 100
    
    # Calculate growth rates
    asset_growth = ((etf_data['assets'][end_idx-1] / etf_data['assets'][start_idx]) ** (1/(end_year-start_year)) - 1) * 100
    equity_growth = ((etf_data['equity'][end_idx-1] / etf_data['equity'][start_idx]) ** (1/(end_year-start_year)) - 1) * 100
    
    return {
        'avg_assets': avg_assets,
        'avg_equity': avg_equity,
        'avg_liabilities': avg_liabilities,
        'equity_ratio': equity_ratio,
        'debt_ratio': debt_ratio,
        'asset_growth': asset_growth,
        'equity_growth': equity_growth
    }

def main():
    # Current time display
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown(f'<div class="time-display">LIVE DATA | {current_time}</div>', unsafe_allow_html=True)
    
    # Terminal header
    st.markdown("""
    <div class="terminal-header">
        <h1 class="terminal-title">ADE FINANCIAL TERMINAL</h1>
        <p class="terminal-subtitle">Assets • Debt • Equity Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)
    

    
    # Load data
    with st.spinner("🔄 Loading market data..."):
        data = generate_dummy_data()
    
    # Control panel
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    
    # Create control layout
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown("**🎯 SECURITY SELECTION**")
        etf_options = {symbol: f"{symbol} - {info['name']}" for symbol, info in data.items()}
        selected_etf = st.selectbox(
            "Select ETF/Security:",
            options=list(etf_options.keys()),
            format_func=lambda x: etf_options[x],
            index=0,
            key="etf_select"
        )
    
    with col2:
        st.markdown("**📅 START YEAR**")
        start_year = st.selectbox(
            "From:",
            options=list(range(2010, 2026)),
            index=0,
            key="start_year"
        )
    
    with col3:
        st.markdown("**📅 END YEAR**")
        end_year = st.selectbox(
            "To:",
            options=list(range(start_year, 2026)),
            index=len(list(range(start_year, 2026))) - 1,
            key="end_year"
        )
    
    with col4:
        st.markdown("**⏱️ PERIOD**")
        years_selected = end_year - start_year + 1
        st.markdown(f'<div class="data-value">{years_selected} YRS</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate metrics
    metrics = create_metrics_dashboard(data, selected_etf, start_year, end_year)
    
    # Key metrics dashboard
    st.markdown("### 📊 KEY PERFORMANCE INDICATORS")
    
    met_col1, met_col2, met_col3, met_col4 = st.columns(4)
    
    with met_col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value"><b>${metrics['avg_assets']:,.0f}M</b></div>
            <div class="metric-label"><b>AVG ASSETS</b></div>
        </div>
        """, unsafe_allow_html=True)
    
    with met_col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value"><b>{metrics['equity_ratio']:.1f}%</b></div>
            <div class="metric-label"><b>EQUITY RATIO</b></div>
        </div>
        """, unsafe_allow_html=True)
    
    with met_col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value"><b>{metrics['asset_growth']:+.1f}%</b></div>
            <div class="metric-label"><b>ASSET GROWTH</b></div>
        </div>
        """, unsafe_allow_html=True)
    
    with met_col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value"><b>{metrics['equity_growth']:+.1f}%</b></div>
            <div class="metric-label"><b>EQUITY GROWTH</b></div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main visualization
    st.markdown("### 📈 FINANCIAL ANALYSIS DASHBOARD")
    
    with st.spinner("🔄 Generating advanced analytics..."):
        fig = create_professional_chart(data, selected_etf, start_year, end_year)
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("### 📋 DETAILED FINANCIAL DATA")
    
    # Create comprehensive dataframe
    etf_info = data[selected_etf]
    start_idx = etf_info['years'].index(start_year)
    end_idx = etf_info['years'].index(end_year) + 1
    
    df = pd.DataFrame({
        'YEAR': etf_info['years'][start_idx:end_idx],
        'ASSETS (A)': [f"${x:,}M" for x in etf_info['assets'][start_idx:end_idx]],
        'EQUITY (E)': [f"${x:,}M" for x in etf_info['equity'][start_idx:end_idx]],
        'LIABILITIES (D)': [f"${x:,}M" for x in etf_info['liabilities'][start_idx:end_idx]],
        'E/A RATIO': [f"{(e/a)*100:.1f}%" for e, a in zip(etf_info['equity'][start_idx:end_idx], etf_info['assets'][start_idx:end_idx])],
        'D/A RATIO': [f"{(d/a)*100:.1f}%" for d, a in zip(etf_info['liabilities'][start_idx:end_idx], etf_info['assets'][start_idx:end_idx])],
        'LEVERAGE': [f"{a/e:.2f}x" for e, a in zip(etf_info['equity'][start_idx:end_idx], etf_info['assets'][start_idx:end_idx])],
        'YoY GROWTH': ['N/A'] + [f"{((etf_info['assets'][i]/etf_info['assets'][i-1])-1)*100:+.1f}%" for i in range(start_idx+1, end_idx)]
    })
    
    st.dataframe(df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <b>ADE FINANCIAL TERMINAL</b> | Professional Financial Analysis Platform<br>
        <i>⚠️ Simulated data for demonstration purposes | Real-time data integration available</i>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()



