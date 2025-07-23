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


def create_cagr_heatmap(matrix_data, etf_name, start_year, end_year):
    """Create professional Plotly heatmap with excellent visibility and contrast"""
    
    display_matrix = matrix_data.iloc[::-1].copy()
    display_matrix_clean = display_matrix.where(pd.notna(display_matrix), None)
    
    colorscale = [
        [0.0, '#800000'],
        [0.15, '#CC0000'],
        [0.35, '#FF6666'],
        [0.45, '#FFE6E6'],
        [0.5, '#F8F8F8'],
        [0.55, '#E6F3E6'],
        [0.65, '#66CC66'],
        [0.8, '#339933'],
        [1.0, '#006600']
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
    
    annotations = []
    
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
    
    for i, row_year in enumerate(display_matrix_clean.index):
        for j, col_year in enumerate(display_matrix_clean.columns):
            value = display_matrix_clean.iloc[i, j]
            if pd.notna(value) and value is not None:
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
    
    fig.data[0].text = None
    fig.data[0].texttemplate = None
    
    return fig