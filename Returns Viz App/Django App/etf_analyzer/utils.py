import pandas as pd
import numpy as np
import os
from django.conf import settings
import plotly.graph_objects as go


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
    returns_decimal = annual_returns_series / 100
    
    if start_year is None:
        start_year = returns_decimal.index.min()
    if end_year is None:
        end_year = returns_decimal.index.max()
    
    returns_filtered = returns_decimal.loc[start_year:end_year]
    years = returns_filtered.index.tolist()
    
    matrix = pd.DataFrame(index=years, columns=years, dtype=float)
    
    for start_yr in years:
        for end_yr in years:
            if end_yr >= start_yr:
                period_returns = returns_filtered.loc[start_yr:end_yr]
                num_years = len(period_returns)
                
                if num_years == 1:
                    cagr = period_returns.loc[start_yr] * 100
                else:
                    cumulative_return = (1 + period_returns).prod()
                    cagr = (cumulative_return ** (1/num_years) - 1) * 100
                
                matrix.loc[end_yr, start_yr] = cagr
    
    return matrix


def create_total_return_matrix(annual_returns_series, start_year=None, end_year=None):
    """
    Creates a matrix of Total Returns between different year ranges.
    
    Parameters:
    annual_returns_series: Series with annual returns as percentages, indexed by year
    start_year: First year to include (default: earliest year in data)
    end_year: Last year to include (default: latest year in data)
    
    Returns:
    DataFrame where columns are starting years, rows are ending years,
    and values are total return percentages
    """
    returns_decimal = annual_returns_series / 100
    
    if start_year is None:
        start_year = returns_decimal.index.min()
    if end_year is None:
        end_year = returns_decimal.index.max()
    
    returns_filtered = returns_decimal.loc[start_year:end_year]
    years = returns_filtered.index.tolist()
    
    matrix = pd.DataFrame(index=years, columns=years, dtype=float)
    
    for start_yr in years:
        for end_yr in years:
            if end_yr >= start_yr:
                period_returns = returns_filtered.loc[start_yr:end_yr]
                
                # Calculate total return: compound the returns and subtract 1
                cumulative_return = (1 + period_returns).prod()
                total_return = (cumulative_return - 1) * 100
                
                matrix.loc[end_yr, start_yr] = total_return
    
    return matrix


def create_simple_annualized_return_matrix(annual_returns_series, start_year=None, end_year=None):
    """
    Creates a matrix of Simple Annualized Returns between different year ranges.
    Simple Annualized Return = Total Return ÷ Number of Years
    
    Parameters:
    annual_returns_series: Series with annual returns as percentages, indexed by year
    start_year: First year to include (default: earliest year in data)
    end_year: Last year to include (default: latest year in data)
    
    Returns:
    DataFrame where columns are starting years, rows are ending years,
    and values are simple annualized return percentages
    """
    returns_decimal = annual_returns_series / 100
    
    if start_year is None:
        start_year = returns_decimal.index.min()
    if end_year is None:
        end_year = returns_decimal.index.max()
    
    returns_filtered = returns_decimal.loc[start_year:end_year]
    years = returns_filtered.index.tolist()
    
    matrix = pd.DataFrame(index=years, columns=years, dtype=float)
    
    for start_yr in years:
        for end_yr in years:
            if end_yr >= start_yr:
                period_returns = returns_filtered.loc[start_yr:end_yr]
                num_years = len(period_returns)
                
                if num_years == 1:
                    # For single year periods, simple annualized return equals the single year return
                    simple_annualized_return = period_returns.loc[start_yr] * 100
                else:
                    # Calculate total return first
                    cumulative_return = (1 + period_returns).prod()
                    total_return = (cumulative_return - 1) * 100
                    
                    # Simple annualized return = Total return ÷ number of years
                    simple_annualized_return = total_return / num_years
                
                matrix.loc[end_yr, start_yr] = simple_annualized_return
    
    return matrix


