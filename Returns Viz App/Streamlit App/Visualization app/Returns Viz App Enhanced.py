import streamlit as st
import pandas as pd
import numpy as np
import os
import warnings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Import our new modules
from fmp_api import FMPDataProvider
from performance_metrics import PerformanceMetrics, calculate_performance_metrics

warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Pearson Creek Capital - ETF CAGR Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional financial dashboard
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom color scheme */
    :root {
        --primary-blue: #1f4e79;
        --secondary-blue: #2e5c8a;
        --accent-gold: #d4af37;
        --light-gray: #f8f9fa;
        --medium-gray: #6c757d;
        --dark-gray: #343a40;
        --success-green: #28a745;
        --danger-red: #dc3545;
        --warning-orange: #fd7e14;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95%;
    }
    
    /* Company header */
    .company-header {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .company-name {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: 1px;
    }
    
    .company-tagline {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 300;
    }
    
    /* Control panel */
    .control-panel {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Performance metrics cards */
    .metric-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .metric-title {
        font-size: 0.9rem;
        color: var(--medium-gray);
        margin-bottom: 0.3rem;
    }
    
    .metric-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--primary-blue);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border: 2px solid var(--primary-blue);
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-blue);
        color: white;
    }
    
    /* Matrix container */
    .matrix-container {
        background: white;
        border-radius: 10px;
        padding: 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    /* Stats container */
    .stats-container {
        display: flex;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        flex: 1;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-blue);
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: var(--medium-gray);
        font-weight: 500;
    }
    
    /* Instructions box */
    .instructions {
        background: #f0f8ff;
        border: 1px solid #b8daff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 2rem 0;
        color: #004085;
    }
    
    .instructions h4 {
        color: #004085;
        margin-bottom: 1rem;
    }
    
    .instructions ul {
        margin: 0;
        padding-left: 1.5rem;
    }
    
    .instructions li {
        margin-bottom: 0.5rem;
    }
    
    /* Custom selectbox styling */
    .stSelectbox > div > div {
        background-color: white;
        border: 2px solid #e9ecef;
        border-radius: 8px;
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

def create_cagr_matrix(annual_returns_series, start_year=None, end_year=None):
    """
    Creates a matrix of Compound Annual Growth Rates (CAGR) between different year ranges.
    """
    # Convert percentages back to decimals for calculations
    returns_decimal = annual_returns_series / 100
    
    # Get year range
    if start_year is None:
        start_year = returns_decimal.index.min()
    if end_year is None:
        end_year = returns_decimal.index.max()
    
    # Filter data to specified year range
    returns_filtered = returns_decimal.loc[start_year:end_year]
    years = returns_filtered.index.tolist()
    
    # Initialize matrix
    matrix = pd.DataFrame(index=years, columns=years, dtype=float)
    
    # Fill the matrix
    for start_yr in years:
        for end_yr in years:
            if end_yr >= start_yr:  # Only calculate for valid date ranges
                # Get returns for the period
                period_returns = returns_filtered.loc[start_yr:end_yr]
                
                # Calculate number of years
                num_years = len(period_returns)
                
                if num_years == 1:
                    # Single year return
                    cagr = period_returns.loc[start_yr] * 100
                else:
                    # Multi-year CAGR
                    cumulative_return = (1 + period_returns).prod()
                    cagr = (cumulative_return ** (1/num_years) - 1) * 100
                
                matrix.loc[end_yr, start_yr] = cagr
    
    return matrix

@st.cache_data
def load_etf_data():
    """Load and process ETF data to calculate annual returns"""
    
    try:
        # Get the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, "..", "Historical Data")
        
        # Check if data directory exists
        if not os.path.exists(data_dir):
            return None, None
        
        # Import the CSV files with absolute paths
        dia_data = pd.read_csv(os.path.join(data_dir, "DIA.csv"))
        spy_data = pd.read_csv(os.path.join(data_dir, "SPY.csv"))
        qqq_data = pd.read_csv(os.path.join(data_dir, "QQQ.csv"))
        vti_data = pd.read_csv(os.path.join(data_dir, "VTI.csv"))
        
        # Convert Date columns to datetime and clean up dataframes
        dia_data['Date'] = pd.to_datetime(dia_data['Date'])
        spy_data['Date'] = pd.to_datetime(spy_data['Date'])
        qqq_data['Date'] = pd.to_datetime(qqq_data['Date'])
        vti_data['Date'] = pd.to_datetime(vti_data['Date'])
        
        # Keep only Date and Adj Close columns, rename Adj Close to ETF name
        dia_data = dia_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'DIA'})
        spy_data = spy_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'SPY'})
        qqq_data = qqq_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'QQQ'})
        vti_data = vti_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'VTI'})
        
        # Convert prices to returns
        dia_data['DIA'] = dia_data['DIA'].pct_change()
        spy_data['SPY'] = spy_data['SPY'].pct_change()
        qqq_data['QQQ'] = qqq_data['QQQ'].pct_change()
        vti_data['VTI'] = vti_data['VTI'].pct_change()
        
        # Drop the first row with NaN values from pct_change()
        dia_data = dia_data.dropna()
        spy_data = spy_data.dropna()
        qqq_data = qqq_data.dropna()
        vti_data = vti_data.dropna()
        
        # Combine all dataframes
        combined_data = dia_data.merge(spy_data, on='Date', how='outer') \
                                .merge(qqq_data, on='Date', how='outer') \
                                .merge(vti_data, on='Date', how='outer')
        
        # Set Date as index and sort chronologically
        combined_data.set_index('Date', inplace=True)
        combined_data.sort_index(inplace=True)
        
        # Extract year from the date index
        combined_data['Year'] = combined_data.index.year
        
        # Group by year and calculate annual returns correctly
        annual_returns = combined_data.groupby('Year')[['DIA', 'SPY', 'QQQ', 'VTI']].apply(
            lambda x: (1 + x).prod() - 1
        )
        
        # Convert to percentage and round to 2 decimal places
        annual_returns = (annual_returns * 100).round(2)
        
        return annual_returns, combined_data
        
    except Exception as e:
        return None, None

