import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from matplotlib.dates import DateFormatter, YearLocator, MonthLocator
import warnings
warnings.filterwarnings('ignore')
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.patches import Patch

# Set style for matplotlib
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Function to create enhanced candlestick plot using Plotly
def plot_candlestick(df, title, symbol='Stock'):
    # Resample data to monthly for better visualization
    df_resampled = df.resample('M').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    })
    
    # Define colors for a premium look
    up_color = '#2ecc71'  # Vibrant green
    down_color = '#e74c3c'  # Rich red
    wick_color = '#2c3e50'  # Dark slate
    shadow_color = '#95a5a6'  # Subtle gray for shadows
    
    # Create figure with candlestick
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df_resampled.index,
        open=df_resampled['Open'],
        high=df_resampled['High'],
        low=df_resampled['Low'],
        close=df_resampled['Close'],
        increasing_line=dict(color=up_color, width=1),
        decreasing_line=dict(color=down_color, width=1),
        whiskerwidth=0.5,
        line=dict(width=1),
        name='Price'
    ))
    
    # Configure layout for a premium look
    fig.update_layout(
        title={
            'text': f'{title} ({symbol})',
            'font': {
                'size': 18,
                'color': '#2c3e50',
                'family': 'Arial',
                'weight': 'bold'
            },
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis={
            'title': {
                'text': 'Date',
                'font': {
                    'size': 14,
                    'color': '#34495e',
                    'family': 'Arial'
                }
            },
            'rangeslider': {
                'visible': False  # Hide rangeslider for a cleaner look
            },
            'gridcolor': '#ecf0f1',
            'gridwidth': 1,
            'griddash': 'dash',
            'tickfont': {
                'size': 12,
                'color': '#34495e'
            },
            'tickformat': '%Y',  # Show only years by default
            'tickangle': 0,
            'type': 'date'
        },
        yaxis={
            'title': {
                'text': 'Price (USD)',
                'font': {
                    'size': 14,
                    'color': '#34495e',
                    'family': 'Arial'
                }
            },
            'tickformat': '$,.2f',
            'gridcolor': '#ecf0f1',
            'gridwidth': 1,
            'griddash': 'dash',
            'tickfont': {
                'size': 12,
                'color': '#34495e'
            },
            'autorange': True,
            'fixedrange': False
        },
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#ffffff',
        margin=dict(t=80, b=40, l=60, r=40),
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1,
            'traceorder': 'normal',
            'font': {'size': 12},
            'bgcolor': 'rgba(255, 255, 255, 0.9)',
            'bordercolor': '#ecf0f1',
            'borderwidth': 1
        },
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial'
        ),
        # Add shapes to highlight bullish and bearish markers for legend
        shapes=[
            # Shape to represent bullish in legend
            dict(
                type="rect",
                x0=0.8, x1=0.85,
                y0=1.05, y1=1.10,
                xref="paper", yref="paper",
                fillcolor=up_color,
                line=dict(width=0),
                opacity=0.8
            ),
            # Shape to represent bearish in legend
            dict(
                type="rect",
                x0=0.9, x1=0.95,
                y0=1.05, y1=1.10,
                xref="paper", yref="paper",
                fillcolor=down_color,
                line=dict(width=0),
                opacity=0.8
            )
        ],
        annotations=[
            # Bullish annotation
            dict(
                x=0.82,
                y=1.075,
                xref="paper",
                yref="paper",
                text="Bullish",
                showarrow=False,
                font=dict(
                    size=12,
                    color="#2c3e50"
                )
            ),
            # Bearish annotation
            dict(
                x=0.92,
                y=1.075,
                xref="paper",
                yref="paper",
                text="Bearish",
                showarrow=False,
                font=dict(
                    size=12,
                    color="#2c3e50"
                )
            )
        ],
        # Add custom hover template through layout instead of trace update
        hovermode='closest'
    )
    
    return fig

