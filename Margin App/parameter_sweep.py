import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
from typing import Dict, Tuple, List
import warnings
import io
import base64
warnings.filterwarnings('ignore')

# Parameter sweep functionality
@st.cache_data
def run_parameter_sweep(
    etf: str,
    start_date: str,
    end_date: str,
    initial_investment: float,
    account_type: str,
    backtest_mode: str = "liquidation_reentry",
    parameter_name: str = "leverage",
    parameter_values: List[float] = None,
    profit_threshold_pct: float = 100.0
) -> pd.DataFrame:
    """
    Run parameter sweep across multiple values and collect results.
    
    Args:
        parameter_name: "leverage", "initial_investment", "profit_threshold" 
        parameter_values: List of values to test
        backtest_mode: "liquidation_reentry", "fresh_capital", "profit_threshold"
    
    Returns:
        DataFrame with parameter values and corresponding metrics
    """
    
    # Import the backtest functions
    from historical_backtest import (
        run_liquidation_reentry_backtest, 
        run_margin_restart_backtest, 
        run_profit_threshold_backtest
    )
    
    # Use the global FMP data provider instance
    from fmp_data_provider import fmp_provider
    
    # Fetch data once for all parameter sweeps
    with st.spinner(f"Fetching data for {etf}..."):
        prices_df, dividends_df, fed_funds_df = fmp_provider.get_combined_data(
            etf, start_date, end_date
        )
    
    if prices_df.empty:
        st.error(f"No data available for {etf} in the specified date range.")
        return pd.DataFrame()
    
    if parameter_values is None:
        if parameter_name == "leverage":
            parameter_values = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0] if account_type == 'portfolio' else [1.0, 1.5, 2.0]
        elif parameter_name == "initial_investment":
            parameter_values = [50000, 100000, 250000, 500000, 1000000]
        elif parameter_name == "profit_threshold":
            parameter_values = [25, 50, 75, 100, 150, 200]
    
    sweep_results = []
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, param_value in enumerate(parameter_values):
        status_text.text(f"Running backtest {i+1}/{len(parameter_values)}: {parameter_name}={param_value}")
        
        try:
            # Set parameters for this iteration
            current_leverage = param_value if parameter_name == "leverage" else 2.0
            current_investment = param_value if parameter_name == "initial_investment" else initial_investment
            current_profit_threshold = param_value if parameter_name == "profit_threshold" else profit_threshold_pct
            
            # Run appropriate backtest
            if backtest_mode == "liquidation_reentry":
                df_results, metrics, round_analysis = run_liquidation_reentry_backtest(
                    etf=etf,
                    start_date=start_date,
                    end_date=end_date,
                    initial_investment=current_investment,
                    leverage=current_leverage,
                    account_type=account_type,
                    prices_df=prices_df,
                    dividends_df=dividends_df,
                    fed_funds_df=fed_funds_df
                )
            elif backtest_mode == "fresh_capital":
                df_results, metrics, round_analysis = run_margin_restart_backtest(
                    etf=etf,
                    start_date=start_date,
                    end_date=end_date,
                    initial_investment=current_investment,
                    leverage=current_leverage,
                    account_type=account_type,
                    prices_df=prices_df,
                    dividends_df=dividends_df,
                    fed_funds_df=fed_funds_df
                )
            elif backtest_mode == "profit_threshold":
                df_results, metrics, round_analysis = run_profit_threshold_backtest(
                    etf=etf,
                    start_date=start_date,
                    end_date=end_date,
                    initial_investment=current_investment,
                    target_leverage=current_leverage,
                    account_type=account_type,
                    profit_threshold_pct=current_profit_threshold,
                    prices_df=prices_df,
                    dividends_df=dividends_df,
                    fed_funds_df=fed_funds_df
                )
            
            # Extract key metrics
            if metrics:
                result_row = {
                    parameter_name: param_value,
                    'Total_Return_Pct': metrics.get('Total Return (%)', 0),
                    'CAGR_Pct': metrics.get('CAGR (%)', 0),
                    'Final_Equity': metrics.get('Final Equity ($)', 0),
                    'Max_Drawdown_Pct': metrics.get('Max Drawdown (%)', 0),
                    'Sharpe_Ratio': metrics.get('Sharpe Ratio', 0),
                    'Sortino_Ratio': metrics.get('Sortino Ratio', 0),
                    'Annual_Volatility_Pct': metrics.get('Annual Volatility (%)', 0),
                    'Total_Liquidations': metrics.get('Total Liquidations', 0),
                    'Time_in_Market_Pct': metrics.get('Time in Market (%)', 0),
                    'Max_Drawdown_Duration': metrics.get('Max Drawdown Duration (days)', 0),
                    'Total_Interest_Paid': metrics.get('Total Interest Paid ($)', 0),
                    'Net_Interest_Cost': metrics.get('Net Interest Cost ($)', 0),
                    'Avg_Days_Between_Liquidations': metrics.get('Avg Days Between Liquidations', 0),
                    'Worst_Single_Loss_Pct': metrics.get('Worst Single Loss (%)', 0),
                    'Backtest_Days': metrics.get('Backtest Days', 0),
                    'Backtest_Years': metrics.get('Backtest Years', 0)
                }
                
                # Add mode-specific metrics
                if backtest_mode == "fresh_capital":
                    result_row['Total_Capital_Deployed'] = metrics.get('Total Capital Deployed ($)', 0)
                    result_row['Liquidation_Rate_Pct'] = metrics.get('Liquidation Rate (%)', 0)
                elif backtest_mode == "profit_threshold":
                    result_row['Total_Rebalances'] = metrics.get('Total Rebalances', 0)
                    result_row['Profit_Rebalances'] = metrics.get('Profit Rebalances', 0)
                
                sweep_results.append(result_row)
            
        except Exception as e:
            st.warning(f"Failed to run backtest for {parameter_name}={param_value}: {str(e)}")
            continue
        
        # Update progress
        progress_bar.progress((i + 1) / len(parameter_values))
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(sweep_results)