def create_cagr_heatmap(matrix_data, etf_name, start_year, end_year):
    """Create professional Plotly heatmap with excellent visibility and contrast"""
    
    # Reverse the matrix to show recent years at top
    display_matrix = matrix_data.iloc[::-1].copy()
    
    # Replace NaN values with None for better display
    display_matrix_clean = display_matrix.where(pd.notna(display_matrix), None)
    
    # Create a balanced colorscale with better contrast
    colorscale = [
        [0.0, '#800000'],    # Dark red for very negative
        [0.15, '#CC0000'],   # Red for negative
        [0.35, '#FF6666'],   # Light red for slightly negative
        [0.45, '#FFE6E6'],   # Very light red for small negative
        [0.5, '#F8F8F8'],    # Light gray for near zero
        [0.55, '#E6F3E6'],   # Very light green for small positive
        [0.65, '#66CC66'],   # Light green for positive
        [0.8, '#339933'],    # Green for good positive
        [1.0, '#006600']     # Dark green for very positive
    ]
    
    # Find the range of values for better color scaling
    flat_values = display_matrix_clean.values.flatten()
    valid_values = [v for v in flat_values if v is not None and not pd.isna(v)]
    
    if valid_values:
        min_val = min(valid_values)
        max_val = max(valid_values)
        # Cap the colorscale range for better visualization
        zmin = max(min_val, -50)
        zmax = min(max_val, 50)
    else:
        zmin, zmax = -30, 30
    
    # Create annotations for better text contrast
    annotations = []
    
    # Add the "From the start of" label
    annotations.append(
        dict(
            x=0.02,
            y=1.12,
            text='From the start of',
            showarrow=False,
            font=dict(color='#1f4e79', size=16, family='Arial'),
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='bottom'
        )
    )
    
    # Add value annotations with dynamic text color
    for i, row_year in enumerate(display_matrix_clean.index):
        for j, col_year in enumerate(display_matrix_clean.columns):
            value = display_matrix_clean.iloc[i, j]
            if pd.notna(value) and value is not None:
                # Determine text color based on value
                if value < -15:
                    text_color = 'white'
                elif value > 25:
                    text_color = 'white'
                else:
                    text_color = 'black'
                
                annotations.append(
                    dict(
                        x=col_year,
                        y=row_year,
                        text=f'{value:.1f}%',
                        showarrow=False,
                        font=dict(color=text_color, size=12, family='Arial'),
                        xref='x',
                        yref='y'
                    )
                )
    
    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=display_matrix_clean.values,
        x=display_matrix_clean.columns,
        y=display_matrix_clean.index,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        showscale=True,
        colorbar=dict(
            title=dict(
                text="CAGR (%)",
                side="right",
                font=dict(size=14, color='#1f4e79')
            ),
            tickmode="linear",
            tick0=-40,
            dtick=10,
            len=0.8,
            thickness=20,
            x=1.02,
            tickfont=dict(size=12, color='#1f4e79')
        ),
        hoverongaps=False,
        hovertemplate='<b>From %{x} to %{y}</b><br>CAGR: %{z:.1f}%<extra></extra>',
        text=display_matrix_clean.round(1),
        texttemplate='%{text}%',
        textfont=dict(size=11, color='black')
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{etf_name} - Compound Annual Growth Rate Matrix Period {start_year}-{end_year}',
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='#1f4e79', family='Arial'),
            pad=dict(t=20, b=15)
        ),
        xaxis=dict(
            title=None,
            side='top',
            tickfont=dict(size=12, color='#1f4e79'),
            dtick=1,
            tick0=start_year,
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=2,
            linecolor='#1f4e79'
        ),
        yaxis=dict(
            title=dict(
                text='To the end of',
                font=dict(size=16, color='#1f4e79', family='Arial'),
                standoff=20
            ),
            tickfont=dict(size=12, color='#1f4e79'),
            dtick=1,
            tick0=start_year,
            showgrid=False,
            zeroline=False,
            autorange='reversed',
            showline=True,
            linewidth=2,
            linecolor='#1f4e79'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=None,
        height=650,
        margin=dict(l=120, r=180, t=140, b=80),
        font=dict(family='Arial'),
        annotations=annotations
    )
    
    # Remove the default text to avoid overlap
    fig.data[0].text = None
    fig.data[0].texttemplate = None
    
    return fig