# Function to plot dividend bars
def plot_dividend_bars(df, title, symbol='Stock'):
    if 'Dividends' not in df.columns:
        raise ValueError("DataFrame must contain a 'Dividends' column")
    
    # Data preparation
    df_plot = df.copy()
    df_plot['Year'] = df_plot.index.year
    df_plot['Quarter'] = (df_plot.index.month - 1) // 3 + 1
    df_plot['QuarterLabel'] = df_plot['Quarter'].apply(lambda q: f'Q{q}')
    df_plot['YearQuarter'] = df_plot['Year'].astype(str) + '-Q' + df_plot['Quarter'].astype(str)
    
    # Calculate additional metrics
    df_plot['YoY_Growth'] = df_plot.groupby('Quarter')['Dividends'].pct_change(4) * 100
    
    # Calculate annual dividends
    annual_dividends = df_plot.groupby('Year')['Dividends'].sum().reset_index()
    annual_dividends['YoY_Growth'] = annual_dividends['Dividends'].pct_change() * 100
    
    # Calculate summary statistics
    current_year = df_plot['Year'].max()
    current_year_dividends = df_plot[df_plot['Year'] == current_year]['Dividends'].sum()
    previous_year_dividends = df_plot[df_plot['Year'] == (current_year - 1)]['Dividends'].sum() if current_year - 1 in df_plot['Year'].values else 0
    yoy_growth = ((current_year_dividends / previous_year_dividends) - 1) * 100 if previous_year_dividends > 0 else 0
    total_dividends = df_plot['Dividends'].sum()
    avg_quarterly = df_plot['Dividends'].mean()
    
    # Set color palette - create a continuous gradient based on growth rate
    def get_growth_color(growth):
        if pd.isna(growth):
            return '#7F7F7F'  # Gray for no growth data
        elif growth < 0:
            # Red spectrum for negative growth
            intensity = min(255, int(192 + abs(growth) * 3)) 
            return f'rgba({intensity}, 59, 59, 0.85)'
        else:
            # Green spectrum for positive growth
            intensity = min(255, int(46 + growth * 3))
            return f'rgba(46, {intensity}, 113, 0.85)'
    
    # Apply growth-based colors
    df_plot['Color'] = df_plot['YoY_Growth'].apply(get_growth_color)
    
    # Main figure
    fig = go.Figure()
    
    # Add background bands for years
    years = sorted(df_plot['Year'].unique())
    for i, year in enumerate(years):
        year_data = df_plot[df_plot['Year'] == year]
        if len(year_data) > 0:
            start_date = year_data.index.min() - datetime.timedelta(days=15)
            end_date = year_data.index.max() + datetime.timedelta(days=15)
            
            # Alternate background colors for years
            bgcolor = '#f0f4f8' if i % 2 == 0 else '#e8eef3'
            
            fig.add_shape(
                type="rect",
                x0=start_date,
                x1=end_date,
                y0=0,
                y1=1,
                yref="paper",
                fillcolor=bgcolor,
                opacity=0.3,
                layer="below",
                line=dict(width=0)
            )
    
    # Add trend line for dividend growth
    quarterly_avg = df_plot.groupby(['Year', 'Quarter'])['Dividends'].mean().reset_index()
    quarterly_avg['Date'] = quarterly_avg.apply(
        lambda x: pd.Timestamp(f"{int(x['Year'])}-{int(x['Quarter']*3-2)}-15"), axis=1
    )
    quarterly_avg = quarterly_avg.sort_values('Date')
    
    fig.add_trace(go.Scatter(
        x=quarterly_avg['Date'],
        y=quarterly_avg['Dividends'],
        mode='lines',
        line=dict(
            color='rgba(53, 92, 125, 0.7)',
            width=2,
            dash='solid'
        ),
        name='Dividend Trend',
        hoverinfo='skip'
    ))
    
    # Add bars with dynamic hover information
    for i, row in df_plot.iterrows():
        # Define detailed hover template
        hover_template = (
            f"<b>{row['Year']} Q{row['Quarter']}</b><br>" +
            f"Dividend: <b>${row['Dividends']:.2f}</b><br>" +
            (f"YoY Growth: <b>{row['YoY_Growth']:.1f}%</b>" if not pd.isna(row['YoY_Growth']) else "YoY Growth: <b>N/A</b>") +
            "<extra></extra>"
        )
        
        # Main bar for each dividend payment
        fig.add_trace(go.Bar(
            x=[i],
            y=[row['Dividends']],
            width=30,
            marker=dict(
                color=row['Color'],
                line=dict(color='rgba(255, 255, 255, 0.5)', width=1)
            ),
            name=f"{row['Year']} Q{row['Quarter']}",
            text=f"Q{row['Quarter']}",
            textposition='inside',
            insidetextfont=dict(color='white', size=11, family='Arial Bold'),
            hoverinfo='text',
            hovertext=hover_template,
            showlegend=False
        ))
        
        # Add growth indicator arrows for each bar when available
        if not pd.isna(row['YoY_Growth']):
            arrow_y = row['Dividends'] + 0.02
            arrow_symbol = "triangle-up" if row['YoY_Growth'] >= 0 else "triangle-down"
            arrow_color = "#2ecc71" if row['YoY_Growth'] >= 0 else "#e74c3c"
            
            fig.add_trace(go.Scatter(
                x=[i],
                y=[arrow_y],
                mode='markers',
                marker=dict(
                    symbol=arrow_symbol,
                    size=10,
                    color=arrow_color,
                    line=dict(color='rgba(255, 255, 255, 0.8)', width=1)
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add annual dividend markers
    for _, row in annual_dividends.iterrows():
        year_data = df_plot[df_plot['Year'] == row['Year']]
        if not year_data.empty:
            mid_date = year_data.index.min() + (year_data.index.max() - year_data.index.min()) / 2
            
            # Annual sum annotation above the bars
            fig.add_annotation(
                x=mid_date,
                y=year_data['Dividends'].max() * 1.25,
                text=f"${row['Dividends']:.2f}",
                showarrow=False,
                font=dict(size=13, color="#2c3e50", family="Arial", weight="bold"),
                bgcolor="rgba(255, 255, 255, 0.85)",
                bordercolor="#34495e",
                borderwidth=1,
                borderpad=4,
                opacity=0.9
            )
    
    
    
    
    # Add year labels at the top
    for year in years:
        year_data = df_plot[df_plot['Year'] == year]
        if not year_data.empty:
            mid_date = year_data.index.min() + (year_data.index.max() - year_data.index.min()) / 2
            
            # Year label
            fig.add_annotation(
                x=mid_date,
                y=1.05,
                text=str(year),
                showarrow=False,
                xref="x",
                yref="paper",
                font=dict(size=13, color="#34495e", family="Arial", weight="bold"),
                bgcolor="white",
                bordercolor="#95a5a6",
                borderwidth=1,
                borderpad=3,
                opacity=0.9
            )
    
    # Add summary statistics as annotations
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"<b>Summary</b><br>" +
             f"Total: <b>${total_dividends:.2f}</b><br>" +
             f"Latest Annual: <b>${current_year_dividends:.2f}</b>" +
             (f"<br>YoY: <b>{yoy_growth:+.1f}%</b>" if previous_year_dividends > 0 else ""),
        showarrow=False,
        align="left",
        font=dict(size=12, color="#2c3e50"),
        bgcolor="rgba(255, 255, 255, 0.85)",
        bordercolor="#95a5a6",
        borderwidth=1,
        borderpad=5,
        opacity=0.9
    )
    
    # Add legend for growth indicators
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(symbol="triangle-up", size=10, color="#2ecc71"),
        name='YoY Increase',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(symbol="triangle-down", size=10, color="#e74c3c"),
        name='YoY Decrease',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='lines',
        line=dict(color='rgba(53, 92, 125, 0.7)', width=2),
        name='Trend Line',
        showlegend=True
    ))
    
    # Configure layout
    max_dividend = df_plot['Dividends'].max() * 1.35  # Increased space for annotations
    
    fig.update_layout(
        title={
            'text': f"<b>{title}</b><br><span style='font-size:14px; color:#7f8c8d'>Quarterly Dividend Distribution ({symbol})</span>",
            'font': {
                'size': 22,
                'color': '#2c3e50',
                'family': 'Arial',
            },
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis={
            'title': {
                'text': 'Distribution Date',
                'font': {
                    'size': 14,
                    'color': '#34495e',
                    'family': 'Arial'
                }
            },
            'tickangle': 45,
            'gridcolor': '#ecf0f1',
            'gridwidth': 0.5,
            'tickfont': {
                'size': 11,
                'color': '#34495e'
            },
            'type': 'date',
            'tickformat': '%b %Y',
            'dtick': 'M3',
            'showgrid': False
        },
        yaxis={
            'title': {
                'text': 'Dividend per Share (USD)',
                'font': {
                    'size': 14,
                    'color': '#34495e',
                    'family': 'Arial'
                }
            },
            'tickformat': '$,.2f',
            'gridcolor': '#ecf0f1',
            'gridwidth': 0.5,
            'range': [0, max_dividend],
            'tickfont': {
                'size': 11,
                'color': '#34495e'
            },
            'showgrid': True
        },
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        margin=dict(t=120, b=60, l=60, r=40),
        showlegend=True,
        legend={
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.01,
            'xanchor': 'right',
            'x': 1,
            'bgcolor': 'rgba(255, 255, 255, 0.8)',
            'bordercolor': '#d5dbdb',
            'borderwidth': 1
        },
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial',
            bordercolor='#95a5a6'
        ),
        hovermode='closest',
        modebar={'orientation': 'v'},
        bargap=0.35
    )
    
    # Add a subtle watermark
    fig.add_annotation(
        text=symbol,
        x=0.98,
        y=0.05,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=80, color="#ecf0f1"),
        opacity=0.15,
        align="right"
    )
    
    # Add custom range buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.02,
                y=1.1,
                buttons=[
                    dict(
                        label="5Y",
                        method="relayout",
                        args=[{"xaxis.range": [df_plot.index.max() - pd.DateOffset(years=5), df_plot.index.max() + pd.DateOffset(months=1)]}]
                    ),
                    dict(
                        label="All",
                        method="relayout",
                        args=[{"xaxis.autorange": True}]
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                bgcolor="#ffffff",
                bordercolor="#d5dbdb",
                borderwidth=1,
                font=dict(size=12)
            )
        ]
    )
    
    return fig