def align_ticker_data(primary_returns, benchmark_returns):
    """
    Align two ticker return series to have the same year index (intersection of both)
    
    Parameters:
    primary_returns: Series with annual returns for primary ticker
    benchmark_returns: Series with annual returns for benchmark ticker
    
    Returns:
    Tuple of (aligned_primary, aligned_benchmark) with same year index
    """
    # Find intersection of years
    common_years = primary_returns.index.intersection(benchmark_returns.index)
    
    if len(common_years) == 0:
        raise ValueError("No overlapping years found between the two tickers")
    
    # Sort years
    common_years = sorted(common_years)
    
    # Return aligned data
    aligned_primary = primary_returns.loc[common_years]
    aligned_benchmark = benchmark_returns.loc[common_years]
    
    return aligned_primary, aligned_benchmark


def create_difference_matrix(primary_returns, benchmark_returns, matrix_type="CAGR", start_year=None, end_year=None):
    """
    Creates a matrix showing the difference between primary and benchmark returns
    Difference = Primary - Benchmark (positive means primary outperformed)
    
    Parameters:
    primary_returns: Series with annual returns for primary ticker (e.g., AAPL)
    benchmark_returns: Series with annual returns for benchmark ticker (e.g., SPY)
    matrix_type: Type of return calculation ("CAGR", "Total Return", "Simple Annualized Return")
    start_year: First year to include
    end_year: Last year to include
    
    Returns:
    DataFrame where values are differences (primary - benchmark)
    """
    # Align the data
    primary_aligned, benchmark_aligned = align_ticker_data(primary_returns, benchmark_returns)
    
    # Create matrices for both tickers using the same function
    if matrix_type == "CAGR":
        primary_matrix = create_cagr_matrix(primary_aligned, start_year, end_year)
        benchmark_matrix = create_cagr_matrix(benchmark_aligned, start_year, end_year)
    elif matrix_type == "Total Return":
        primary_matrix = create_total_return_matrix(primary_aligned, start_year, end_year)
        benchmark_matrix = create_total_return_matrix(benchmark_aligned, start_year, end_year)
    elif matrix_type == "Simple Annualized Return":
        primary_matrix = create_simple_annualized_return_matrix(primary_aligned, start_year, end_year)
        benchmark_matrix = create_simple_annualized_return_matrix(benchmark_aligned, start_year, end_year)
    else:
        raise ValueError(f"Unknown matrix type: {matrix_type}")
    
    # Calculate difference (primary - benchmark)
    difference_matrix = primary_matrix - benchmark_matrix
    
    return difference_matrix


def create_ratio_matrix(primary_returns, benchmark_returns, matrix_type="CAGR", start_year=None, end_year=None):
    """
    Creates a matrix showing the ratio between primary and benchmark returns
    Ratio = Primary ÷ Benchmark (>1.0 means primary outperformed)
    
    Parameters:
    primary_returns: Series with annual returns for primary ticker (e.g., AAPL)
    benchmark_returns: Series with annual returns for benchmark ticker (e.g., SPY)
    matrix_type: Type of return calculation ("CAGR", "Total Return", "Simple Annualized Return")
    start_year: First year to include
    end_year: Last year to include
    
    Returns:
    DataFrame where values are ratios (primary ÷ benchmark)
    """
    # Align the data
    primary_aligned, benchmark_aligned = align_ticker_data(primary_returns, benchmark_returns)
    
    # Create matrices for both tickers using the same function
    if matrix_type == "CAGR":
        primary_matrix = create_cagr_matrix(primary_aligned, start_year, end_year)
        benchmark_matrix = create_cagr_matrix(benchmark_aligned, start_year, end_year)
    elif matrix_type == "Total Return":
        primary_matrix = create_total_return_matrix(primary_aligned, start_year, end_year)
        benchmark_matrix = create_total_return_matrix(benchmark_aligned, start_year, end_year)
    elif matrix_type == "Simple Annualized Return":
        primary_matrix = create_simple_annualized_return_matrix(primary_aligned, start_year, end_year)
        benchmark_matrix = create_simple_annualized_return_matrix(benchmark_aligned, start_year, end_year)
    else:
        raise ValueError(f"Unknown matrix type: {matrix_type}")
    
    # Calculate ratio (primary ÷ benchmark)
    # Handle division by zero by replacing with NaN
    ratio_matrix = primary_matrix / benchmark_matrix
    ratio_matrix = ratio_matrix.replace([np.inf, -np.inf], np.nan)
    
    return ratio_matrix