def display_performance_metrics(metrics_dict, ticker_name):
    """Display performance metrics in a professional layout"""
    
    # Create columns for metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    # Format helper function
    def format_metric(value, suffix='%', decimals=2):
        if value is None:
            return "N/A"
        if suffix == '%':
            return f"{value*100:.{decimals}f}{suffix}"
        else:
            return f"{value:.{decimals}f}"
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CAGR</div>
            <div class="metric-value">{format_metric(metrics_dict['cagr'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Volatility</div>
            <div class="metric-value">{format_metric(metrics_dict['volatility'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Max Drawdown</div>
            <div class="metric-value">{format_metric(metrics_dict['maximum_drawdown'])}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Sharpe Ratio</div>
            <div class="metric-value">{format_metric(metrics_dict['sharpe_ratio'], suffix='', decimals=3)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Sortino Ratio</div>
            <div class="metric-value">{format_metric(metrics_dict['sortino_ratio'], suffix='', decimals=3)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Calmar Ratio</div>
            <div class="metric-value">{format_metric(metrics_dict['calmar_ratio'], suffix='', decimals=3)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Win Rate</div>
            <div class="metric-value">{format_metric(metrics_dict['win_rate'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Pain Index</div>
            <div class="metric-value">{format_metric(metrics_dict['pain_index'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">VaR (5%)</div>
            <div class="metric-value">{format_metric(metrics_dict['var_5'])}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Best Year</div>
            <div class="metric-value">{format_metric(metrics_dict['best_year'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Worst Year</div>
            <div class="metric-value">{format_metric(metrics_dict['worst_year'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        recovery_days = metrics_dict['recovery_days']
        recovery_text = f"{recovery_days} days" if recovery_days else "Still in DD"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Recovery Days</div>
            <div class="metric-value">{recovery_text}</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Company Header
    st.markdown("""
    <div class="company-header">
        <h1 class="company-name">PEARSON CREEK CAPITAL LLC</h1>
        <p class="company-tagline">Professional ETF Performance Analysis & Investment Research</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📊 CAGR Matrix Analysis", "📈 Performance Overview", "🔍 Custom Ticker Analysis"])
    
    with tab1:
        # Load local data
        with st.spinner("📊 Loading market data..."):
            annual_returns, combined_data = load_etf_data()
        
        if annual_returns is None:
            st.info("📁 Local data files not found. Please use the Custom Ticker Analysis tab to fetch data from the API.")
            st.stop()
        
        # Control Panel
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            etf_options = ['SPY', 'QQQ', 'DIA', 'VTI']
            selected_etf = st.selectbox(
                "🎯 Select ETF:",
                etf_options,
                index=0,
                help="Choose which ETF to analyze"
            )
        
        with col2:
            # Time period selection
            available_years = annual_returns.index.tolist()
            min_year = min(available_years)
            max_year = max(available_years)
            
            time_period_options = {
                "Recent Decade (2013-2024)": (2013, 2024),
                "Post-Crisis (2010-2025)": (2010, 2025),
                "Modern Era (2000-2025)": (2000, 2025),
                "Full Period": (min_year, max_year),
                "Custom": "custom"
            }
            
            period_choice = st.selectbox(
                "📅 Time Period:",
                list(time_period_options.keys()),
                index=0
            )
        
        with col3:
            if period_choice == "Custom":
                start_year = st.number_input(
                    "Start Year:",
                    min_value=min_year,
                    max_value=max_year,
                    value=2013
                )
            else:
                start_year, end_year = time_period_options[period_choice]
                st.metric("Start Year", start_year)
        
        with col4:
            if period_choice == "Custom":
                end_year = st.number_input(
                    "End Year:",
                    min_value=min_year,
                    max_value=max_year,
                    value=2024
                )
            else:
                st.metric("End Year", end_year)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Validate year range
        if start_year >= end_year:
            st.error("⚠️ Start year must be less than end year!")
            st.stop()
        
        # Filter available data
        available_data = annual_returns[selected_etf].loc[start_year:end_year]
        if available_data.empty:
            st.error(f"❌ No data available for {selected_etf} in the period {start_year}-{end_year}")
            st.stop()
        
        # Generate CAGR matrix
        with st.spinner("🔄 Calculating CAGR matrix..."):
            cagr_matrix = create_cagr_matrix(annual_returns[selected_etf], start_year, end_year)
        
        # Display professional matrix as interactive heatmap
        heatmap_fig = create_cagr_heatmap(cagr_matrix, selected_etf, start_year, end_year)
        st.plotly_chart(heatmap_fig, use_container_width=True)
        
        # Instructions
        st.markdown("""
        <div class="instructions">
            <h4>📖 How to Read This Interactive Heatmap</h4>
            <ul>
                <li><strong>X-axis (From the start of):</strong> Starting year of investment period</li>
                <li><strong>Y-axis (To the end of):</strong> Ending year of investment period</li>
                <li><strong>Cell Values:</strong> Compound Annual Growth Rate (CAGR) for that specific time period</li>
                <li><strong>Color Coding:</strong> Red shades for negative returns, green shades for positive returns</li>
                <li><strong>Interactive:</strong> Hover over cells to see detailed CAGR information</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Statistics
        st.markdown('<div class="stats-container">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Best single year
            single_year_data = {year: cagr_matrix.loc[year, year] for year in cagr_matrix.index 
                               if not pd.isna(cagr_matrix.loc[year, year])}
            if single_year_data:
                best_year_value = max(single_year_data.values())
                best_year_actual = [year for year, value in single_year_data.items() if value == best_year_value][0]
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{best_year_value:.1f}%</div>
                    <div class="stat-label">Best Single Year ({best_year_actual})</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if single_year_data:
                worst_year_value = min(single_year_data.values())
                worst_year_actual = [year for year, value in single_year_data.items() if value == worst_year_value][0]
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{worst_year_value:.1f}%</div>
                    <div class="stat-label">Worst Single Year ({worst_year_actual})</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            # 10-year CAGR (if available)
            if end_year - 9 >= start_year:
                ten_year_start = end_year - 9
                if ten_year_start in cagr_matrix.index:
                    ten_year_cagr = cagr_matrix.loc[end_year, ten_year_start]
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">{ten_year_cagr:.1f}%</div>
                        <div class="stat-label">10-Year CAGR ({ten_year_start}-{end_year})</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col4:
            # Full period CAGR
            if start_year in cagr_matrix.index and end_year in cagr_matrix.index:
                full_period_cagr = cagr_matrix.loc[end_year, start_year]
                period_years = end_year - start_year + 1
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{full_period_cagr:.1f}%</div>
                    <div class="stat-label">{period_years}-Year CAGR ({start_year}-{end_year})</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ETF Comparison
        st.markdown("### 🔄 ETF Performance Comparison")
        comparison_data = {}
        
        for etf in etf_options:
            try:
                etf_matrix = create_cagr_matrix(annual_returns[etf], start_year, end_year)
                if start_year in etf_matrix.index and end_year in etf_matrix.index:
                    full_period_cagr = etf_matrix.loc[end_year, start_year]
                    comparison_data[etf] = full_period_cagr
            except:
                pass
        
        if comparison_data:
            comparison_df = pd.DataFrame.from_dict(
                comparison_data, 
                orient='index', 
                columns=[f'CAGR {start_year}-{end_year} (%)']
            ).round(2).sort_values(f'CAGR {start_year}-{end_year} (%)', ascending=False)
            
            st.dataframe(
                comparison_df,
                use_container_width=True,
                column_config={
                    f'CAGR {start_year}-{end_year} (%)': st.column_config.NumberColumn(
                        f'CAGR {start_year}-{end_year} (%)',
                        format="%.2f%%"
                    )
                }
            )
        
        # Download Section
        st.markdown("### 💾 Export Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            # Convert matrix to CSV
            display_matrix = cagr_matrix.round(2).fillna('')
            display_matrix_reversed = display_matrix.iloc[::-1]
            csv_data = display_matrix_reversed.to_csv()
            
            st.download_button(
                label=f"📥 Download {selected_etf} CAGR Matrix",
                data=csv_data,
                file_name=f"PearsonCreek_{selected_etf}_CAGR_Matrix_{start_year}_{end_year}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Download annual returns
            annual_display = annual_returns.loc[start_year:end_year]
            annual_csv = annual_display.to_csv()
            
            st.download_button(
                label=f"📊 Download Annual Returns Data",
                data=annual_csv,
                file_name=f"PearsonCreek_Annual_Returns_{start_year}_{end_year}.csv",
                mime="text/csv"
            )
    
    with tab2:
        st.markdown("### 📈 Performance Overview")
        
        # Check if we have local data
        if annual_returns is not None and combined_data is not None:
            # ETF selection for performance metrics
            selected_etf_perf = st.selectbox(
                "Select ETF for Performance Analysis:",
                ['SPY', 'QQQ', 'DIA', 'VTI'],
                key="perf_etf"
            )
            
            # Get daily returns for the selected ETF
            daily_returns = combined_data[selected_etf_perf].dropna()
            
            # Calculate performance metrics
            with st.spinner("Calculating performance metrics..."):
                metrics = calculate_performance_metrics(daily_returns)
            
            # Display metrics
            st.markdown(f"### {selected_etf_perf} Performance Metrics")
            display_performance_metrics(metrics, selected_etf_perf)
            
            # Additional visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Cumulative returns chart
                cumulative_returns = (1 + daily_returns).cumprod()
                fig_cumulative = go.Figure()
                fig_cumulative.add_trace(go.Scatter(
                    x=cumulative_returns.index,
                    y=cumulative_returns.values,
                    mode='lines',
                    name='Cumulative Returns',
                    line=dict(color='#1f4e79', width=2)
                ))
                fig_cumulative.update_layout(
                    title=f"{selected_etf_perf} Cumulative Returns",
                    xaxis_title="Date",
                    yaxis_title="Cumulative Return",
                    template="plotly_white",
                    height=400
                )
                st.plotly_chart(fig_cumulative, use_container_width=True)
            
            with col2:
                # Drawdown chart
                cumulative = (1 + daily_returns).cumprod()
                peak = cumulative.expanding().max()
                drawdown = (cumulative / peak) - 1
                
                fig_drawdown = go.Figure()
                fig_drawdown.add_trace(go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values * 100,
                    mode='lines',
                    name='Drawdown',
                    fill='tozeroy',
                    line=dict(color='#dc3545', width=1)
                ))
                fig_drawdown.update_layout(
                    title=f"{selected_etf_perf} Drawdown",
                    xaxis_title="Date",
                    yaxis_title="Drawdown (%)",
                    template="plotly_white",
                    height=400
                )
                st.plotly_chart(fig_drawdown, use_container_width=True)
        else:
            st.info("📁 Local data not available. Please use the Custom Ticker Analysis tab to fetch data from the API.")
    
    with tab3:
        st.markdown("### 🔍 Custom Ticker Analysis")
        
        # API Key input
        api_key = st.text_input(
            "Enter FMP API Key:",
            type="password",
            help="Get your free API key from https://financialmodelingprep.com/"
        )
        
        if api_key:
            try:
                # Initialize FMP provider
                fmp = FMPDataProvider(api_key)
                
                # Ticker input
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    ticker_input = st.text_input(
                        "Enter ticker symbols (comma-separated):",
                        value="SPY,QQQ,VTI",
                        help="Enter one or more ticker symbols separated by commas"
                    )
                
                with col2:
                    validate_btn = st.button("🔍 Validate Tickers", use_container_width=True)
                
                if ticker_input:
                    tickers = [t.strip().upper() for t in ticker_input.split(',')]
                    
                    if validate_btn:
                        # Validate tickers
                        valid_tickers = []
                        invalid_tickers = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, ticker in enumerate(tickers):
                            status_text.text(f"Validating {ticker}...")
                            if fmp.validate_ticker(ticker):
                                valid_tickers.append(ticker)
                            else:
                                invalid_tickers.append(ticker)
                            progress_bar.progress((i + 1) / len(tickers))
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        if valid_tickers:
                            st.success(f"✅ Valid tickers: {', '.join(valid_tickers)}")
                        if invalid_tickers:
                            st.error(f"❌ Invalid tickers: {', '.join(invalid_tickers)}")
                    
                    # Date range selection
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        start_year_api = st.number_input(
                            "Start Year:",
                            min_value=1980,
                            max_value=datetime.now().year,
                            value=2010,
                            key="api_start_year"
                        )
                    
                    with col2:
                        end_year_api = st.number_input(
                            "End Year:",
                            min_value=1980,
                            max_value=datetime.now().year,
                            value=datetime.now().year,
                            key="api_end_year"
                        )
                    
                    if st.button("📊 Fetch Data and Analyze", type="primary", use_container_width=True):
                        try:
                            # Fetch data for all tickers
                            returns_df, errors = fmp.get_multiple_tickers_returns(
                                tickers, start_year_api, end_year_api
                            )
                            
                            if not returns_df.empty:
                                st.success(f"✅ Successfully fetched data for {len(returns_df.columns)} tickers")
                                
                                # Display annual returns
                                st.markdown("### 📊 Annual Returns")
                                st.dataframe(
                                    returns_df.style.format("{:.2f}%"),
                                    use_container_width=True
                                )
                                
                                # Select ticker for CAGR matrix
                                selected_ticker_api = st.selectbox(
                                    "Select ticker for CAGR Matrix:",
                                    returns_df.columns.tolist(),
                                    key="api_ticker_select"
                                )
                                
                                # Generate CAGR matrix
                                if selected_ticker_api:
                                    cagr_matrix_api = create_cagr_matrix(
                                        returns_df[selected_ticker_api],
                                        start_year_api,
                                        end_year_api
                                    )
                                    
                                    # Display heatmap
                                    heatmap_fig_api = create_cagr_heatmap(
                                        cagr_matrix_api,
                                        selected_ticker_api,
                                        start_year_api,
                                        end_year_api
                                    )
                                    st.plotly_chart(heatmap_fig_api, use_container_width=True)
                                    
                                    # Performance metrics
                                    st.markdown(f"### 📈 {selected_ticker_api} Performance Metrics")
                                    
                                    # Get daily returns for metrics
                                    daily_returns_api = fmp.get_daily_returns(
                                        selected_ticker_api,
                                        start_year_api,
                                        end_year_api
                                    )
                                    
                                    # Calculate metrics
                                    metrics_api = calculate_performance_metrics(daily_returns_api)
                                    display_performance_metrics(metrics_api, selected_ticker_api)
                                    
                                    # Download options
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        # Download CAGR matrix
                                        csv_matrix = cagr_matrix_api.round(2).fillna('').to_csv()
                                        st.download_button(
                                            label=f"📥 Download {selected_ticker_api} CAGR Matrix",
                                            data=csv_matrix,
                                            file_name=f"{selected_ticker_api}_CAGR_Matrix_{start_year_api}_{end_year_api}.csv",
                                            mime="text/csv"
                                        )
                                    
                                    with col2:
                                        # Download annual returns
                                        csv_returns = returns_df.to_csv()
                                        st.download_button(
                                            label="📊 Download All Annual Returns",
                                            data=csv_returns,
                                            file_name=f"Annual_Returns_{start_year_api}_{end_year_api}.csv",
                                            mime="text/csv"
                                        )
                            
                            if errors:
                                st.warning(f"⚠️ Failed to fetch data for: {', '.join(errors.keys())}")
                                for ticker, error in errors.items():
                                    st.error(f"{ticker}: {error}")
                                    
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            
            except Exception as e:
                st.error(f"❌ Error initializing API: {str(e)}")
                st.info("Please ensure you have a valid FMP API key.")
        else:
            st.info("👆 Please enter your FMP API key to use custom ticker analysis.")
            st.markdown("[Get your free API key here](https://financialmodelingprep.com/)")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: var(--medium-gray); font-size: 0.9rem; padding: 1rem;">
        <strong>Pearson Creek Capital LLC</strong> | Professional Investment Research<br>
        <em>This analysis is for informational purposes only and does not constitute investment advice.</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()