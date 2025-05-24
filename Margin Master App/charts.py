import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def create_margin_what_if_chart(prices, reg_t_equity, portfolio_equity, liquidation_points, investment_amount):
    """
    Create an interactive "What-If" chart showing equity value across price scenarios
    
    Args:
        prices (list): List of price percentages
        reg_t_equity (list): List of equity values for Reg-T margin
        portfolio_equity (list): List of equity values for Portfolio margin
        liquidation_points (dict): Dictionary with liquidation points for each margin type
        investment_amount (float): Original investment amount for reference line
        
    Returns:
        plotly.graph_objects.Figure: Interactive chart
    """
    # Create figure
    fig = go.Figure()
    
    # Add traces for equity values
    fig.add_trace(go.Scatter(
        x=prices,
        y=reg_t_equity,
        mode='lines',
        name='Reg-T Margin',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='Price: %{x:.1f}%<br>Equity: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=prices,
        y=portfolio_equity,
        mode='lines',
        name='Portfolio Margin',
        line=dict(color='#2ca02c', width=3),
        hovertemplate='Price: %{x:.1f}%<br>Equity: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add reference line for original investment
    fig.add_trace(go.Scatter(
        x=[min(prices), max(prices)],
        y=[investment_amount, investment_amount],
        mode='lines',
        name='Initial Investment',
        line=dict(color='#7f7f7f', width=2, dash='dash'),
        hovertemplate='Initial Investment: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add vertical lines at liquidation points
    if liquidation_points['reg_t'] > 0:
        fig.add_vline(
            x=liquidation_points['reg_t'], 
            line_width=2, line_dash="dash", line_color="#d62728",
            annotation_text="Reg-T Margin Call",
            annotation_position="top right"
        )
    
    if liquidation_points['portfolio'] > 0:
        fig.add_vline(
            x=liquidation_points['portfolio'], 
            line_width=2, line_dash="dash", line_color="#ff7f0e",
            annotation_text="Portfolio Margin Call",
            annotation_position="bottom right"
        )
    
    # Update layout with better styling
    fig.update_layout(
        title={
            'text': 'What-If Price Scenario Analysis',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Price Relative to Purchase (%)',
        yaxis_title='Equity Value ($)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        template='plotly_white',
        hovermode="x unified",
        margin=dict(l=50, r=50, t=80, b=50),
        height=500
    )
    
    # Add light shaded background for margin call zone
    if min(liquidation_points.values()) > min(prices):
        fig.add_shape(
            type="rect",
            x0=min(prices), y0=0,
            x1=min(liquidation_points.values()), y1=max(max(reg_t_equity), max(portfolio_equity)),
            fillcolor="rgba(255, 0, 0, 0.1)",
            line_width=0,
            layer="below"
        )
    
    return fig

def create_danger_zone_gauge(cushion_percentage):
    """
    Create a semi-circular gauge showing safety zones
    
    Args:
        cushion_percentage (float): Current cushion percentage
        
    Returns:
        plotly.graph_objects.Figure: Gauge chart
    """
    # Map cushion percentage to a 0-180 scale for the gauge
    # -20% cushion or less is 0, 50% cushion or more is 180
    gauge_value = min(max((cushion_percentage + 20) * 3, 0), 180)
    
    # Determine color based on cushion percentage
    if cushion_percentage < 0:
        color = "#e74c3c"  # Red for negative cushion (margin call territory)
    elif cushion_percentage < 10:
        color = "#ff9800"  # Orange for low cushion
    else:
        color = "#2ecc71"  # Green for healthy cushion
    
    # Create the gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cushion_percentage,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Margin Cushion", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [-20, 50], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [-20, 0], 'color': 'rgba(231, 76, 60, 0.3)'},
                {'range': [0, 10], 'color': 'rgba(255, 152, 0, 0.3)'},
                {'range': [10, 50], 'color': 'rgba(46, 204, 113, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0
            }
        },
        number={
            'suffix': "%",
            'font': {'size': 28, 'color': color}
        }
    ))
    
    # Add text labels for the zones
    fig.add_annotation(x=0.15, y=0.4,
                    text="MARGIN CALL",
                    showarrow=False,
                    font=dict(size=12, color="red"))
    
    fig.add_annotation(x=0.5, y=0.4,
                    text="WARNING",
                    showarrow=False,
                    font=dict(size=12, color="orange"))
    
    fig.add_annotation(x=0.85, y=0.4,
                    text="SAFE",
                    showarrow=False,
                    font=dict(size=12, color="green"))
    
    # Update layout for cleaner appearance
    fig.update_layout(
        height=300,
        margin=dict(l=30, r=30, t=50, b=30),
    )
    
    return fig

def create_stress_test_chart(scenario, investment_amount, leverage_percentage, maintenance_margin_percentage):
    """
    Create chart showing equity under stress test scenario
    
    Args:
        scenario (dict): Scenario data including price changes
        investment_amount (float): Investment amount
        leverage_percentage (float): Leverage percentage
        maintenance_margin_percentage (float): Maintenance margin percentage
        
    Returns:
        plotly.graph_objects.Figure: Stress test chart
    """
    from calculations import calculate_maintenance_cushion
    
    # Generate data points
    price_changes = scenario['price_changes']
    timeframe_days = scenario['timeframe_days']
    
    # Calculate number of days per step (evenly distributed)
    days_per_step = timeframe_days / (len(price_changes) - 1) if len(price_changes) > 1 else 0
    days = [i * days_per_step for i in range(len(price_changes))]
    
    # Calculate equity and cushion at each price point
    equity_values = []
    cushion_values = []
    cushion_percentages = []
    
    for price_change in price_changes:
        current_price_percentage = 100 + price_change
        
        # Calculate equity (simplified)
        leverage_ratio = leverage_percentage / 100
        loan_amount = investment_amount * (1 - 1/leverage_ratio) if leverage_ratio > 1 else 0
        position_value = investment_amount * leverage_ratio * (current_price_percentage / 100)
        equity = position_value - loan_amount
        
        # Calculate cushion
        cushion_amount, cushion_pct = calculate_maintenance_cushion(
            investment_amount, 
            leverage_percentage,
            maintenance_margin_percentage,
            current_price_percentage
        )
        
        equity_values.append(equity)
        cushion_values.append(cushion_amount)
        cushion_percentages.append(cushion_pct)
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=days,
        y=equity_values,
        mode='lines+markers',
        name='Equity Value',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='Day: %{x:.0f}<br>Equity: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=days,
        y=cushion_values,
        mode='lines+markers',
        name='Margin Cushion',
        line=dict(color='#ff7f0e', width=3),
        hovertemplate='Day: %{x:.0f}<br>Cushion: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add zero line
    fig.add_shape(
        type="line",
        x0=0, y0=0,
        x1=max(days), y1=0,
        line=dict(color="red", width=2, dash="dash")
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f'Stress Test: {scenario["name"]}',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Day',
        yaxis_title='Value ($)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        template='plotly_white',
        hovermode="x unified",
        margin=dict(l=50, r=50, t=80, b=50),
        height=400
    )
    
    return fig 