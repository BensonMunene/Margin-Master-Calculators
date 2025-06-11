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

def create_cushion_analytics_dashboard(df_results: pd.DataFrame, metrics: Dict[str, float]) -> go.Figure:
    """Create comprehensive margin cushion analytics dashboard"""
    
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
    
    # Calculate days to margin call at current interest rate (assuming no price movement)
    df_cushion['Daily_Interest_Rate'] = df_cushion['Margin_Rate'] / 100 / 365
    df_cushion['Days_To_Margin_Call'] = np.where(
        (df_cushion['Daily_Interest_Cost'] > 0) & (df_cushion['Cushion_Dollars'] > 0),
        df_cushion['Cushion_Dollars'] / df_cushion['Daily_Interest_Cost'],
        np.inf
    )
    
    # Calculate break-even price (price at which margin call would trigger)
    df_cushion['Break_Even_Price'] = np.where(
        df_cushion['Shares_Held'] > 0,
        df_cushion['Margin_Loan'] / (df_cushion['Shares_Held'] * (1 - (metrics.get('maintenance_margin_pct', 25) / 100))),
        0
    )
    
    # Create color mapping for risk zones
    def get_cushion_color(cushion_pct):
        if cushion_pct >= 50:
            return '#27AE60'  # Green - Safe
        elif cushion_pct >= 20:
            return '#F39C12'  # Yellow - Caution
        elif cushion_pct >= 5:
            return '#E67E22'  # Orange - Warning
        else:
            return '#E74C3C'  # Red - Critical
    
    # Apply color mapping
    df_cushion['Risk_Color'] = df_cushion['Cushion_Percentage'].apply(get_cushion_color)
    
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Margin Cushion Over Time', 'Real-Time Cushion Gauge',
            'Days to Margin Call Timeline', 'Break-Even Price Analysis',
            'Cushion Dollar Buffer', 'Interest Rate Impact on Cushion'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "indicator"}],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )
    
    # 1. Cushion percentage over time with risk zones
    active_positions = df_cushion[df_cushion['In_Position'] == True]
    if not active_positions.empty:
        # Create separate traces for different risk levels for better visualization
        for risk_level, color in [('Safe (>50%)', '#27AE60'), ('Caution (20-50%)', '#F39C12'), 
                                 ('Warning (5-20%)', '#E67E22'), ('Critical (<5%)', '#E74C3C')]:
            if risk_level == 'Safe (>50%)':
                mask = active_positions['Cushion_Percentage'] >= 50
            elif risk_level == 'Caution (20-50%)':
                mask = (active_positions['Cushion_Percentage'] >= 20) & (active_positions['Cushion_Percentage'] < 50)
            elif risk_level == 'Warning (5-20%)':
                mask = (active_positions['Cushion_Percentage'] >= 5) & (active_positions['Cushion_Percentage'] < 20)
            else:  # Critical
                mask = active_positions['Cushion_Percentage'] < 5
            
            if mask.any():
                filtered_data = active_positions[mask]
                fig.add_trace(
                    go.Scatter(
                        x=filtered_data.index,
                        y=filtered_data['Cushion_Percentage'],
                        mode='markers+lines',
                        name=risk_level,
                        line=dict(color=color, width=2),
                        marker=dict(color=color, size=4),
                        hovertemplate=f'{risk_level}<br>Date: %{{x}}<br>Cushion: %{{y:.1f}}%<extra></extra>'
                    ),
                    row=1, col=1
                )
        
        # Add horizontal risk zone lines as scatter traces
        if not active_positions.empty:
            x_range = [active_positions.index[0], active_positions.index[-1]]
            
            # Safe zone line (50%)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[50, 50],
                    mode='lines',
                    line=dict(color='#27AE60', width=2, dash='dash'),
                    name='Safe Zone (50%)',
                    showlegend=False,
                    hovertemplate='Safe Zone: 50%<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Caution zone line (20%)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[20, 20],
                    mode='lines',
                    line=dict(color='#F39C12', width=2, dash='dash'),
                    name='Caution Zone (20%)',
                    showlegend=False,
                    hovertemplate='Caution Zone: 20%<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Critical zone line (5%)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=[5, 5],
                    mode='lines',
                    line=dict(color='#E74C3C', width=2, dash='dash'),
                    name='Critical Zone (5%)',
                    showlegend=False,
                    hovertemplate='Critical Zone: 5%<extra></extra>'
                ),
                row=1, col=1
            )
    
    # 2. Current cushion gauge (using last available data)
    current_cushion = active_positions['Cushion_Percentage'].iloc[-1] if not active_positions.empty else 0
    gauge_color = get_cushion_color(current_cushion)
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=current_cushion,
            delta={'reference': 50, 'valueformat': '.1f'},
            title={'text': "Current Margin Cushion", 'font': {'size': 16}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100], 'tickformat': '.0f'},
                'bar': {'color': gauge_color, 'thickness': 0.8},
                'steps': [
                    {'range': [0, 5], 'color': "#FADBD8"},      # Critical zone
                    {'range': [5, 20], 'color': "#FCF3CF"},     # Warning zone  
                    {'range': [20, 50], 'color': "#FEF9E7"},    # Caution zone
                    {'range': [50, 100], 'color': "#EAFAF1"}    # Safe zone
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 25  # Maintenance margin typical level
                }
            },
            number={'suffix': "%", 'valueformat': '.1f', 'font': {'size': 20}}
        ),
        row=1, col=2
    )
    
    # 3. Days to margin call timeline
    if not active_positions.empty:
        # Cap extremely high values for better visualization
        capped_days = np.minimum(active_positions['Days_To_Margin_Call'], 1000)
        
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=capped_days,
                mode='lines+markers',
                name='Days to Margin Call',
                line=dict(color='#8E44AD', width=2),
                marker=dict(size=3),
                hovertemplate='Date: %{x}<br>Days to Margin Call: %{y:.0f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add warning zones as scatter traces (since add_hline doesn't work with indicator subplots nearby)
        fig.add_trace(
            go.Scatter(
                x=[active_positions.index[0], active_positions.index[-1]],
                y=[30, 30],
                mode='lines',
                line=dict(color='#E74C3C', width=2, dash='dash'),
                name='30-Day Warning',
                showlegend=False,
                hovertemplate='30-Day Warning Line<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=[active_positions.index[0], active_positions.index[-1]],
                y=[90, 90],
                mode='lines',
                line=dict(color='#F39C12', width=2, dash='dash'),
                name='90-Day Caution',
                showlegend=False,
                hovertemplate='90-Day Caution Line<extra></extra>'
            ),
            row=2, col=1
        )
    
    # 4. Break-even price analysis
    if not active_positions.empty:
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Break_Even_Price'],
                mode='lines',
                name='Break-Even Price',
                line=dict(color='#DC3545', width=2, dash='dash'),
                hovertemplate='Date: %{x}<br>Break-Even Price: $%{y:.2f}<extra></extra>'
            ),
            row=2, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['ETF_Price'],
                mode='lines',
                name='Current ETF Price',
                line=dict(color='#1f77b4', width=2),
                hovertemplate='Date: %{x}<br>ETF Price: $%{y:.2f}<extra></extra>'
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
                line=dict(color='#16A085', width=2),
                marker=dict(size=3),
                fill='tozeroy',
                fillcolor='rgba(22, 160, 133, 0.2)',
                hovertemplate='Date: %{x}<br>Cushion Buffer: $%{y:,.0f}<extra></extra>'
            ),
            row=3, col=1
        )
    
    # 6. Interest rate impact on cushion erosion
    if not active_positions.empty:
        # Calculate cushion erosion rate (daily interest as % of cushion)
        cushion_erosion_rate = np.where(
            active_positions['Cushion_Dollars'] > 0,
            (active_positions['Daily_Interest_Cost'] / active_positions['Cushion_Dollars']) * 100,
            0
        )
        
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=cushion_erosion_rate,
                mode='lines+markers',
                name='Daily Cushion Erosion Rate',
                line=dict(color='#E74C3C', width=2),
                marker=dict(size=3),
                hovertemplate='Date: %{x}<br>Daily Erosion: %{y:.3f}%<extra></extra>'
            ),
            row=3, col=2
        )
        
        # Add margin rate for comparison (on same axis, different scale handled in layout)
        fig.add_trace(
            go.Scatter(
                x=active_positions.index,
                y=active_positions['Margin_Rate'],
                mode='lines',
                name='Annual Margin Rate',
                line=dict(color='#8E44AD', width=2, dash='dot'),
                hovertemplate='Date: %{x}<br>Margin Rate: %{y:.2f}%<extra></extra>'
            ),
            row=3, col=2
        )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"🛡️ Margin Cushion Risk Management Dashboard | Current Cushion: {current_cushion:.1f}%",
            'x': 0.5,
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        height=900,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    # Update axes styling
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    
    # Format specific axes
    fig.update_yaxes(tickformat='.1f', row=1, col=1, title_text="Cushion (%)")
    fig.update_yaxes(tickformat='.0f', row=2, col=1, title_text="Days")
    fig.update_yaxes(tickformat='$,.2f', row=2, col=2, title_text="Price ($)")
    fig.update_yaxes(tickformat='$,.0f', row=3, col=1, title_text="Cushion Buffer ($)")
    fig.update_yaxes(tickformat='.3f', row=3, col=2, title_text="Erosion Rate (%/day)")
    
    return fig