def load_etf_data():
    """Load and process ETF data to calculate annual returns"""
    
    try:
        data_dir = settings.DATA_DIR
        
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        dia_data = pd.read_csv(os.path.join(data_dir, "DIA.csv"))
        spy_data = pd.read_csv(os.path.join(data_dir, "SPY.csv"))
        qqq_data = pd.read_csv(os.path.join(data_dir, "QQQ.csv"))
        vti_data = pd.read_csv(os.path.join(data_dir, "VTI.csv"))
        
        dia_data['Date'] = pd.to_datetime(dia_data['Date'])
        spy_data['Date'] = pd.to_datetime(spy_data['Date'])
        qqq_data['Date'] = pd.to_datetime(qqq_data['Date'])
        vti_data['Date'] = pd.to_datetime(vti_data['Date'])
        
        dia_data = dia_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'DIA'})
        spy_data = spy_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'SPY'})
        qqq_data = qqq_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'QQQ'})
        vti_data = vti_data[['Date', 'Adj Close']].rename(columns={'Adj Close': 'VTI'})
        
        dia_data['DIA'] = dia_data['DIA'].pct_change()
        spy_data['SPY'] = spy_data['SPY'].pct_change()
        qqq_data['QQQ'] = qqq_data['QQQ'].pct_change()
        vti_data['VTI'] = vti_data['VTI'].pct_change()
        
        dia_data = dia_data.dropna()
        spy_data = spy_data.dropna()
        qqq_data = qqq_data.dropna()
        vti_data = vti_data.dropna()
        
        combined_data = dia_data.merge(spy_data, on='Date', how='outer') \
                                .merge(qqq_data, on='Date', how='outer') \
                                .merge(vti_data, on='Date', how='outer')
        
        combined_data.set_index('Date', inplace=True)
        combined_data.sort_index(inplace=True)
        
        combined_data['Year'] = combined_data.index.year
        
        annual_returns = combined_data.groupby('Year')[['DIA', 'SPY', 'QQQ', 'VTI']].apply(
            lambda x: (1 + x).prod() - 1
        )
        
        annual_returns = (annual_returns * 100).round(2)
        
        return annual_returns, combined_data
        
    except Exception as e:
        raise Exception(f"Error loading data: {e}")