# Function to create dividend plots using matplotlib and seaborn - Updated version
def plot_dividend_bars_mpl(df, title, symbol='Stock', width_factor=0.6):
    """
    Create elegant dividend bar plots using matplotlib and seaborn with sophisticated styling
    """
    if 'Dividends' not in df.columns:
        raise ValueError("DataFrame must contain a 'Dividends' column")
    
    # Data preparation - filter out zero dividends
    df_plot = df.copy()
    df_plot = df_plot[df_plot['Dividends'] > 0]
    
    if df_plot.empty:
        st.warning(f"No dividend data available for {symbol}")
        return None
    
    #— figure & style
    fig, ax = plt.subplots(figsize=(18, 9), dpi=150)
    sns.set_style("whitegrid", {
        'grid.linestyle': '--', 'grid.alpha': 0.2,
        'axes.facecolor': '#f9fbfc', 'figure.facecolor': '#ffffff',
    })
    ax.set_facecolor('#f8f9fa')
    
    #— compute bar positions & widths
    dates = mdates.date2num(df_plot.index.to_pydatetime())
    avg_dist = np.mean(np.diff(dates)) if len(dates) > 1 else 1
    bar_width = avg_dist * width_factor
    
    #— year bands & labels (works for both SPY & VTI)
    years = df_plot.index.year.unique()
    colors = plt.cm.viridis(np.linspace(0, 0.85, len(years)))
    year_to_color = dict(zip(sorted(years), colors))
    prev, start = None, None
    bands = []
    for i, dt in enumerate(df_plot.index):
        y = dt.year
        if y != prev:
            if prev is not None:
                bands.append((start, i-1, prev))
            start = i
            prev = y
    bands.append((start, len(df_plot)-1, prev))
    
    # Use different y position for year labels depending on symbol
    for idx, (s, e, y) in enumerate(bands):
        left = dates[s] - bar_width/1.5
        right = dates[e] + bar_width/1.5
        color = '#f0f4f8' if idx % 2 == 0 else '#e8eef3'
        ax.axvspan(left, right, color=color, alpha=0.4, zorder=0)
        mid = (left + right)/2
        if symbol == 'SPY':
            year_y = ax.get_ylim()[1]*2.1
        elif symbol == 'VTI':
            year_y = ax.get_ylim()[1]*1.07
        else:
            year_y = ax.get_ylim()[1]*1.01
        ax.text(mid, year_y, str(y),
                ha='center', va='bottom', fontsize=12,
                fontweight='bold', color='#34495e',
                bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.2'))
    
    #— bars & annotations
    for i, (dt, row) in enumerate(df_plot.iterrows()):
        x = dates[i]
        div = row['Dividends']
        ycol = year_to_color[dt.year]
        # shadow
        ax.bar(x+bar_width/4, div, width=bar_width*1.1,
               color='#7f8c8d', alpha=0.15, zorder=1)
        # main
        ax.bar(x, div, width=bar_width, color=ycol, alpha=0.9, zorder=3)
        # quarter label
        q = (dt.month-1)//3 + 1
        ax.text(x, div/2, f'Q{q}',
                ha='center', va='center', fontsize=9,
                fontweight='bold', color='white', zorder=5)
        # dividend value
        ax.text(x, div + div*0.02, f'${div:.2f}',
                ha='center', va='bottom', fontsize=10,
                fontweight='bold', color='#2c3e50',
                rotation=90, zorder=4)
    
    #— axis titles & formatting
    ax.set_title(f'{title} ({symbol})', fontsize=20,
                 fontweight='bold', pad=20, color='#2c3e50')
    ax.text(0.5, 0.97, 'Quarterly Dividend Distribution',
            ha='center', va='top', transform=ax.transAxes,
            fontsize=12, fontstyle='italic', color='#7f8c8d')
    ax.set_xlabel('Year', fontsize=14, fontweight='medium', color='#34495e')
    ax.set_ylabel('Dividend per Share (USD)', fontsize=14,
                  fontweight='medium', color='#34495e')
    
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator([1,4,7,10]))
    ax.grid(which='minor', axis='x', linestyle=':', alpha=0.4, zorder=0)
    ax.grid(which='major', axis='y', linestyle='--', alpha=0.2, color='#bdc3c7')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.2f}'))
    ax.tick_params(axis='both', which='major', labelsize=12, colors='#34495e')
    ax.tick_params(axis='x', which='major', width=6, direction='out', pad=10, rotation=45)
    
    #— clip top margins so annotations fit
    top = df_plot['Dividends'].max() * 1.15
    ax.set_ylim(0, top)
    
    #— remove space before 2010 & add room after last bar
    first, last = dates[0], dates[-1]
    ax.set_xlim(first - bar_width/2, last + bar_width*4)
    
    #— hide that "2026" tick label and build legend there
    for lbl in ax.get_xticklabels():
        if lbl.get_text() == '2026':
            lbl.set_visible(False)
    
    legend_years = [y for y in sorted(years) if y != 2026]
    legend_elements = [
        Patch(facecolor=year_to_color[y], label=str(y))
        for y in legend_years
    ]
    ax.legend(
        handles=legend_elements,
        bbox_to_anchor=(1, 1),
        loc='upper left',
        borderaxespad=0,
        handlelength=1,
        handletextpad=0.5,
        fontsize=10,
        frameon=True
    )
    
    #— polished spines & watermark
    for spine in ax.spines.values():
        spine.set_edgecolor('#d5dbdb')
        spine.set_linewidth(1.5)
    fig.text(0.95, 0.05, symbol, fontsize=60,
             color='#ecf0f1', ha='right', va='bottom', alpha=0.2)
    
    plt.tight_layout(pad=2)
    return fig 