def create_parameter_sweep_charts(sweep_df: pd.DataFrame, parameter_name: str, backtest_mode: str) -> List[go.Figure]:
    """
    Create comprehensive visualization charts for parameter sweep results.
    """
    
    if sweep_df.empty:
        return []
    
    figures = []
    param_col = parameter_name
    
    # Chart 1: Performance Overview (Multi-metric)
    fig1 = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Total Return & CAGR', 'Risk Metrics', 'Drawdown Analysis', 'Trading Frequency'),
        specs=[[{"secondary_y": True}, {"secondary_y": True}], 
               [{"secondary_y": False}, {"secondary_y": True}]]
    )
    
    # Performance metrics
    fig1.add_trace(
        go.Scatter(x=sweep_df[param_col], y=sweep_df['Total_Return_Pct'], 
                  name='Total Return %', line=dict(color='#00a2ff', width=3)),
        row=1, col=1
    )
    fig1.add_trace(
        go.Scatter(x=sweep_df[param_col], y=sweep_df['CAGR_Pct'], 
                  name='CAGR %', line=dict(color='#ff8c00', width=3)),
        row=1, col=1, secondary_y=True
    )
    
    # Risk metrics
    fig1.add_trace(
        go.Scatter(x=sweep_df[param_col], y=sweep_df['Sharpe_Ratio'], 
                  name='Sharpe Ratio', line=dict(color='#00ff00', width=3)),
        row=1, col=2
    )
    fig1.add_trace(
        go.Scatter(x=sweep_df[param_col], y=sweep_df['Max_Drawdown_Pct'], 
                  name='Max Drawdown %', line=dict(color='#ff0000', width=3)),
        row=1, col=2, secondary_y=True
    )
    
    # Drawdown analysis
    fig1.add_trace(
        go.Bar(x=sweep_df[param_col], y=sweep_df['Max_Drawdown_Duration'], 
               name='Max DD Duration (days)', marker=dict(color='#ff6b6b')),
        row=2, col=1
    )
    
    # Trading frequency
    fig1.add_trace(
        go.Scatter(x=sweep_df[param_col], y=sweep_df['Total_Liquidations'], 
                  name='Total Liquidations', line=dict(color='#e74c3c', width=3)),
        row=2, col=2
    )
    fig1.add_trace(
        go.Scatter(x=sweep_df[param_col], y=sweep_df['Time_in_Market_Pct'], 
                  name='Time in Market %', line=dict(color='#3498db', width=3)),
        row=2, col=2, secondary_y=True
    )
    
    fig1.update_layout(
        title=f"Parameter Sweep: {parameter_name.title()} Analysis - {backtest_mode.title()} Mode",
        height=800,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    # Update axes styling
    fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    
    figures.append(fig1)
    
    # Chart 2: Risk-Return Scatter Plot (FIXED - removed sizemax)
    fig2 = go.Figure()
    
    # Scale bubble sizes and cap them manually
    bubble_sizes = sweep_df['Final_Equity'] / 1000  # Scale by thousands
    # Cap maximum size manually
    max_size = 50
    min_size = 10
    bubble_sizes_capped = np.clip(bubble_sizes, min_size, max_size)
    
    # Create bubble chart: Return vs Risk
    fig2.add_trace(go.Scatter(
        x=sweep_df['Annual_Volatility_Pct'],
        y=sweep_df['Total_Return_Pct'],
        mode='markers+text',
        marker=dict(
            size=bubble_sizes_capped,  # Use capped sizes
            color=sweep_df[param_col],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title=parameter_name.title()),
            sizemode='diameter',
            sizemin=min_size,
            line=dict(width=2, color='white')
        ),
        text=[f"{parameter_name}={val}" for val in sweep_df[param_col]],
        textposition="middle center",
        textfont=dict(size=10),
        name='Risk-Return Profile',
        hovertemplate=f'<b>{parameter_name.title()}: %{{text}}</b><br>' +
                     'Annual Volatility: %{x:.1f}%<br>' +
                     'Total Return: %{y:.1f}%<br>' +
                     'Final Equity: $%{customdata:,.0f}<br>' +
                     '<extra></extra>',
        customdata=sweep_df['Final_Equity']  # Use customdata for hover info
    ))
    
    fig2.update_layout(
        title=f'Risk-Return Analysis: {parameter_name.title()} Sweep',
        xaxis_title='Annual Volatility (%)',
        yaxis_title='Total Return (%)',
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA',
        height=600,
        showlegend=False
    )
    
    fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    
    figures.append(fig2)
    
    # Chart 3: Efficiency Frontier (Sharpe Ratio Analysis)
    fig3 = go.Figure()
    
    # Sharpe ratio by parameter
    colors = ['#ff0000' if sr < 0 else '#ffff00' if sr < 0.5 else '#00ff00' for sr in sweep_df['Sharpe_Ratio']]
    
    fig3.add_trace(go.Bar(
        x=sweep_df[param_col],
        y=sweep_df['Sharpe_Ratio'],
        marker=dict(color=colors, line=dict(color='white', width=1)),
        name='Sharpe Ratio',
        text=[f'{sr:.3f}' for sr in sweep_df['Sharpe_Ratio']],
        textposition='outside'
    ))
    
    # Add Sortino ratio as line
    fig3.add_trace(go.Scatter(
        x=sweep_df[param_col],
        y=sweep_df['Sortino_Ratio'],
        mode='lines+markers',
        line=dict(color='#00a2ff', width=3),
        marker=dict(size=8, color='#00a2ff'),
        name='Sortino Ratio',
        yaxis='y2'
    ))
    
    fig3.update_layout(
        title=f'Risk-Adjusted Returns: {parameter_name.title()} Analysis',
        xaxis_title=parameter_name.title(),
        yaxis_title='Sharpe Ratio',
        yaxis2=dict(title='Sortino Ratio', overlaying='y', side='right', color='#00a2ff'),
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA',
        height=500,
        showlegend=True
    )
    
    fig3.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig3.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    
    figures.append(fig3)
    
    # Chart 4: Cost Analysis (if applicable)
    if 'Total_Interest_Paid' in sweep_df.columns:
        fig4 = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Interest Costs vs Returns', 'Cost Efficiency'),
            specs=[[{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        # Interest vs returns
        fig4.add_trace(
            go.Scatter(x=sweep_df[param_col], y=sweep_df['Total_Interest_Paid'], 
                      name='Total Interest Paid', line=dict(color='#e74c3c', width=3)),
            row=1, col=1
        )
        fig4.add_trace(
            go.Scatter(x=sweep_df[param_col], y=sweep_df['Total_Return_Pct'], 
                      name='Total Return %', line=dict(color='#2ecc71', width=3)),
            row=1, col=1, secondary_y=True
        )
        
        # Cost efficiency (return per dollar of interest)
        cost_efficiency = sweep_df['Total_Return_Pct'] / (sweep_df['Total_Interest_Paid'] / 1000 + 0.1)  # Avoid div by zero
        fig4.add_trace(
            go.Bar(x=sweep_df[param_col], y=cost_efficiency, 
                   name='Return per $1K Interest', marker=dict(color='#9b59b6')),
            row=1, col=2
        )
        
        fig4.update_layout(
            title=f'Cost Analysis: {parameter_name.title()} Impact',
            height=500,
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='#FAFAFA'
        )
        
        fig4.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
        fig4.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
        
        figures.append(fig4)
    
    return figures

def export_sweep_results(sweep_df: pd.DataFrame, parameter_name: str, backtest_mode: str) -> str:
    """
    Create downloadable CSV export of sweep results.
    """
    
    # Create formatted export DataFrame
    export_df = sweep_df.copy()
    
    # Add metadata columns
    export_df.insert(0, 'Parameter_Name', parameter_name)
    export_df.insert(1, 'Backtest_Mode', backtest_mode)
    export_df.insert(2, 'Export_Date', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Round numeric columns for cleaner export
    numeric_columns = export_df.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        if col.endswith('_Pct') or col in ['Sharpe_Ratio', 'Sortino_Ratio']:
            export_df[col] = export_df[col].round(3)
        elif col.endswith('_Equity') or col.startswith('Total_'):
            export_df[col] = export_df[col].round(0)
        else:
            export_df[col] = export_df[col].round(2)
    
    # Convert to CSV
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    csv_string = csv_buffer.getvalue()
    
    # Create download link
    b64 = base64.b64encode(csv_string.encode()).decode()
    filename = f"parameter_sweep_{parameter_name}_{backtest_mode}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">📊 Download Parameter Sweep Results (CSV)</a>'

def render_parameter_sweep_section(etf_choice, start_date, end_date, equity, leverage, account_type, excel_data=None):
    """
    Render the parameter sweep section UI
    Note: excel_data parameter is kept for backward compatibility but is no longer used
    """
    
    # PARAMETER SWEEP SECTION
    st.markdown("---")
    st.markdown("<h1>📊 PARAMETER SWEEP ANALYSIS</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #1a1a1a; border: 1px solid #ff8c00; padding: 1rem; color: #e0e0e0; margin-bottom: 2rem;">
        <strong style="color: #ff8c00;">AUTOMATED PARAMETER TESTING:</strong> Run multiple backtests across parameter ranges and visualize results. 
        Perfect for optimizing leverage levels, testing different investment amounts, or analyzing profit thresholds.
    </div>
    """, unsafe_allow_html=True)
    
    # Parameter sweep controls
    param_col1, param_col2, param_col3 = st.columns([1, 1, 1])
    
    with param_col1:
        st.markdown("**PARAMETER TO SWEEP**")
        parameter_name = st.selectbox(
            "Parameter",
            ["leverage", "initial_investment", "profit_threshold"],
            format_func=lambda x: {
                "leverage": "Leverage Multiplier",
                "initial_investment": "Initial Investment Amount",
                "profit_threshold": "Profit Threshold %"
            }[x],
            help="Choose which parameter to test across multiple values",
            key="sweep_parameter"
        )
        
        st.markdown("**BACKTEST MODE**")
        sweep_mode = st.selectbox(
            "Mode",
            ["liquidation_reentry", "fresh_capital", "profit_threshold"],
            format_func=lambda x: {
                "liquidation_reentry": "Liquidation-Reentry",
                "fresh_capital": "Fresh Capital",
                "profit_threshold": "Profit Threshold"
            }[x],
            help="Which backtest mode to use for the sweep",
            key="sweep_mode"
        )
    
    with param_col2:
        st.markdown("**PARAMETER VALUES**")
        
        # Default ranges based on parameter type
        if parameter_name == "leverage":
            if account_type == "reg_t":
                default_values = "1.0, 1.2, 1.5, 1.8, 2.0"
                max_val = 2.0
            else:
                default_values = "1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0"
                max_val = 7.0
            help_text = f"Leverage values to test (max {max_val:.1f}x for {account_type})"
        elif parameter_name == "initial_investment":
            default_values = "10000, 25000, 50000, 100000, 250000, 500000, 1000000"
            help_text = "Investment amounts to test ($)"
        else:  # profit_threshold
            default_values = "25, 50, 75, 100, 150, 200, 300"
            help_text = "Profit threshold percentages to test"
        
        parameter_values_input = st.text_area(
            "Values (comma-separated)",
            value=default_values,
            help=help_text,
            key="sweep_values",
            height=80
        )
        
        # Parse parameter values
        try:
            parameter_values = [float(x.strip()) for x in parameter_values_input.split(",")]
            
            # Validate values
            if parameter_name == "leverage":
                max_leverage = 2.0 if account_type == "reg_t" else 7.0
                parameter_values = [v for v in parameter_values if 1.0 <= v <= max_leverage]
            elif parameter_name == "initial_investment":
                parameter_values = [v for v in parameter_values if v >= 1000]
            elif parameter_name == "profit_threshold":
                parameter_values = [v for v in parameter_values if 10 <= v <= 1000]
                
            if not parameter_values:
                st.error("No valid parameter values found")
                
        except ValueError:
            st.error("Please enter valid numbers separated by commas")
            parameter_values = []
    
    with param_col3:
        st.markdown("**SWEEP CONFIGURATION**")
        
        # Show number of backtests that will run
        num_backtests = len(parameter_values) if parameter_values else 0
        estimated_time = num_backtests * 2  # Rough estimate of 2 seconds per backtest
        
        st.markdown(f"""
        <div class="terminal-card">
            <div class="data-grid">
                <div class="data-label">BACKTESTS:</div>
                <div class="data-value">{num_backtests}</div>
                <div class="data-label">EST. TIME:</div>
                <div class="data-value">{estimated_time}s</div>
                <div class="data-label">PARAMETER:</div>
                <div class="data-value">{parameter_name.replace('_', ' ').title()}</div>
                <div class="data-label">MODE:</div>
                <div class="data-value">{sweep_mode.replace('_', ' ').title()}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add profit threshold for profit_threshold mode
        if sweep_mode == "profit_threshold" and parameter_name != "profit_threshold":
            sweep_profit_threshold = st.number_input(
                "Profit Threshold %",
                min_value=10.0,
                max_value=500.0,
                value=100.0,
                step=10.0,
                help="Fixed profit threshold for sweep (only used if not sweeping this parameter)",
                key="sweep_profit_threshold"
            )
        else:
            sweep_profit_threshold = 100.0
    
    # Run parameter sweep
    if st.button("🚀 RUN PARAMETER SWEEP", use_container_width=True, type="primary", key="run_sweep_button"):
        
        if not parameter_values:
            st.error("Please enter valid parameter values to sweep")
            return
        
        if num_backtests > 20:
            st.warning("Large parameter sweep detected. This may take several minutes.")
        
        # Use the same base parameters as the regular backtest
        base_investment = equity * leverage if parameter_name != "initial_investment" else 100000
        
        with st.spinner(f"Running {num_backtests} backtests across {parameter_name} values..."):
            
            # Run the parameter sweep
            sweep_results = run_parameter_sweep(
                etf=etf_choice,
                start_date=str(start_date),
                end_date=str(end_date),
                initial_investment=base_investment,
                account_type=account_type,
                backtest_mode=sweep_mode,
                parameter_name=parameter_name,
                parameter_values=parameter_values,
                profit_threshold_pct=sweep_profit_threshold
            )
        
        if sweep_results.empty:
            st.error("❌ Parameter sweep failed. No valid results generated.")
            return
        
        # Display results
        st.success(f"✅ **Parameter Sweep Complete!** Analyzed {len(sweep_results)} parameter combinations")
        
        # Summary statistics
        st.markdown("### 📈 PARAMETER SWEEP RESULTS")
        
        # Key insights
        best_return_idx = sweep_results['Total_Return_Pct'].idxmax()
        best_sharpe_idx = sweep_results['Sharpe_Ratio'].idxmax()
        lowest_risk_idx = sweep_results['Max_Drawdown_Pct'].idxmin()
        
        insight_col1, insight_col2, insight_col3 = st.columns(3)
        
        with insight_col1:
            best_return_value = sweep_results.loc[best_return_idx, parameter_name]
            best_return_pct = sweep_results.loc[best_return_idx, 'Total_Return_Pct']
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 2px solid #00ff00; padding: 1rem; text-align: center;">
                <div style="color: #00ff00; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">BEST RETURN</div>
                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{parameter_name.replace('_', ' ').title()}: {best_return_value}</div>
                <div style="color: #00ff00; font-size: 1.1rem; margin-top: 0.5rem;">{best_return_pct:.1f}% Return</div>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_col2:
            best_sharpe_value = sweep_results.loc[best_sharpe_idx, parameter_name]
            best_sharpe_ratio = sweep_results.loc[best_sharpe_idx, 'Sharpe_Ratio']
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 2px solid #00a2ff; padding: 1rem; text-align: center;">
                <div style="color: #00a2ff; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">BEST RISK-ADJUSTED</div>
                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{parameter_name.replace('_', ' ').title()}: {best_sharpe_value}</div>
                <div style="color: #00a2ff; font-size: 1.1rem; margin-top: 0.5rem;">{best_sharpe_ratio:.3f} Sharpe</div>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_col3:
            lowest_risk_value = sweep_results.loc[lowest_risk_idx, parameter_name]
            lowest_risk_dd = sweep_results.loc[lowest_risk_idx, 'Max_Drawdown_Pct']
            st.markdown(f"""
            <div style="background-color: #1a1a1a; border: 2px solid #ff8c00; padding: 1rem; text-align: center;">
                <div style="color: #ff8c00; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">LOWEST RISK</div>
                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{parameter_name.replace('_', ' ').title()}: {lowest_risk_value}</div>
                <div style="color: #ff8c00; font-size: 1.1rem; margin-top: 0.5rem;">{lowest_risk_dd:.1f}% Max DD</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Results table
        st.markdown("### 📋 DETAILED SWEEP RESULTS")
        
        # Format display table
        display_sweep = sweep_results.copy()
        
        # Format numeric columns
        display_sweep['Total Return'] = display_sweep['Total_Return_Pct'].apply(lambda x: f"{x:.1f}%")
        display_sweep['CAGR'] = display_sweep['CAGR_Pct'].apply(lambda x: f"{x:.1f}%")
        display_sweep['Final Equity'] = display_sweep['Final_Equity'].apply(lambda x: f"${x:,.0f}")
        display_sweep['Max Drawdown'] = display_sweep['Max_Drawdown_Pct'].apply(lambda x: f"{x:.1f}%")
        display_sweep['Sharpe'] = display_sweep['Sharpe_Ratio'].apply(lambda x: f"{x:.3f}")
        display_sweep['Liquidations'] = display_sweep['Total_Liquidations'].apply(lambda x: f"{x:.0f}")
        
        # Select columns for display
        display_columns = [parameter_name, 'Total Return', 'CAGR', 'Final Equity', 'Max Drawdown', 'Sharpe', 'Liquidations']
        
        if sweep_mode == "fresh_capital":
            display_sweep['Capital Deployed'] = display_sweep['Total_Capital_Deployed'].apply(lambda x: f"${x:,.0f}")
            display_columns.append('Capital Deployed')
        elif sweep_mode == "profit_threshold":
            display_sweep['Rebalances'] = display_sweep['Total_Rebalances'].apply(lambda x: f"{x:.0f}")
            display_columns.append('Rebalances')
        
        # Display table
        st.dataframe(
            display_sweep[display_columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                parameter_name: st.column_config.NumberColumn(parameter_name.replace('_', ' ').title(), width="small"),
                'Total Return': st.column_config.TextColumn("Total Return", width="small"),
                'CAGR': st.column_config.TextColumn("CAGR", width="small"),
                'Final Equity': st.column_config.TextColumn("Final Equity", width="medium"),
                'Max Drawdown': st.column_config.TextColumn("Max DD", width="small"),
                'Sharpe': st.column_config.TextColumn("Sharpe", width="small"),
                'Liquidations': st.column_config.TextColumn("Liquidations", width="small")
            }
        )
        
        # Create and display charts
        st.markdown("### 📊 PARAMETER SWEEP VISUALIZATIONS")
        
        # Add CSS to ensure white backgrounds
        st.markdown("""
        <style>
        .js-plotly-plot .plotly .plot-container {
            background-color: white !important;
        }
        .js-plotly-plot .plotly .plot-container .svg-container {
            background-color: white !important;
        }
        .js-plotly-plot .plotly .plot-container .svg-container svg {
            background-color: white !important;
        }
        .modebar {
            background-color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        charts = create_parameter_sweep_charts(sweep_results, parameter_name, sweep_mode)
        
        for i, chart in enumerate(charts):
            st.plotly_chart(chart, use_container_width=True, config={'displayModeBar': True})
            if i < len(charts) - 1:  # Add separator between charts
                st.markdown("<div style='border-bottom: 1px solid #333333; margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        # Export functionality
        st.markdown("### 💾 EXPORT RESULTS")
        
        download_link = export_sweep_results(sweep_results, parameter_name, sweep_mode)
        st.markdown(download_link, unsafe_allow_html=True)
        
        # Advanced insights
        st.markdown("### 🧠 AI INSIGHTS")
        
        # Calculate some insights
        correlation_with_return = np.corrcoef(sweep_results[parameter_name], sweep_results['Total_Return_Pct'])[0, 1]
        correlation_with_risk = np.corrcoef(sweep_results[parameter_name], sweep_results['Max_Drawdown_Pct'])[0, 1]
        
        optimal_range = None
        if len(sweep_results) >= 3:
            # Find values where Sharpe > median Sharpe
            median_sharpe = sweep_results['Sharpe_Ratio'].median()
            good_sharpe_mask = sweep_results['Sharpe_Ratio'] > median_sharpe
            if good_sharpe_mask.any():
                optimal_values = sweep_results[good_sharpe_mask][parameter_name]
                optimal_range = f"{optimal_values.min():.1f} - {optimal_values.max():.1f}"
        
        insights_text = f"""
        **Parameter Analysis for {parameter_name.replace('_', ' ').title()}:**
        
        • **Return Correlation**: {correlation_with_return:.3f} - {'Strong positive' if correlation_with_return > 0.7 else 'Moderate positive' if correlation_with_return > 0.3 else 'Weak positive' if correlation_with_return > 0 else 'Negative'} relationship with returns
        • **Risk Correlation**: {correlation_with_risk:.3f} - {'Higher values increase risk' if correlation_with_risk > 0.3 else 'Lower values increase risk' if correlation_with_risk < -0.3 else 'Mixed impact on risk'}
        """
        
        if optimal_range:
            insights_text += f"• **Optimal Range**: {optimal_range} shows above-median risk-adjusted returns"
        
        # Add mode-specific insights
        if sweep_mode == "liquidation_reentry":
            avg_liquidations = sweep_results['Total_Liquidations'].mean()
            insights_text += f"\n• **Liquidation Analysis**: Average {avg_liquidations:.1f} liquidations per strategy"
        elif sweep_mode == "fresh_capital":
            avg_capital = sweep_results['Total_Capital_Deployed'].mean()
            insights_text += f"\n• **Capital Requirements**: Average ${avg_capital:,.0f} total capital deployed"
        
        st.markdown(f"""
        <div style="background-color: #1a1a1a; border: 1px solid #9b59b6; padding: 1.5rem; color: #e0e0e0;">
            {insights_text}
        </div>
        """, unsafe_allow_html=True) 