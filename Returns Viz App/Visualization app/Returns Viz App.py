import streamlit as st
import pandas as pd
import numpy as np
import os
import warnings

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
        # Import the CSV files
        dia_data = pd.read_csv("../Historical Data/DIA.csv")
        spy_data = pd.read_csv("../Historical Data/SPY.csv")
        qqq_data = pd.read_csv("../Historical Data/QQQ.csv")
        vti_data = pd.read_csv("../Historical Data/VTI.csv")
        
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
        st.error("Please make sure the CSV files are in the '../Historical Data/' directory")
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

def create_professional_matrix_html(matrix_data, etf_name, start_year, end_year):
    """Create professional HTML table matching the screenshot style"""
    
    # Reverse the matrix to show recent years at top
    display_matrix = matrix_data.iloc[::-1]
    
    years = display_matrix.columns.tolist()
    
    html = f"""
    <div class="matrix-container">
        <div class="matrix-header">
            <h2 class="matrix-title">{etf_name} - Compound Annual Growth Rate Matrix</h2>
            <p class="matrix-subtitle">From the start of ({start_year} - {end_year})</p>
        </div>
        <table class="professional-table">
            <thead>
                <tr>
                    <th style="background-color: var(--primary-blue);">To Year / End of</th>
    """
    
    # Add year headers
    for year in years:
        html += f'<th>{year}</th>'
    
    html += """
                </tr>
            </thead>
            <tbody>
    """
    
    # Add data rows
    for row_year in display_matrix.index:
        html += f'<tr><td class="year-label">{row_year}</td>'
        
        for col_year in years:
            value = display_matrix.loc[row_year, col_year]
            formatted_value = format_value_with_color(value)
            html += f'<td>{formatted_value}</td>'
        
        html += '</tr>'
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html

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
    
    # Display professional matrix
    matrix_html = create_professional_matrix_html(cagr_matrix, selected_etf, start_year, end_year)
    st.markdown(matrix_html, unsafe_allow_html=True)
    
    # Instructions
    st.markdown("""
    <div class="instructions">
        <h4>📖 How to Read This Matrix</h4>
        <ul>
            <li><strong>Columns:</strong> Starting year of investment period</li>
            <li><strong>Rows:</strong> Ending year of investment period</li>
            <li><strong>Values:</strong> Compound Annual Growth Rate (CAGR) for that specific time period</li>
            <li><strong>Color Coding:</strong> Green shades indicate positive returns, red indicates losses</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Statistics
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Best single year
        single_year_returns = [cagr_matrix.loc[year, year] for year in cagr_matrix.index 
                              if not pd.isna(cagr_matrix.loc[year, year])]
        if single_year_returns:
            best_year = max(single_year_returns)
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{best_year:.1f}%</div>
                <div class="stat-label">Best Single Year</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if single_year_returns:
            worst_year = min(single_year_returns)
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{worst_year:.1f}%</div>
                <div class="stat-label">Worst Single Year</div>
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
                    <div class="stat-label">10-Year CAGR</div>
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
                <div class="stat-label">{period_years}-Year CAGR</div>
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
