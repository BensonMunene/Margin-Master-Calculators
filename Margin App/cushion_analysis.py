"""
Margin Cushion Analytics Module
===============================

This module provides comprehensive margin cushion risk management analytics
for leveraged trading strategies. It can be imported optionally to add
advanced cushion monitoring capabilities to backtesting applications.

Author: MarginMaster Analytics
License: Proprietary
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

# Module version and metadata
__version__ = "1.0.0"
__author__ = "MarginMaster Analytics"
__description__ = "Advanced Margin Cushion Risk Management Analytics"

def create_cushion_analytics_dashboard(df_results: pd.DataFrame, metrics: Dict[str, float], use_dark_theme: bool = True) -> go.Figure:
    """Create comprehensive margin cushion analytics dashboard"""
    
    # Define color schemes based on theme
    if use_dark_theme:
        # Dark theme colors (Bloomberg Terminal style)
        bg_color = '#0a0a0a'
        plot_bg_color = '#1a1a1a'
        grid_color = '#333333'
        text_color = '#ffffff'
        title_color = '#00ff88'
        
        # Risk zone colors for dark theme
        safe_color = '#00ff88'  # Bright green
        caution_color = '#ffbb00'  # Bright yellow
        warning_color = '#ff6600'  # Bright orange
        critical_color = '#ff3366'  # Bright red
        
        # Line colors for dark theme
        primary_line_color = '#00d4ff'  # Bright cyan
        secondary_line_color = '#ff3366'  # Bright red
        tertiary_line_color = '#00ff88'  # Bright green
        quaternary_line_color = '#ff00ff'  # Bright magenta
        
        # Fill colors with transparency
        safe_fill = 'rgba(0, 255, 136, 0.15)'
        caution_fill = 'rgba(255, 187, 0, 0.15)'
        warning_fill = 'rgba(255, 102, 0, 0.15)'
        critical_fill = 'rgba(255, 51, 102, 0.15)'
        
    else:
        # Light theme colors (Professional Report style)
        bg_color = '#ffffff'
        plot_bg_color = '#ffffff'
        grid_color = '#E8E8E8'
        text_color = '#2C3E50'
        title_color = '#2C3E50'
        
        # Risk zone colors for light theme
        safe_color = '#27AE60'  # Green
        caution_color = '#F39C12'  # Yellow
        warning_color = '#E67E22'  # Orange
        critical_color = '#E74C3C'  # Red
        
        # Line colors for light theme
        primary_line_color = '#1f77b4'  # Blue
        secondary_line_color = '#DC3545'  # Red
        tertiary_line_color = '#27AE60'  # Green
        quaternary_line_color = '#8E44AD'  # Purple
        
        # Fill colors with transparency
        safe_fill = 'rgba(39, 174, 96, 0.1)'
        caution_fill = 'rgba(243, 156, 18, 0.15)'
        warning_fill = 'rgba(230, 126, 34, 0.15)'
        critical_fill = 'rgba(231, 76, 60, 0.15)'
    
    # Calculate cushion metrics
    df_cushion = df_results.copy()
    
    # Calculate cushion percentage: (Equity - Maintenance_Margin) / Maintenance_Margin * 100
    # This shows how much buffer exists above the minimum requirement
    df_cushion['Cushion_Percentage'] = np.where(
        df_cushion['Maintenance_Margin_Required'] > 0,
        ((df_cushion['Equity'] - df_cushion['Maintenance_Margin_Required']) / df_cushion['Maintenance_Margin_Required']) * 100,
        0
    )
    
    # Calculate cushion dollar amount
    df_cushion['Cushion_Dollars'] = df_cushion['Equity'] - df_cushion['Maintenance_Margin_Required']
    
    # Calculate break-even price (price at which margin call would trigger)
    df_cushion['Break_Even_Price'] = np.where(
        df_cushion['Shares_Held'] > 0,
        df_cushion['Margin_Loan'] / (df_cushion['Shares_Held'] * (1 - (metrics.get('maintenance_margin_pct', 25) / 100))),
        0
    )
    
    # Calculate portfolio value drop requirements
    df_cushion['Current_Portfolio_Value'] = df_cushion['ETF_Price'] * df_cushion['Shares_Held']
    df_cushion['Portfolio_Drop_Required_Dollars'] = np.where(
        df_cushion['Shares_Held'] > 0,
        (df_cushion['ETF_Price'] - df_cushion['Break_Even_Price']) * df_cushion['Shares_Held'],
        0
    )
    df_cushion['Portfolio_Drop_Required_Percentage'] = np.where(
        df_cushion['Current_Portfolio_Value'] > 0,
        (df_cushion['Portfolio_Drop_Required_Dollars'] / df_cushion['Current_Portfolio_Value']) * 100,
        0
    )
    
    # Calculate distance from margin call
    df_cushion['Price_Distance_Dollars'] = df_cushion['ETF_Price'] - df_cushion['Break_Even_Price']
    df_cushion['Price_Distance_Percentage'] = np.where(
        df_cushion['ETF_Price'] > 0,
        (df_cushion['Price_Distance_Dollars'] / df_cushion['ETF_Price']) * 100,
        0
    )
    
    # Create color mapping for risk zones
    def get_cushion_color(cushion_pct):
        if cushion_pct >= 50:
            return safe_color
        elif cushion_pct >= 20:
            return caution_color
        elif cushion_pct >= 5:
            return warning_color
        else:
            return critical_color
    
    # Apply color mapping
    df_cushion['Risk_Color'] = df_cushion['Cushion_Percentage'].apply(get_cushion_color)
    
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=(
            'Margin Cushion Over Time', 'Real-Time Cushion Gauge',
            'ETF Price vs Margin Call Price', 'Portfolio Value Drop Required (%)',
            'Cushion Dollar Buffer', 'Portfolio Value Drop Required ($)',
            'Break-Even Price Analysis', 'Portfolio Value vs Loan Balance'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "indicator"}],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08
    )
    
    # Handle different backtest modes - some don't have 'In_Position' column
    if 'In_Position' in df_cushion.columns:
        active_positions = df_cushion[df_cushion['In_Position'] == True]
    else:
        # For constant leverage mode, consider positions active when shares are held
        active_positions = df_cushion[df_cushion['Shares_Held'] > 0]
    
    # 1. Cushion percentage over time with risk zones
    if not active_positions.empty:
        x_range = [active_positions.index[0], active_positions.index[-1]]
        
        # Add shaded regions first (so they appear behind other elements)
        # Light green shading below 50% line
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=[50, 50],
                mode='lines',
                line=dict(color='rgba(255,255,255,0)'),  # Invisible line
                name='Safe Zone Background',
                showlegend=False,
                hoverinfo='skip',
                fill='tozeroy',
                fillcolor=safe_fill
            ),
            row=1, col=1
        )
        
        # Light yellow shading below 20% line
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=[20, 20],
                mode='lines',
                line=dict(color='rgba(255,255,255,0)'),  # Invisible line
                name='Caution Zone Background',
                showlegend=False,
                hoverinfo='skip',
                fill='tozeroy',
                fillcolor=caution_fill
            ),
            row=1, col=1
        )
        
        # Light red shading below 5% line
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=[5, 5],
                mode='lines',
                line=dict(color='rgba(255,255,255,0)'),  # Invisible line
                name='Critical Zone Background',
                showlegend=False,
                hoverinfo='skip',
                fill='tozeroy',
                fillcolor=critical_fill
            ),
            row=1, col=1
        )
        
        # Create colored segments for different risk zones
        cushion_data = active_positions['Cushion_Percentage']
        dates = active_positions.index
        
        # Create continuous colored segments
        for i in range(len(cushion_data)):
            if i == 0:
                continue  # Skip first point as we need pairs for segments
            
            # Get current and previous values
            prev_cushion = cushion_data.iloc[i-1]
            curr_cushion = cushion_data.iloc[i]
            prev_date = dates[i-1]
            curr_date = dates[i]
            
            # Determine color based on the current cushion level
            if curr_cushion >= 50:
                color = safe_color
                zone_name = 'Safe Zone'
            elif curr_cushion >= 20:
                color = caution_color
                zone_name = 'Caution Zone'
            elif curr_cushion >= 5:
                color = warning_color
                zone_name = 'Warning Zone'
            else:
                color = critical_color
                zone_name = 'Critical Zone'
            
            # Add line segment
            fig.add_trace(
                go.Scatter(
                    x=[prev_date, curr_date],
                    y=[prev_cushion, curr_cushion],
                    mode='lines',
                    name='Margin Cushion %' if i == 1 else None,  # Only show name for first segment
                    showlegend=True if i == 1 else False,  # Only show in legend once
                    line=dict(color=color, width=3),
                    fill='tozeroy',  # Fill area below the line
                    fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.05)',  # Very light transparent fill
                    hovertemplate=f'{zone_name}<br>Date: %{{x}}<br>Cushion: %{{y:.1f}}%<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Add horizontal threshold lines
        if not active_positions.empty:
            # Safe zone threshold (50%)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[50, 50],
                    mode='lines',
                    line=dict(color=safe_color, width=2, dash='dash'),
                    name='Safe Zone (50%)',
                    showlegend=True,
                    hovertemplate='Safe Zone: 50%<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Caution zone threshold (20%)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[20, 20],
                    mode='lines',
                    line=dict(color=caution_color, width=2, dash='dash'),
                    name='Caution Zone (20%)',
                    showlegend=True,
                    hovertemplate='Caution Zone: 20%<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Critical zone threshold (5%)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[5, 5],
                    mode='lines',
                    line=dict(color=critical_color, width=2, dash='dash'),
                    name='Critical Zone (5%)',
                    showlegend=True,
                    hovertemplate='Critical Zone: 5%<extra></extra>'
                ),
                row=1, col=1
            )
    
    # 2. Current cushion gauge (using last available data)
    current_cushion = active_positions['Cushion_Percentage'].iloc[-1] if not active_positions.empty else 0
    gauge_color = get_cushion_color(current_cushion)
    
    # Define gauge background colors based on theme
    if use_dark_theme:
        gauge_bg_colors = [
            {'range': [0, 5], 'color': "rgba(255, 51, 102, 0.3)"},      # Critical zone
            {'range': [5, 20], 'color': "rgba(255, 102, 0, 0.3)"},      # Warning zone  
            {'range': [20, 50], 'color': "rgba(255, 187, 0, 0.3)"},     # Caution zone
            {'range': [50, 100], 'color': "rgba(0, 255, 136, 0.3)"}     # Safe zone
        ]
        threshold_color = "#ffffff"
    else:
        gauge_bg_colors = [
            {'range': [0, 5], 'color': "#FADBD8"},      # Critical zone
            {'range': [5, 20], 'color': "#FCF3CF"},     # Warning zone  
            {'range': [20, 50], 'color': "#FEF9E7"},    # Caution zone
            {'range': [50, 100], 'color': "#EAFAF1"}    # Safe zone
        ]
        threshold_color = "black"
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=current_cushion,
            delta={'reference': 50, 'valueformat': '.1f'},
            title={'text': "Current Margin Cushion", 'font': {'size': 16, 'color': text_color}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100], 'tickformat': '.0f', 'tickfont': {'color': text_color}},
                'bar': {'color': gauge_color, 'thickness': 0.8},
                'steps': gauge_bg_colors,
                'threshold': {
                    'line': {'color': threshold_color, 'width': 4},
                    'thickness': 0.75,
                    'value': 25  # Maintenance margin typical level
                }
            },
            number={'suffix': "%", 'valueformat': '.1f', 'font': {'size': 20, 'color': text_color}}
        ),
        row=1, col=2
    )
    
    # 3. ETF Price vs Margin Call Price with filled areas
    if not active_positions.empty:
        # Add filled area between ETF Price and Margin Call Price
        for i in range(len(active_positions)):
            if i == 0:
                continue
            
            prev_date = active_positions.index[i-1]
            curr_date = active_positions.index[i]
            prev_etf = active_positions['ETF_Price'].iloc[i-1]
            curr_etf = active_positions['ETF_Price'].iloc[i]
            prev_margin = active_positions['Break_Even_Price'].iloc[i-1]
            curr_margin = active_positions['Break_Even_Price'].iloc[i]
            
            # Determine fill color based on whether ETF price is above or below margin call price
            if curr_etf > curr_margin:
                fill_color = safe_fill if use_dark_theme else 'rgba(39, 174, 96, 0.2)'  # Light green
                safety_status = 'Safe'
            else:
                fill_color = critical_fill if use_dark_theme else 'rgba(231, 76, 60, 0.2)'  # Light red
                safety_status = 'Margin Call Risk'
            
            # Add filled area
            fig.add_trace(
                go.Scatter(
                    x=[prev_date, curr_date, curr_date, prev_date],
                    y=[prev_etf, curr_etf, curr_margin, prev_margin],
                    fill='toself',
                    fillcolor=fill_color,
                    line=dict(color='rgba(255,255,255,0)'),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=2, col=1
            )
        
        # Add ETF Price line
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['ETF_Price'],
                mode='lines',
                name='ETF Price',
                line=dict(color=primary_line_color, width=3),
                hovertemplate='Date: %{x}<br>ETF Price: $%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add Margin Call Price line
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Break_Even_Price'],
                mode='lines',
                name='Margin Call Price',
                line=dict(color=secondary_line_color, width=3),
                hovertemplate='Date: %{x}<br>Margin Call Price: $%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # 4. Portfolio Value Drop Required (Percentage)
    if not active_positions.empty:
        # Create risk-based coloring for portfolio drop percentages
        portfolio_drop_colors = []
        for drop_pct in active_positions['Portfolio_Drop_Required_Percentage']:
            if drop_pct >= 30:
                portfolio_drop_colors.append(safe_color)  # Green - Safe
            elif drop_pct >= 15:
                portfolio_drop_colors.append(caution_color)  # Yellow - Caution
            elif drop_pct >= 5:
                portfolio_drop_colors.append(warning_color)  # Orange - Warning
            else:
                portfolio_drop_colors.append(critical_color)  # Red - Critical
        
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Portfolio_Drop_Required_Percentage'],
                mode='lines+markers',
                name='Portfolio Drop Required (%)',
                line=dict(color=tertiary_line_color, width=2),
                marker=dict(size=4, color=portfolio_drop_colors),
                fill='tozeroy',
                fillcolor=f'rgba({int(quaternary_line_color[1:3], 16)}, {int(quaternary_line_color[3:5], 16)}, {int(quaternary_line_color[5:7], 16)}, 0.2)',
                hovertemplate='Date: %{x}<br>Drop Required: %{y:.1f}%<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Add threshold lines
        fig.add_trace(
            go.Scatter(
                x=[active_positions.index[0], active_positions.index[-1]],
                y=[30, 30],
                mode='lines',
                line=dict(color=safe_color, width=2, dash='dash'),
                name='Safe Threshold (30%)',
                showlegend=False,
                hovertemplate='Safe Threshold: 30%<extra></extra>'
            ),
            row=2, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=[active_positions.index[0], active_positions.index[-1]],
                y=[15, 15],
                mode='lines',
                line=dict(color=caution_color, width=2, dash='dash'),
                name='Caution Threshold (15%)',
                showlegend=False,
                hovertemplate='Caution Threshold: 15%<extra></extra>'
            ),
            row=2, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=[active_positions.index[0], active_positions.index[-1]],
                y=[5, 5],
                mode='lines',
                line=dict(color=critical_color, width=2, dash='dash'),
                name='Critical Threshold (5%)',
                showlegend=False,
                hovertemplate='Critical Threshold: 5%<extra></extra>'
            ),
            row=2, col=2
        )
    
    # 5. Cushion dollar buffer
    if not active_positions.empty:
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Cushion_Dollars'],
                mode='lines+markers',
                name='Cushion Buffer',
                line=dict(color=tertiary_line_color, width=2),
                marker=dict(size=3),
                fill='tozeroy',
                fillcolor='rgba(22, 160, 133, 0.2)',
                hovertemplate='Date: %{x}<br>Cushion Buffer: $%{y:,.0f}<extra></extra>'
            ),
            row=3, col=1
        )
    
    # 6. Portfolio Value Drop Required (Dollars)
    if not active_positions.empty:
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Portfolio_Drop_Required_Dollars'],
                mode='lines+markers',
                name='Portfolio Drop Required ($)',
                line=dict(color=critical_color, width=2),
                marker=dict(size=4),
                fill='tozeroy',
                fillcolor='rgba(231, 76, 60, 0.2)',
                hovertemplate='Date: %{x}<br>Drop Required: $%{y:,.0f}<extra></extra>'
            ),
            row=3, col=2
        )
    
    # 7. Break-even price analysis (enhanced)
    if not active_positions.empty:
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Break_Even_Price'],
                mode='lines',
                name='Break-Even Price',
                line=dict(color=secondary_line_color, width=2),
                hovertemplate='Date: %{x}<br>Break-Even Price: $%{y:.2f}<extra></extra>'
            ),
            row=4, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['ETF_Price'],
                mode='lines',
                name='Current ETF Price',
                line=dict(color=primary_line_color, width=2),
                hovertemplate='Date: %{x}<br>ETF Price: $%{y:.2f}<extra></extra>'
            ),
            row=4, col=1
        )
    
    # 8. Portfolio Value vs Loan Balance
    if not active_positions.empty:
        # Calculate portfolio value
        portfolio_value = active_positions['ETF_Price'] * active_positions['Shares_Held']
        
        # Add filled area between portfolio value and loan balance (equity)
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=portfolio_value,
                mode='lines',
                name='Portfolio Value',
                line=dict(color=primary_line_color, width=3),
                fill='tonexty',
                fillcolor='rgba(31, 119, 180, 0.2)',
                hovertemplate='Date: %{x}<br>Portfolio Value: $%{y:,.0f}<extra></extra>'
            ),
            row=4, col=2
        )
        
        # Add loan balance line
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Margin_Loan'],
                mode='lines',
                name='Loan Balance',
                line=dict(color=secondary_line_color, width=3),
                hovertemplate='Date: %{x}<br>Loan Balance: $%{y:,.0f}<extra></extra>'
            ),
            row=4, col=2
        )
        
        # Add fill area to show equity (space between portfolio value and loan)
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=portfolio_value,
                mode='lines',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                hoverinfo='skip',
                fill='tonexty',
                fillcolor='rgba(39, 174, 96, 0.15)',
                name='Equity Buffer'
            ),
            row=4, col=2
        )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"🛡️ Margin Cushion Risk Management Dashboard | Current Cushion: {current_cushion:.1f}%",
            'x': 0.5,
            'font': {'size': 18, 'color': title_color}
        },
        height=1200,
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)' if use_dark_theme else 'rgba(255,255,255,0.8)',
            bordercolor=grid_color,
            borderwidth=1,
            font=dict(color=text_color, size=11),
            x=1.02,
            y=1
        ),
        plot_bgcolor=plot_bg_color,
        paper_bgcolor=bg_color,
        font=dict(color=text_color, family='Arial, sans-serif'),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor=plot_bg_color,
            font_size=12,
            font_family='Arial, sans-serif',
            font_color=text_color,
            bordercolor=grid_color
        ),
        margin=dict(l=80, r=150, t=100, b=80)
    )
    
    # Update axes styling
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor=grid_color,
        tickfont=dict(color=text_color if use_dark_theme else '#666666', size=11),
        linecolor=grid_color,
        mirror=True
    )
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor=grid_color,
        tickfont=dict(color=text_color if use_dark_theme else '#666666', size=11),
        linecolor=grid_color,
        mirror=True
    )
    
    # Format specific axes
    fig.update_yaxes(tickformat='.1f', row=1, col=1, title_text="Cushion (%)", title_font_color=text_color)
    fig.update_yaxes(tickformat='$,.2f', row=2, col=1, title_text="Price ($)", title_font_color=text_color)
    fig.update_yaxes(tickformat='.1f', row=2, col=2, title_text="Drop Required (%)", title_font_color=text_color)
    fig.update_yaxes(tickformat='$,.0f', row=3, col=1, title_text="Cushion Buffer ($)", title_font_color=text_color)
    fig.update_yaxes(tickformat='$,.0f', row=3, col=2, title_text="Drop Required ($)", title_font_color=text_color)
    fig.update_yaxes(tickformat='$,.2f', row=4, col=1, title_text="Price ($)", title_font_color=text_color)
    fig.update_yaxes(tickformat='$,.0f', row=4, col=2, title_text="Value ($)", title_font_color=text_color)
    
    # Update subplot titles with theme colors
    for annotation in fig['layout']['annotations']:
        if annotation['text'] in [
            'Margin Cushion Over Time', 'Real-Time Cushion Gauge',
            'ETF Price vs Margin Call Price', 'Portfolio Value Drop Required (%)',
            'Cushion Dollar Buffer', 'Portfolio Value Drop Required ($)',
            'Break-Even Price Analysis', 'Portfolio Value vs Loan Balance'
        ]:
            annotation['font']['color'] = text_color
            annotation['font']['size'] = 14 if use_dark_theme else 13
    
    return fig

def render_cushion_analytics_section(results_df: pd.DataFrame, metrics: Dict[str, float], mode: str = "liquidation_reentry", use_dark_theme: bool = True):
    """Render the complete cushion analytics section for Streamlit"""
    
    st.markdown("### 🛡️ Margin Cushion Risk Management Dashboard")
    
    # Handle different backtest modes - some don't have 'In_Position' column
    if 'In_Position' in results_df.columns:
        active_positions = results_df[results_df['In_Position'] == True]
    else:
        # For constant leverage mode, consider positions active when shares are held
        active_positions = results_df[results_df['Shares_Held'] > 0]
    
    if not active_positions.empty:
        # Calculate current cushion metrics
        current_cushion_pct = ((active_positions['Equity'].iloc[-1] - active_positions['Maintenance_Margin_Required'].iloc[-1]) / active_positions['Maintenance_Margin_Required'].iloc[-1]) * 100 if active_positions['Maintenance_Margin_Required'].iloc[-1] > 0 else 0
        current_cushion_dollars = active_positions['Equity'].iloc[-1] - active_positions['Maintenance_Margin_Required'].iloc[-1]
        days_to_margin_call = current_cushion_dollars / active_positions['Daily_Interest_Cost'].iloc[-1] if active_positions['Daily_Interest_Cost'].iloc[-1] > 0 else float('inf')
        
        # Calculate portfolio drop requirements
        current_portfolio_value = active_positions['ETF_Price'].iloc[-1] * active_positions['Shares_Held'].iloc[-1]
        break_even_price = active_positions['Margin_Loan'].iloc[-1] / (active_positions['Shares_Held'].iloc[-1] * 0.75) if active_positions['Shares_Held'].iloc[-1] > 0 else 0
        portfolio_drop_dollars = (active_positions['ETF_Price'].iloc[-1] - break_even_price) * active_positions['Shares_Held'].iloc[-1] if active_positions['Shares_Held'].iloc[-1] > 0 else 0
        portfolio_drop_percentage = (portfolio_drop_dollars / current_portfolio_value) * 100 if current_portfolio_value > 0 else 0
        
        # Risk zone classification
        if current_cushion_pct >= 50:
            risk_level = "🟢 SAFE ZONE"
        elif current_cushion_pct >= 20:
            risk_level = "🟡 CAUTION ZONE"
        elif current_cushion_pct >= 5:
            risk_level = "🟠 WARNING ZONE"
        else:
            risk_level = "🔴 CRITICAL ZONE"
        
        # Display current cushion status
        cushion_col1, cushion_col2, cushion_col3, cushion_col4 = st.columns(4)
        
        with cushion_col1:
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Current Cushion</div>
                <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{current_cushion_pct:.1f}%</div>
                <div style="color: #a0a0a0; font-size: 0.9rem;">{risk_level}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cushion_col2:
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Cushion Buffer</div>
                <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${current_cushion_dollars:,.0f}</div>
                <div style="color: #a0a0a0; font-size: 0.9rem;">Safety margin above requirement</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cushion_col3:
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Portfolio Drop Tolerance</div>
                <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{portfolio_drop_percentage:.1f}%</div>
                <div style="color: #a0a0a0; font-size: 0.9rem;">Market decline tolerance</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cushion_col4:
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Portfolio Drop Buffer</div>
                <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${portfolio_drop_dollars:,.0f}</div>
                <div style="color: #a0a0a0; font-size: 0.9rem;">Dollar decline tolerance</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Add spacing before risk assessment messages
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Mode-specific risk assessment messages
        if mode == "fresh_capital":
            if current_cushion_pct < 20:
                st.error(f"""
                🚨 **{risk_level} - Fresh Capital Mode**: Current position cushion at {current_cushion_pct:.1f}%. 
                With fresh capital strategy, this position will liquidate and restart with ${metrics.get('Fresh Capital Per Round ($)', 0):,.0f} in fresh capital.
                Portfolio can tolerate {portfolio_drop_percentage:.1f}% decline (${portfolio_drop_dollars:,.0f})
                """)
            elif current_cushion_pct < 50:
                st.warning(f"""
                ⚠️ **{risk_level} - Fresh Capital Mode**: Monitor position closely. Cushion: {current_cushion_pct:.1f}% 
                Portfolio drop tolerance: {portfolio_drop_percentage:.1f}% (${portfolio_drop_dollars:,.0f}) before fresh capital restart
                """)
            else:
                st.success(f"""
                ✅ **{risk_level} - Fresh Capital Mode**: Healthy margin cushion at {current_cushion_pct:.1f}%. 
                Strong drop tolerance: {portfolio_drop_percentage:.1f}% (${portfolio_drop_dollars:,.0f}) provides good protection before fresh capital restart.
                """)
        else:
            if current_cushion_pct < 20:
                st.error(f"""
                🚨 **{risk_level}**: Your margin cushion is at {current_cushion_pct:.1f}%. 
                Portfolio can only tolerate {portfolio_drop_percentage:.1f}% decline (${portfolio_drop_dollars:,.0f}) before margin call.
                """)
            elif current_cushion_pct < 50:
                st.warning(f"""
                ⚠️ **{risk_level}**: Monitor position closely. Cushion: {current_cushion_pct:.1f}% 
                Portfolio drop tolerance: {portfolio_drop_percentage:.1f}% (${portfolio_drop_dollars:,.0f}) before margin call
                """)
            else:
                st.success(f"""
                ✅ **{risk_level}**: Healthy margin cushion at {current_cushion_pct:.1f}%. 
                Strong drop tolerance: {portfolio_drop_percentage:.1f}% (${portfolio_drop_dollars:,.0f}) provides good protection.
                """)
    else:
        mode_text = "Fresh Capital Mode" if mode == "fresh_capital" else ""
        st.info(f"📊 **Cushion Analysis {mode_text}**: No active positions to analyze. Cushion metrics available when in leveraged positions.")
    
    # Display the comprehensive cushion dashboard
    cushion_fig = create_cushion_analytics_dashboard(results_df, metrics, use_dark_theme)
    st.plotly_chart(cushion_fig, use_container_width=True)
    
    # Educational expander
    if not active_positions.empty:
        # Add custom CSS for gray background in expander content AND header
        st.markdown("""
        <style>
        /* Style the expander header/box itself with gray background */
        div[data-testid="stExpander"] {
            background-color: #404040 !important;
            border: 1px solid #606060 !important;
            border-radius: 8px !important;
            margin: 0.5rem 0 !important;
            padding: 0 !important;
        }
        
        /* Style the expander header (clickable part) */
        div[data-testid="stExpander"] > details > summary {
            background-color: #404040 !important;
            color: #ffffff !important;
            padding: 0.75rem 1rem !important;
            border-radius: 8px 8px 0 0 !important;
            cursor: pointer !important;
            font-weight: 600 !important;
        }
        
        /* Style the expander header when closed (full rounded corners) */
        div[data-testid="stExpander"]:not([open]) > details > summary {
            border-radius: 8px !important;
        }
        
        /* Style the expander arrow icon */
        div[data-testid="stExpander"] details summary::-webkit-details-marker {
            color: #ff8c00 !important;
        }
        
        /* Target the specific expander content area and apply gray background */
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
            background-color: #404040 !important;
            color: #ffffff !important;
            padding: 1rem !important;
            border-radius: 0 0 8px 8px !important;
            margin-top: 0 !important;
            border-top: 1px solid #606060 !important;
        }
        
        /* Ensure all text inside expander is white for contrast */
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] * {
            color: #ffffff !important;
        }
        
        /* Style headers inside expander */
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] h1,
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] h2,
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] h3 {
            color: #ff8c00 !important;
        }
        
        /* Style bullet points and list items */
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] ul,
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] li {
            color: #ffffff !important;
        }
        
        /* Style code blocks for better contrast */
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] code {
            background-color: #606060 !important;
            color: #ffff00 !important;
            padding: 2px 4px !important;
            border-radius: 3px !important;
        }
        
        /* Style strong/bold text */
        div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] strong {
            color: #ffa500 !important;
        }
        
        /* Hover effect for expander header */
        div[data-testid="stExpander"] > details > summary:hover {
            background-color: #505050 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.expander("💡 Cushion Strategy Insights & Risk Management", expanded=False):
            if mode == "fresh_capital":
                st.markdown(f"""
                ### 🛡️ Fresh Capital Cushion Analysis
                
                **Fresh Capital Mode Cushion Behavior:**
                - **Same Cushion Calculations**: Risk zones apply identically to individual positions
                - **Unlimited Restart Capital**: Each liquidation triggers fresh ${metrics.get('Fresh Capital Per Round ($)', 0):,.0f} deployment
                - **Pattern Recognition**: Shows optimal timing and frequency for position entries
                - **Capital Efficiency**: Evaluate if fresh capital strategy is sustainable
                
                **Risk Zones Explained (Fresh Capital Context):**
                - 🟢 **Safe Zone (50%+)**: Position stable, fresh capital not needed soon
                - 🟡 **Caution Zone (20-50%)**: Monitor for restart timing, fresh capital on standby
                - 🟠 **Warning Zone (5-20%)**: Fresh capital restart likely within days
                - 🔴 **Critical Zone (<5%)**: Fresh capital restart imminent
                """)
            elif mode == "constant_leverage":
                st.markdown("""
                ### 🛡️ Constant Leverage Cushion Analysis
                
                **Constant Leverage Mode Cushion Behavior:**
                - **Dynamic Position Sizing**: Cushion changes as positions are rebalanced to maintain target leverage
                - **Rebalancing Impact**: Each rebalance adjusts position size, affecting cushion levels
                - **Leverage Maintenance**: System automatically borrows more when equity increases
                - **Cost Considerations**: Transaction costs from rebalancing affect overall cushion
                
                **Risk Zones Explained (Constant Leverage Context):**
                - 🟢 **Safe Zone (50%+)**: Healthy cushion, rebalancing can proceed normally
                - 🟡 **Caution Zone (20-50%)**: Monitor rebalancing costs and frequency
                - 🟠 **Warning Zone (5-20%)**: Consider reducing target leverage or rebalancing frequency
                - 🔴 **Critical Zone (<5%)**: Immediate risk of forced liquidation despite rebalancing
                """)
            else:
                st.markdown("""
                ### 🛡️ Understanding Margin Cushion
                
                **What is Margin Cushion?**
                - **Cushion Percentage**: How much your equity exceeds the minimum maintenance requirement
                - **Buffer Dollars**: Actual dollar amount of protection above margin call level
                - **Days to Margin Call**: Time until interest costs erode your cushion (assuming no price movement)
                
                **Risk Zones Explained:**
                - 🟢 **Safe Zone (50%+)**: Strong protection, comfortable leverage level
                - 🟡 **Caution Zone (20-50%)**: Moderate risk, monitor daily, consider position reduction
                - 🟠 **Warning Zone (5-20%)**: High risk, immediate attention required
                - 🔴 **Critical Zone (<5%)**: Margin call imminent, emergency action needed
                
                **Emergency Protocols:**
                - **<20% Cushion**: Consider partial position reduction immediately
                - **<10% Cushion**: Reduce position by 50% or add capital within 24 hours
                - **<5% Cushion**: Close position immediately or face forced liquidation
                
                ### 📊 Detailed Plot Explanations
                
                **🔶 Plot 1: Margin Cushion Over Time**
                
                This plot shows your margin cushion percentage evolution throughout the backtest period. The cushion percentage is calculated as:
                
                `(Current Equity - Maintenance Margin Required) / Maintenance Margin Required × 100`
                
                **Data Sources:**
                - **Equity**: Daily portfolio equity from backtest calculations (Portfolio Value - Margin Loan)
                - **Maintenance Margin Required**: 25% of portfolio value for Reg-T accounts, 15% for Portfolio Margin
                - **Color Coding**: Green (Safe >50%), Yellow (Caution 20-50%), Orange (Warning 5-20%), Red (Critical <5%)
                
                **Key Insights:**
                - **Trend Analysis**: Declining cushion indicates increasing risk from interest erosion or adverse price movement
                - **Risk Zone Transitions**: Watch for periods spent in warning/critical zones
                - **Volatility Impact**: Sharp drops reveal portfolio sensitivity to market movements
                - **Interest Erosion**: Gradual decline shows cumulative impact of daily interest costs
                
                **🔶 Plot 2: Real-Time Cushion Gauge**
                
                This gauge displays your current margin cushion as a speedometer-style indicator with color-coded risk zones.
                
                **Data Sources:**
                - **Current Value**: Latest cushion percentage from active position data
                - **Reference Point**: 50% (Safe Zone threshold) used as benchmark
                - **Background Zones**: Visual representation of the four risk categories
                
                **Key Insights:**
                - **Instant Risk Assessment**: Quick visual of current risk level
                - **Threshold Monitoring**: Black line shows typical maintenance margin level (25%)
                - **Delta Indicator**: Shows difference from 50% safe threshold
                - **Action Trigger**: Red zone (<5%) indicates immediate liquidation risk
                
                **🔶 Plot 3: ETF Price vs Margin Call Price**
                
                This innovative plot shows the relationship between current ETF price and the critical margin call price, with dynamic color-filled areas indicating safety zones.
                
                **Data Sources:**
                - **ETF Price**: Current market price of the leveraged ETF
                - **Margin Call Price**: `Margin Loan / (Shares Held × (1 - Maintenance Margin %))`
                - **Fill Areas**: Light green when ETF > Margin Call Price (Safe), Light red when below (Danger)
                
                **Key Insights:**
                - **Visual Safety Assessment**: Instantly see if you're in safe territory or approaching danger
                - **Price Relationship**: Track how the gap between prices changes over time
                - **Risk Visualization**: Color zones make it immediately clear when positions are at risk
                - **Trend Monitoring**: Watch for converging lines indicating increasing vulnerability
                
                **🔶 Plot 4: Portfolio Value Drop Required (%)**
                
                This plot shows what percentage your portfolio value needs to drop to trigger a margin call, with color-coded risk thresholds.
                
                **Data Sources:**
                - **Calculation**: `(ETF Price - Margin Call Price) / ETF Price × 100`
                - **Risk Thresholds**: 30% (Safe), 15% (Caution), 5% (Critical)
                - **Color Coding**: Green markers for safe positions, red for critical
                
                **Key Insights:**
                - **Drop Tolerance**: Shows how much market decline you can absorb
                - **Risk Assessment**: Higher percentages indicate more resilient positions
                - **Threshold Alerts**: Visual warnings when drop tolerance becomes dangerous
                - **Position Sizing**: Use to determine appropriate leverage levels
                
                **🔶 Plot 5: Cushion Dollar Buffer**
                
                This area chart displays the absolute dollar amount of your margin cushion buffer over time.
                
                **Data Sources:**
                - **Cushion Buffer**: `Current Equity - Maintenance Margin Required`
                - **Daily Tracking**: Shows buffer erosion from interest costs and market movements
                - **Fill Area**: Visual representation of protective capital above minimum
                
                **Key Insights:**
                - **Absolute Protection**: Dollar amount available to absorb losses
                - **Erosion Rate**: Declining area shows speed of buffer depletion
                - **Position Scale**: Larger positions require proportionally larger buffers
                - **Capital Efficiency**: Evaluate if buffer size justifies position risk
                
                **🔶 Plot 6: Portfolio Value Drop Required ($)**
                
                This plot shows the absolute dollar amount your portfolio can drop before hitting a margin call.
                
                **Data Sources:**
                - **Calculation**: `(ETF Price - Margin Call Price) × Shares Held`
                - **Dollar Protection**: Actual dollar buffer available for market declines
                - **Position Scaling**: Larger positions show proportionally larger dollar buffers
                
                **Key Insights:**
                - **Dollar Risk Tolerance**: Exact amount you can lose before margin call
                - **Position Sizing**: Compare to typical daily dollar volatility
                - **Capital Planning**: Use for risk budgeting and position management
                - **Loss Capacity**: Understand maximum sustainable drawdown
                
                **🔶 Plot 7: Break-Even Price Analysis**
                
                This dual-line plot compares the current ETF price with the calculated break-even price that would trigger a margin call.
                
                **Data Sources:**
                - **Current ETF Price**: Daily closing prices from market data
                - **Break-Even Price**: `Margin Loan / (Shares Held × (1 - Maintenance Margin %))`
                - **Price Gap**: Distance between current and break-even prices
                
                **Key Insights:**
                - **Price Risk**: Shows exact price level that triggers liquidation
                - **Safety Margin**: Gap between lines indicates price drop protection
                - **Trend Analysis**: Converging lines indicate increasing vulnerability
                - **Volatility Assessment**: Compare gap to typical daily price ranges
                
                **🔶 Plot 8: Portfolio Value vs Loan Balance**
                
                This fundamental plot shows the relationship between your total portfolio value and outstanding loan balance, with the gap representing your equity.
                
                **Data Sources:**
                - **Portfolio Value**: `ETF Price × Shares Held`
                - **Loan Balance**: Outstanding margin debt from leveraged positions
                - **Equity Gap**: Visual area between lines showing actual equity
                - **Fill Colors**: Light blue for portfolio value, light green for equity buffer
                
                **Key Insights:**
                - **Equity Visualization**: Green area shows your actual equity buffer
                - **Leverage Assessment**: Closer lines indicate higher leverage ratios
                - **Risk Monitoring**: Converging lines show increasing leverage risk
                - **Fundamental Analysis**: Core relationship driving all margin calculations
                
                **📈 Advanced Portfolio Risk Metrics:**
                
                **Portfolio Drop Requirements:**
                - **Percentage Drop**: Shows market decline tolerance as a percentage
                - **Dollar Drop**: Shows absolute dollar amount of decline tolerance
                - **Combined Analysis**: Use both metrics for comprehensive risk assessment
                - **Position Sizing**: Larger positions amplify both percentage and dollar impacts
                
                **Portfolio Value Analysis:**
                - **ETF vs Margin Call Price**: Direct comparison of current vs critical prices
                - **Dynamic Visualization**: Color-filled areas show safety zones in real-time
                - **Portfolio vs Loan Balance**: Fundamental relationship showing equity evolution
                - **Equity Buffer Tracking**: Visual representation of actual equity protection
                
                **Risk Integration:**
                - **Multi-Perspective Analysis**: Each plot shows different aspects of the same risk
                - **Cross-Validation**: Use multiple plots to confirm risk assessments
                - **Action Triggers**: Multiple visualizations make it clear when action is needed
                - **Comprehensive Coverage**: From high-level percentages to detailed dollar amounts
                """)

def is_cushion_analytics_available() -> bool:
    """Check if cushion analytics module is properly loaded"""
    return True

# Module initialization message (optional, for debugging)
def get_module_info() -> Dict[str, str]:
    """Return module information"""
    return {
        "name": "Cushion Analytics",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "status": "Loaded and Ready"
    }