def create_cagr_heatmap(matrix_data, etf_name, start_year, end_year, matrix_type="CAGR"):
    """Create professional Plotly heatmap with excellent visibility and contrast"""
    
    display_matrix = matrix_data.iloc[::-1].copy()
    display_matrix_clean = display_matrix.where(pd.notna(display_matrix), None)
    
    # BLOOMBERG TERMINAL COLORSCALE - NUCLEAR MODE 🔥
    colorscale = [
        [0.0, 'rgb(255,0,64)'],      # Bright red for extreme losses
        [0.2, 'rgb(204,0,51)'],      # Dark red for significant losses
        [0.35, 'rgb(102,0,25)'],     # Deep red for moderate losses
        [0.45, 'rgb(51,26,0)'],      # Dark brown for mild losses
        [0.5, 'rgb(20,20,20)'],      # Terminal black for neutral
        [0.55, 'rgb(0,51,25)'],      # Dark green for mild gains
        [0.65, 'rgb(0,102,51)'],     # Medium green for moderate gains
        [0.8, 'rgb(0,204,102)'],     # Bright green for significant gains
        [1.0, 'rgb(0,255,65)']       # Neon green for extreme gains
    ]
    
    flat_values = display_matrix_clean.values.flatten()
    valid_values = [v for v in flat_values if v is not None and not pd.isna(v)]
    
    if valid_values:
        min_val = min(valid_values)
        max_val = max(valid_values)
        zmin = max(min_val, -50)
        zmax = min(max_val, 50)
    else:
        zmin, zmax = -30, 30
    
    text_matrix = display_matrix_clean.copy()
    text_colors = []
    
    for i in range(len(display_matrix_clean.index)):
        text_row = []
        for j in range(len(display_matrix_clean.columns)):
            value = display_matrix_clean.iloc[i, j]
            if pd.isna(value) or value is None:
                text_row.append('')
            else:
                if value < -10 or value > 20:
                    text_row.append('white')
                else:
                    text_row.append('black')
        text_colors.append(text_row)
    
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
                text=f"{matrix_type} (%)",
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
        hovertemplate=f'<b>From %{{x}} to %{{y}}</b><br>{matrix_type}: %{{z:.1f}}%<extra></extra>',
        text=display_matrix_clean.round(1),
        texttemplate='%{text}%',
        textfont=dict(size=11, color='white', family='JetBrains Mono, monospace')
    ))
    
    annotations = []
    
    annotations.append(
        dict(
            x=0.02,
            y=1.12,
            text='▶ FROM START OF',
            showarrow=False,
            font=dict(color='#ff6600', size=14, family='Orbitron'),
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='bottom'
        )
    )
    
    for i, row_year in enumerate(display_matrix_clean.index):
        for j, col_year in enumerate(display_matrix_clean.columns):
            value = display_matrix_clean.iloc[i, j]
            if pd.notna(value) and value is not None:
                # Bloomberg terminal text colors - WHITE for readability
                
                annotations.append(
                    dict(
                        x=col_year,
                        y=row_year,
                        text=f'{value:.1f}%',
                        showarrow=False,
                        font=dict(color='#ffffff', size=12, family='JetBrains Mono, monospace'),
                        xref='x',
                        yref='y'
                    )
                )
    
    # Professional title style
    title_text = f'{etf_name} /// {matrix_type} MATRIX /// PERIOD: {start_year}-{end_year}'
    if matrix_type == "CAGR":
        title_text = f'{etf_name} /// COMPOUND ANNUAL GROWTH RATE /// PERIOD: {start_year}-{end_year}'
    
    fig.update_layout(
        title=dict(
            text=title_text.upper(),
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='#ff6600', family='Orbitron, monospace'),
            pad=dict(t=20, b=20)
        ),
        xaxis=dict(
            title=None,
            side='top',
            tickfont=dict(size=12, color='#ff6600', family='JetBrains Mono'),
            dtick=1,
            tick0=start_year,
            showgrid=True,
            gridcolor='rgba(255,102,0,0.1)',
            zeroline=False,
            showline=True,
            linewidth=2,
            linecolor='#ff6600'
        ),
        yaxis=dict(
            title=dict(
                text='◀ TO END OF',
                font=dict(size=14, color='#ff6600', family='Orbitron'),
                standoff=20
            ),
            tickfont=dict(size=12, color='#ff6600', family='JetBrains Mono'),
            dtick=1,
            tick0=start_year,
            showgrid=True,
            gridcolor='rgba(255,102,0,0.1)',
            zeroline=False,
            autorange='reversed',
            showline=True,
            linewidth=2,
            linecolor='#ff6600'
        ),
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#141414',
        width=None,
        height=650,
        margin=dict(l=120, r=180, t=140, b=80),
        font=dict(family='Arial'),
        annotations=annotations
    )
    
    fig.data[0].text = None
    fig.data[0].texttemplate = None
    
    return fig