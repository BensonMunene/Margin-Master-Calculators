import streamlit as st
import pandas as pd
import numpy as np
import os
import warnings

warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="ETF CAGR Matrix Analysis",
    page_icon="📈",
    layout="wide"
)

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

def main():
    st.title("📈 ETF CAGR Matrix Analysis")
    st.markdown("**Compound Annual Growth Rate Analysis for ETFs**")
    
    # Load data
    with st.spinner("Loading ETF data..."):
        annual_returns, combined_data = load_etf_data()
    
    if annual_returns is None:
        st.stop()
    
    # Data summary
    st.sidebar.header("📊 Data Summary")
    st.sidebar.write(f"**Date Range:** {annual_returns.index.min()} to {annual_returns.index.max()}")
    st.sidebar.write(f"**Total Years:** {len(annual_returns)}")
    
    # Missing data info
    st.sidebar.subheader("Missing Data by ETF:")
    for etf in ['DIA', 'SPY', 'QQQ', 'VTI']:
        missing_pct = (combined_data[etf].isna().sum() / len(combined_data)) * 100
        st.sidebar.write(f"**{etf}:** {missing_pct:.1f}% missing")
    
    # User inputs
    st.sidebar.header("🎛️ Controls")
    
    # ETF selection
    etf_options = ['SPY', 'QQQ', 'DIA', 'VTI']
    selected_etf = st.sidebar.selectbox(
        "Select ETF:",
        etf_options,
        index=0,
        help="Choose which ETF to analyze"
    )
    
    # Time period selection
    available_years = annual_returns.index.tolist()
    min_year = min(available_years)
    max_year = max(available_years)
    
    st.sidebar.subheader("Time Period")
    
    # Predefined time periods
    time_period_options = {
        "Recent Decade (2013-2024)": (2013, 2024),
        "Post-Crisis (2010-2025)": (2010, 2025),
        "Modern Era (2000-2025)": (2000, 2025),
        "Full Period": (min_year, max_year),
        "Custom": "custom"
    }
    
    period_choice = st.sidebar.selectbox(
        "Select Time Period:",
        list(time_period_options.keys()),
        index=0
    )
    
    if period_choice == "Custom":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_year = st.number_input(
                "Start Year:",
                min_value=min_year,
                max_value=max_year,
                value=2013
            )
        with col2:
            end_year = st.number_input(
                "End Year:",
                min_value=min_year,
                max_value=max_year,
                value=2024
            )
    else:
        start_year, end_year = time_period_options[period_choice]
    
    # Ensure valid year range
    if start_year >= end_year:
        st.sidebar.error("Start year must be less than end year!")
        st.stop()
    
    # Filter available data
    available_data = annual_returns[selected_etf].loc[start_year:end_year]
    if available_data.empty:
        st.error(f"No data available for {selected_etf} in the period {start_year}-{end_year}")
        st.stop()
    
    # Main content
    st.header(f"{selected_etf} CAGR Matrix ({start_year}-{end_year})")
    
    # Generate CAGR matrix
    with st.spinner("Generating CAGR matrix..."):
        cagr_matrix = create_cagr_matrix(annual_returns[selected_etf], start_year, end_year)
    
    # Display matrix explanation
    st.info("""
    **How to read this matrix:**
    - **Columns** = Starting year of investment
    - **Rows** = Ending year of investment  
    - **Values** = Compound Annual Growth Rate (%) for that period
    - **Diagonal** = Single-year returns
    - **Upper triangle** = Empty (can't end before you start)
    - **Lower triangle** = Multi-year CAGRs
    """)
    
    # Format and display matrix
    display_matrix = cagr_matrix.round(2).fillna('')
    
    # Reverse row order to show most recent years at top
    display_matrix_reversed = display_matrix.iloc[::-1]
    
    # Color coding for better visualization
    def color_negative_red(val):
        if val == '' or pd.isna(val):
            return 'background-color: #f0f0f0'
        try:
            color = 'red' if float(val) < 0 else 'green' if float(val) > 15 else 'black'
            return f'color: {color}'
        except:
            return ''
    
    styled_matrix = display_matrix_reversed.style.applymap(color_negative_red)
    st.dataframe(styled_matrix, use_container_width=True)
    
    # Key statistics
    st.subheader("📊 Key Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Best single year
        single_year_returns = [cagr_matrix.loc[year, year] for year in cagr_matrix.index 
                              if not pd.isna(cagr_matrix.loc[year, year])]
        if single_year_returns:
            best_year = max(single_year_returns)
            worst_year = min(single_year_returns)
            st.metric("Best Single Year", f"{best_year:.2f}%")
            st.metric("Worst Single Year", f"{worst_year:.2f}%")
    
    with col2:
        # 5-year CAGR (if available)
        if end_year - 4 >= start_year:
            five_year_start = end_year - 4
            if five_year_start in cagr_matrix.index:
                five_year_cagr = cagr_matrix.loc[end_year, five_year_start]
                st.metric("5-Year CAGR", f"{five_year_cagr:.2f}%")
        
        # 10-year CAGR (if available)
        if end_year - 9 >= start_year:
            ten_year_start = end_year - 9
            if ten_year_start in cagr_matrix.index:
                ten_year_cagr = cagr_matrix.loc[end_year, ten_year_start]
                st.metric("10-Year CAGR", f"{ten_year_cagr:.2f}%")
    
    with col3:
        # Full period CAGR
        if start_year in cagr_matrix.index and end_year in cagr_matrix.index:
            full_period_cagr = cagr_matrix.loc[end_year, start_year]
            period_years = end_year - start_year + 1
            st.metric(f"{period_years}-Year CAGR", f"{full_period_cagr:.2f}%")
    
    # Comparison with other ETFs
    st.subheader("🔄 Quick Comparison")
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
        
        st.dataframe(comparison_df, use_container_width=True)
    
    # Download option
    st.subheader("💾 Download Data")
    
    # Convert matrix to CSV
    csv_data = display_matrix_reversed.to_csv()
    
    st.download_button(
        label=f"Download {selected_etf} CAGR Matrix ({start_year}-{end_year})",
        data=csv_data,
        file_name=f"CAGR_Matrix_{selected_etf}_{start_year}_{end_year}.csv",
        mime="text/csv"
    )
    
    # Annual returns table
    with st.expander("📅 View Annual Returns Data"):
        annual_display = annual_returns.loc[start_year:end_year]
        st.dataframe(annual_display, use_container_width=True)

if __name__ == "__main__":
    main()
