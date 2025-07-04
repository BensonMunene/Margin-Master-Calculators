import streamlit as st
import pandas as pd
import numpy as np
import os
import warnings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    
    /* Matrix container */
    .matrix-container {
        background: white;
        border-radius: 10px;
        padding: 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    .matrix-header {
        background: var(--primary-blue);
        color: white;
        padding: 1.5rem;
        margin: 0;
    }
    
    .matrix-title {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
    }
    
    .matrix-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
    }
    
    /* Professional table styling */
    .professional-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Arial', sans-serif;
        margin: 0;
    }
    
    .professional-table th {
        background-color: var(--primary-blue);
        color: white;
        padding: 12px 8px;
        text-align: center;
        font-weight: 600;
        font-size: 0.9rem;
        border: 1px solid #dee2e6;
    }
    
    .professional-table td {
        padding: 10px 8px;
        text-align: center;
        font-size: 0.85rem;
        border: 1px solid #dee2e6;
        font-weight: 500;
    }
    
    .professional-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .professional-table tr:nth-child(odd) {
        background-color: white;
    }
    
    .professional-table tr:hover {
        background-color: #e3f2fd;
    }
    
    /* Year labels */
    .year-label {
        background-color: var(--primary-blue) !important;
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Value color coding */
    .positive-high { color: #006400; font-weight: 600; }
    .positive-medium { color: #228B22; font-weight: 600; }
    .positive-low { color: #32CD32; font-weight: 500; }
    .negative { color: #DC143C; font-weight: 600; }
    .neutral { color: var(--medium-gray); }
    
    /* Statistics cards */
    .stats-container {
        display: flex;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-left: 4px solid var(--accent-gold);
        flex: 1;
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
    
    /* Instructions panel */
    .instructions {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 8px;
        padding: 1.5rem;
        border-left: 4px solid var(--accent-gold);
        margin: 1rem 0;
    }
    
    /* Comparison table */
    .comparison-table {
        margin: 2rem 0;
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
    
    Parameters:
    annual_returns_series: Series with annual returns as percentages, indexed by year
    start_year: First year to include (default: earliest year in data)
    end_year: Last year to include (default: latest year in data)
    
    Returns:
    DataFrame where columns are starting years, rows are ending years,
    and values are CAGR percentages
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
                    # Multi-year CAGR: ((1+r1) * (1+r2) * ... * (1+rn))^(1/n) - 1
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
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
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
        st.error(f"Error loading data: {e}")
        st.error("Please make sure the CSV files are in the '../Historical Data/' directory relative to this script")
        st.error("Expected file structure:")
        st.code("""
Returns Viz App/
├── Visualization app/
│   └── Returns Viz App.py  (this file)
└── Historical Data/
    ├── DIA.csv
    ├── SPY.csv
    ├── QQQ.csv
    └── VTI.csv
        """)
        return None, None

def format_value_with_color(value):
    """Format values with appropriate color coding"""
    if pd.isna(value) or value == '':
        return ''
    
    try:
        val = float(value)
        if val >= 20:
            return f'<span class="positive-high">{val:.1f}%</span>'
        elif val >= 10:
            return f'<span class="positive-medium">{val:.1f}%</span>'
        elif val >= 0:
            return f'<span class="positive-low">{val:.1f}%</span>'
        else:
            return f'<span class="negative">{val:.1f}%</span>'
    except:
        return f'<span class="neutral">{value}</span>'

def create_cagr_heatmap(matrix_data, etf_name, start_year, end_year):
    """Create professional Plotly heatmap with excellent visibility and contrast"""
    
    # Reverse the matrix to show recent years at top (like in screenshot)
    display_matrix = matrix_data.iloc[::-1].copy()
    
    # Replace NaN values with None for better display
    display_matrix_clean = display_matrix.where(pd.notna(display_matrix), None)
    
    # Create a balanced colorscale with better contrast
    colorscale = [
        [0.0, '#800000'],    # Dark red for very negative (-40% and below)
        [0.15, '#CC0000'],   # Red for negative (-20% to -40%)
        [0.35, '#FF6666'],   # Light red for slightly negative (-5% to -20%)
        [0.45, '#FFE6E6'],   # Very light red for small negative (0% to -5%)
        [0.5, '#F8F8F8'],    # Light gray for near zero
        [0.55, '#E6F3E6'],   # Very light green for small positive (0% to 5%)
        [0.65, '#66CC66'],   # Light green for positive (5% to 15%)
        [0.8, '#339933'],    # Green for good positive (15% to 25%)
        [1.0, '#006600']     # Dark green for excellent positive (25%+)
    ]
    
    # Get the data range for better color scaling
    flat_values = display_matrix_clean.values.flatten()
    valid_values = [v for v in flat_values if v is not None and not pd.isna(v)]
    
    if valid_values:
        min_val = min(valid_values)
        max_val = max(valid_values)
        # Set reasonable bounds for color scaling
        zmin = max(min_val, -50)  # Don't go below -50%
        zmax = min(max_val, 50)   # Don't go above 50%
    else:
        zmin, zmax = -30, 30
    
    # Create text annotations with dynamic color for visibility
    text_matrix = display_matrix_clean.copy()
    text_colors = []
    
    for i in range(len(display_matrix_clean.index)):
        text_row = []
        for j in range(len(display_matrix_clean.columns)):
            value = display_matrix_clean.iloc[i, j]
            if pd.isna(value) or value is None:
                text_row.append('')
            else:
                # Use black text for light backgrounds, white for dark
                if value < -10 or value > 20:
                    text_row.append('white')
                else:
                    text_row.append('black')
        text_colors.append(text_row)
    
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
        textfont=dict(size=11, color='black')  # Default to black, we'll customize below
    ))
    
    # Manually set text colors for better contrast
    # This is a workaround since Plotly doesn't support per-cell text colors easily
    annotations = []
    
    # Add custom positioning for "From the start of" - positioned on the left with proper spacing
    annotations.append(
        dict(
            x=0.02,   # Position slightly inside the left edge of the plot area
            y=1.12,   # Position higher above the plot to avoid covering years
            text='From the start of',
            showarrow=False,
            font=dict(color='#1f4e79', size=16, family='Arial'),
            xref='paper',  # Use paper coordinates for positioning
            yref='paper',
            xanchor='left',  # Anchor to the left
            yanchor='bottom'
        )
    )
    
    # Add cell value annotations
    for i, row_year in enumerate(display_matrix_clean.index):
        for j, col_year in enumerate(display_matrix_clean.columns):
            value = display_matrix_clean.iloc[i, j]
            if pd.notna(value) and value is not None:
                # Determine text color based on background
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
    
    # Update layout to match professional style with reasonable spacing
    fig.update_layout(
        title=dict(
            text=f'{etf_name} - Compound Annual Growth Rate Matrix Period {start_year}-{end_year}',
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='#1f4e79', family='Arial'),
            pad=dict(t=20, b=15)  # Reasonable padding around title
        ),
        xaxis=dict(
            title=None,  # Remove the centered title
            side='top',
            tickfont=dict(size=12, color='#1f4e79'),
            dtick=1,  # Force show every year
            tick0=start_year,  # Start from the first year
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
                standoff=20  # Reasonable space between title and axis
            ),
            tickfont=dict(size=12, color='#1f4e79'),
            dtick=1,  # Force show every year
            tick0=start_year,  # Start from the first year
            showgrid=False,
            zeroline=False,
            autorange='reversed',  # Keep recent years at top
            showline=True,
            linewidth=2,
            linecolor='#1f4e79'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=None,  # Let Streamlit control width
        height=650,  # Back to reasonable height
        margin=dict(l=120, r=180, t=140, b=80),  # Reasonable margins
        font=dict(family='Arial'),
        annotations=annotations  # Add our custom text annotations
    )
    
    # Remove the default text to avoid overlap
    fig.data[0].text = None
    fig.data[0].texttemplate = None
    
    return fig

def main():
    # Company Header
    st.markdown("""
    <div class="company-header">
        <h1 class="company-name">PEARSON CREEK CAPITAL LLC</h1>
        <p class="company-tagline">Professional ETF Performance Analysis & Investment Research</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("📊 Loading market data..."):
        annual_returns, combined_data = load_etf_data()
    
    if annual_returns is None:
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
            <li><strong>Text Color:</strong> Dynamically adjusted (black/white) for optimal readability</li>
            <li><strong>Interactive:</strong> Hover over cells to see detailed CAGR information</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Statistics
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Best single year - find the specific year
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
        # 10-year CAGR (if available) - show specific period
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
        # Full period CAGR - show exact period
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