def render_cushion_analytics_section(results_df: pd.DataFrame, metrics: Dict[str, float], mode: str = "liquidation_reentry"):
    """Render the complete cushion analytics section for Streamlit"""
    
    st.markdown("### 🛡️ Margin Cushion Risk Management Dashboard")
    
    active_positions = results_df[results_df['In_Position'] == True]
    
    if not active_positions.empty:
        # Calculate current cushion metrics
        current_cushion_pct = ((active_positions['Equity'].iloc[-1] - active_positions['Maintenance_Margin_Required'].iloc[-1]) / active_positions['Maintenance_Margin_Required'].iloc[-1]) * 100 if active_positions['Maintenance_Margin_Required'].iloc[-1] > 0 else 0
        current_cushion_dollars = active_positions['Equity'].iloc[-1] - active_positions['Maintenance_Margin_Required'].iloc[-1]
        days_to_margin_call = current_cushion_dollars / active_positions['Daily_Interest_Cost'].iloc[-1] if active_positions['Daily_Interest_Cost'].iloc[-1] > 0 else float('inf')
        
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
            st.metric(
                "Current Cushion",
                f"{current_cushion_pct:.1f}%",
                delta=risk_level
            )
        
        with cushion_col2:
            st.metric(
                "Cushion Buffer",
                f"${current_cushion_dollars:,.0f}",
                delta="Safety margin above requirement"
            )
        
        with cushion_col3:
            days_display = f"{days_to_margin_call:.0f}" if days_to_margin_call != float('inf') else "∞"
            st.metric(
                "Days to Margin Call",
                days_display,
                delta="At current interest rate"
            )
        
        with cushion_col4:
            break_even_price = active_positions['Margin_Loan'].iloc[-1] / (active_positions['Shares_Held'].iloc[-1] * 0.75) if active_positions['Shares_Held'].iloc[-1] > 0 else 0
            current_price = active_positions['ETF_Price'].iloc[-1]
            price_buffer = ((current_price - break_even_price) / current_price) * 100 if current_price > 0 else 0
            st.metric(
                "Price Drop Buffer",
                f"{price_buffer:.1f}%",
                delta=f"Break-even: ${break_even_price:.2f}"
            )
        
        # Mode-specific risk assessment messages
        if mode == "fresh_capital":
            if current_cushion_pct < 20:
                st.error(f"""
                🚨 **{risk_level} - Fresh Capital Mode**: Current position cushion at {current_cushion_pct:.1f}%. 
                With fresh capital strategy, this position will liquidate and restart with ${metrics.get('Fresh Capital Per Round ($)', 0):,.0f} in fresh capital.
                Current buffer: ${current_cushion_dollars:,.0f}
                """)
            elif current_cushion_pct < 50:
                st.warning(f"""
                ⚠️ **{risk_level} - Fresh Capital Mode**: Monitor position closely. Cushion: {current_cushion_pct:.1f}% 
                Buffer: ${current_cushion_dollars:,.0f} • Est. days to fresh capital restart: {days_display}
                """)
            else:
                st.success(f"""
                ✅ **{risk_level} - Fresh Capital Mode**: Healthy margin cushion at {current_cushion_pct:.1f}%. 
                Strong buffer: ${current_cushion_dollars:,.0f} provides good protection before fresh capital restart.
                """)
        else:
            if current_cushion_pct < 20:
                st.error(f"""
                🚨 **{risk_level}**: Your margin cushion is at {current_cushion_pct:.1f}%. 
                Consider reducing position size or adding capital. Current buffer: ${current_cushion_dollars:,.0f}
                """)
            elif current_cushion_pct < 50:
                st.warning(f"""
                ⚠️ **{risk_level}**: Monitor position closely. Cushion: {current_cushion_pct:.1f}% 
                Buffer: ${current_cushion_dollars:,.0f} • Est. days to margin call: {days_display}
                """)
            else:
                st.success(f"""
                ✅ **{risk_level}**: Healthy margin cushion at {current_cushion_pct:.1f}%. 
                Strong buffer: ${current_cushion_dollars:,.0f} provides good protection.
                """)
    else:
        mode_text = "Fresh Capital Mode" if mode == "fresh_capital" else ""
        st.info(f"📊 **Cushion Analysis {mode_text}**: No active positions to analyze. Cushion metrics available when in leveraged positions.")
    
    # Display the comprehensive cushion dashboard
    cushion_fig = create_cushion_analytics_dashboard(results_df, metrics)
    st.plotly_chart(cushion_fig, use_container_width=True)
    
    # Educational expander
    if not active_positions.empty:
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
