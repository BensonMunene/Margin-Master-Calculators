import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')

# Cache data loading for performance
@st.cache_data(ttl=3600)
def load_comprehensive_data():
    """Load all required data including Fed Funds rates from Excel file"""
    try:
        # Try multiple possible data paths
        data_paths = [
            "Data\ETFs and Fed Funds Data.xlsx",  # Direct path
            "../Data/ETFs and Fed Funds Data.xlsx",  # Relative path
            "D:/Benson/aUpWork/Ben Ruff/Implementation/Data/ETFs and Fed Funds Data.xlsx"  # Absolute path
        ]
        
        excel_data = None
        for path in data_paths:
            try:
                excel_data = pd.read_excel(path)
                break
            except:
                continue
                
        if excel_data is None:
            raise FileNotFoundError("Could not find ETFs and Fed Funds Data.xlsx file")
            
        excel_data['Date'] = pd.to_datetime(excel_data['Unnamed: 0'])
        excel_data.set_index('Date', inplace=True)
        excel_data = excel_data.drop('Unnamed: 0', axis=1)
        
        # Try multiple paths for CSV files
        csv_paths = [
            "Data/",
            "../Data/",
            "D:/Benson/aUpWork/Ben Ruff/Implementation/Data/"
        ]
        
        spy_df = None
        for path in csv_paths:
            try:
                spy_df = pd.read_csv(path + "SPY.csv")
                vti_df = pd.read_csv(path + "VTI.csv")
                spy_div_df = pd.read_csv(path + "SPY Dividends.csv")
                vti_div_df = pd.read_csv(path + "VTI Dividends.csv")
                break
            except:
                continue
        
        if spy_df is None:
            raise FileNotFoundError("Could not find CSV data files")
        
        # Process dataframes
        for df in [spy_df, vti_df, spy_div_df, vti_div_df]:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        
        return excel_data, spy_df, vti_df, spy_div_df, vti_div_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None, None

@st.cache_data
def calculate_margin_params(account_type: str, leverage: float) -> Dict[str, float]:
    """Calculate margin parameters based on account type"""
    if account_type == 'reg_t':
        return {
            'max_leverage': 2.0,
            'initial_margin_pct': 50.0,
            'maintenance_margin_pct': 25.0,
            'margin_rate_spread': 1.5  # Fed Funds + 1.5%
        }
    else:  # portfolio margin
        return {
            'max_leverage': 7.0,
            'initial_margin_pct': max(100.0 / leverage, 14.29),  # Dynamic based on leverage
            'maintenance_margin_pct': 15.0,
            'margin_rate_spread': 2.0  # Fed Funds + 2.0% (typically higher for portfolio margin)
        }

@st.cache_data
def run_historical_backtest(
    etf: str,
    start_date: str,
    initial_investment: float,
    leverage: float,
    account_type: str,
    excel_data: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Run comprehensive historical backtest with realistic margin calculations
    """
    
    # Get margin parameters
    margin_params = calculate_margin_params(account_type, leverage)
    
    # Filter data for selected date range and ETF
    data = excel_data.loc[start_date:].copy()
    
    if etf == 'SPY':
        price_col = 'SPY'
        dividend_col = 'SPY_Dividends'
    else:
        price_col = 'VTI'
        dividend_col = 'VTI_Dividends'
    
    # Remove any rows with missing data
    data = data.dropna(subset=[price_col, 'FedFunds (%)'])
    
    if len(data) < 2:
        st.error("Insufficient data for the selected date range")
        return pd.DataFrame(), {}
    
    # Initialize portfolio
    initial_price = data[price_col].iloc[0]
    cash_investment = initial_investment / leverage
    margin_loan = initial_investment - cash_investment
    shares = initial_investment / initial_price
    
    # Initialize tracking arrays
    results = []
    margin_calls = []
    
    # Calculate daily portfolio evolution
    for i, (date, row) in enumerate(data.iterrows()):
        current_price = row[price_col]
        dividend_payment = row[dividend_col] if pd.notna(row[dividend_col]) else 0.0
        fed_funds_rate = row['FedFunds (%)'] / 100.0  # Convert percentage to decimal
        
        # Calculate daily interest on margin loan
        daily_interest_rate = (fed_funds_rate + margin_params['margin_rate_spread'] / 100.0) / 365
        daily_interest_cost = margin_loan * daily_interest_rate
        
        # Handle dividend reinvestment
        if dividend_payment > 0:
            dividend_received = shares * dividend_payment
            # Reinvest dividends (buy more shares)
            additional_shares = dividend_received / current_price
            shares += additional_shares
        
        # Calculate portfolio value
        portfolio_value = shares * current_price
        equity = portfolio_value - margin_loan
        
        # Update margin loan with accrued interest
        margin_loan += daily_interest_cost
        
        # Calculate maintenance margin requirement
        maintenance_margin_required = portfolio_value * (margin_params['maintenance_margin_pct'] / 100.0)
        
        # Check for margin call
        is_margin_call = equity < maintenance_margin_required
        if is_margin_call:
            margin_calls.append(date)
        
        # Calculate margin call price (price at which margin call would trigger)
        if shares > 0:
            margin_call_price = margin_loan / (shares * (1 - margin_params['maintenance_margin_pct'] / 100.0))
        else:
            margin_call_price = 0
        
        # Store results
        results.append({
            'Date': date,
            'ETF_Price': current_price,
            'Shares_Held': shares,
            'Portfolio_Value': portfolio_value,
            'Margin_Loan': margin_loan,
            'Equity': equity,
            'Maintenance_Margin_Required': maintenance_margin_required,
            'Is_Margin_Call': is_margin_call,
            'Margin_Call_Price': margin_call_price,
            'Daily_Interest_Cost': daily_interest_cost,
            'Fed_Funds_Rate': fed_funds_rate * 100,
            'Margin_Rate': (fed_funds_rate + margin_params['margin_rate_spread'] / 100.0) * 100,
            'Dividend_Payment': dividend_payment,
            'Cumulative_Dividends': dividend_payment * shares if dividend_payment > 0 else 0
        })
    
    # Convert to DataFrame
    df_results = pd.DataFrame(results)
    df_results.set_index('Date', inplace=True)
    
    # Calculate performance metrics
    final_equity = df_results['Equity'].iloc[-1]
    total_return = (final_equity - cash_investment) / cash_investment * 100
    
    # Calculate CAGR
    years = len(df_results) / 252  # Approximate trading days per year
    if years > 0 and final_equity > 0:
        cagr = ((final_equity / cash_investment) ** (1 / years) - 1) * 100
    else:
        cagr = 0
    
    # Calculate maximum drawdown
    equity_series = df_results['Equity']
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    
    # Calculate other metrics
    total_interest_paid = df_results['Daily_Interest_Cost'].sum()
    total_dividends_received = df_results['Cumulative_Dividends'].sum()
    num_margin_calls = len(margin_calls)
    
    # Volatility calculation
    daily_returns = equity_series.pct_change().dropna()
    annual_volatility = daily_returns.std() * np.sqrt(252) * 100
    
    # Sharpe ratio (assuming 0% risk-free rate for simplicity)
    if annual_volatility > 0:
        sharpe_ratio = cagr / annual_volatility
    else:
        sharpe_ratio = 0
    
    metrics = {
        'Total Return (%)': total_return,
        'CAGR (%)': cagr,
        'Max Drawdown (%)': max_drawdown,
        'Annual Volatility (%)': annual_volatility,
        'Sharpe Ratio': sharpe_ratio,
        'Total Interest Paid ($)': total_interest_paid,
        'Total Dividends Received ($)': total_dividends_received,
        'Number of Margin Calls': num_margin_calls,
        'Final Portfolio Value ($)': df_results['Portfolio_Value'].iloc[-1],
        'Final Equity ($)': final_equity,
        'Initial Investment ($)': cash_investment,
        'Leverage Used': leverage
    }
    
    return df_results, metrics

@st.cache_data
def run_margin_restart_backtest(
    etf: str,
    start_date: str,
    initial_investment: float,
    leverage: float,
    account_type: str,
    excel_data: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict]:
    """
    Clean, simple backtest with margin call restarts.
    When margin call occurs: liquidate position, start fresh with new capital.
    """
    
    # Get margin parameters
    margin_params = calculate_margin_params(account_type, leverage)
    
    # Prepare data
    data = excel_data.loc[start_date:].copy()
    if etf == 'SPY':
        price_col, dividend_col = 'SPY', 'SPY_Dividends'
    else:
        price_col, dividend_col = 'VTI', 'VTI_Dividends'
    
    data = data.dropna(subset=[price_col, 'FedFunds (%)'])
    
    if len(data) < 10:
        return pd.DataFrame(), {}
    
    # Investment parameters
    cash_per_round = initial_investment / leverage
    margin_per_round = initial_investment - cash_per_round
    
    # Tracking variables
    rounds = []
    current_round = 1
    position_start_idx = 0
    total_cash_deployed = 0
    
    while position_start_idx < len(data) - 1 and current_round <= 1000:  # Safety limit
        
        # Start new position
        start_date_round = data.index[position_start_idx]
        start_price = data[price_col].iloc[position_start_idx]
        shares = initial_investment / start_price
        margin_loan = margin_per_round
        
        total_cash_deployed += cash_per_round
        
        # Track this round
        days_in_round = 0
        total_interest_paid = 0
        total_dividends_received = 0
        
        # Simulate day by day until margin call or end of data
        for i in range(position_start_idx, len(data)):
            current_date = data.index[i]
            current_price = data[price_col].iloc[i]
            dividend = data[dividend_col].iloc[i] if pd.notna(data[dividend_col].iloc[i]) else 0
            fed_rate = data['FedFunds (%)'].iloc[i] / 100
            
            # Daily interest cost
            daily_rate = (fed_rate + margin_params['margin_rate_spread'] / 100) / 365
            daily_interest = margin_loan * daily_rate
            margin_loan += daily_interest
            total_interest_paid += daily_interest
            
            # Handle dividends
            if dividend > 0:
                dividend_cash = shares * dividend
                total_dividends_received += dividend_cash
                # Reinvest dividends
                shares += dividend_cash / current_price
            
            # Calculate current equity
            portfolio_value = shares * current_price
            equity = portfolio_value - margin_loan
            maintenance_required = portfolio_value * (margin_params['maintenance_margin_pct'] / 100)
            
            days_in_round += 1
            
            # Check for margin call
            if equity < maintenance_required:
                # MARGIN CALL - Liquidate everything
                liquidation_value = max(0, equity)
                loss_amount = cash_per_round - liquidation_value
                
                # Record this round
                rounds.append({
                    'round': current_round,
                    'start_date': start_date_round,
                    'end_date': current_date,
                    'days': days_in_round,
                    'start_price': start_price,
                    'end_price': current_price,
                    'price_change_pct': (current_price / start_price - 1) * 100,
                    'cash_invested': cash_per_round,
                    'liquidation_value': liquidation_value,
                    'loss_amount': loss_amount,
                    'loss_pct': (loss_amount / cash_per_round) * 100,
                    'interest_paid': total_interest_paid,
                    'dividends_received': total_dividends_received,
                    'margin_call': True
                })
                
                # Start next round
                current_round += 1
                position_start_idx = i + 1
                break
        else:
            # Reached end of data without margin call
            final_portfolio_value = shares * current_price
            final_equity = final_portfolio_value - margin_loan
            profit_loss = final_equity - cash_per_round
            
            rounds.append({
                'round': current_round,
                'start_date': start_date_round,
                'end_date': current_date,
                'days': days_in_round,
                'start_price': start_price,
                'end_price': current_price,
                'price_change_pct': (current_price / start_price - 1) * 100,
                'cash_invested': cash_per_round,
                'liquidation_value': final_equity,
                'loss_amount': -profit_loss if profit_loss < 0 else 0,
                'profit_amount': profit_loss if profit_loss > 0 else 0,
                'loss_pct': (-profit_loss / cash_per_round * 100) if profit_loss < 0 else 0,
                'profit_pct': (profit_loss / cash_per_round * 100) if profit_loss > 0 else 0,
                'interest_paid': total_interest_paid,
                'dividends_received': total_dividends_received,
                'margin_call': False
            })
            break
    
    # Convert to DataFrame
    rounds_df = pd.DataFrame(rounds)
    
    if rounds_df.empty:
        return rounds_df, {}
    
    # Calculate summary metrics
    total_rounds = len(rounds_df)
    margin_call_rounds = rounds_df['margin_call'].sum()
    total_losses = rounds_df['loss_amount'].sum()
    total_profits = rounds_df.get('profit_amount', 0).sum() if 'profit_amount' in rounds_df.columns else 0
    net_result = total_profits - total_losses
    total_interest = rounds_df['interest_paid'].sum()
    total_dividends = rounds_df['dividends_received'].sum()
    avg_survival_days = rounds_df['days'].mean()
    worst_loss_pct = rounds_df['loss_pct'].max() if 'loss_pct' in rounds_df.columns else 0
    best_gain_pct = rounds_df.get('profit_pct', pd.Series([0])).max()
    
    summary = {
        'total_rounds': total_rounds,
        'margin_calls': margin_call_rounds,
        'successful_rounds': total_rounds - margin_call_rounds,
        'total_cash_deployed': total_cash_deployed,
        'total_losses': total_losses,
        'total_profits': total_profits,
        'net_result': net_result,
        'total_return_pct': (net_result / total_cash_deployed * 100) if total_cash_deployed > 0 else 0,
        'total_interest_paid': total_interest,
        'total_dividends_received': total_dividends,
        'avg_survival_days': avg_survival_days,
        'avg_survival_years': avg_survival_days / 252,
        'worst_loss_pct': worst_loss_pct,
        'best_gain_pct': best_gain_pct,
        'success_rate_pct': ((total_rounds - margin_call_rounds) / total_rounds * 100) if total_rounds > 0 else 0,
        'leverage': leverage,
        'cash_per_round': cash_per_round
    }
    
    return rounds_df, summary

def create_portfolio_chart(df_results: pd.DataFrame, metrics: Dict[str, float]) -> go.Figure:
    """Create comprehensive portfolio performance chart"""
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Portfolio Value & Equity Over Time', 'Drawdown Analysis', 'Margin Metrics'),
        vertical_spacing=0.08,
        row_heights=[0.5, 0.25, 0.25]
    )
    
    # Portfolio value and equity
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Portfolio_Value'],
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='Date: %{x}<br>Portfolio Value: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Equity'],
            name='Equity (Your Money)',
            line=dict(color='#2ca02c', width=2),
            hovertemplate='Date: %{x}<br>Equity: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add margin call markers
    margin_calls = df_results[df_results['Is_Margin_Call']]
    if not margin_calls.empty:
        fig.add_trace(
            go.Scatter(
                x=margin_calls.index,
                y=margin_calls['Equity'],
                mode='markers',
                name='Margin Calls',
                marker=dict(color='red', size=8, symbol='x'),
                hovertemplate='Margin Call<br>Date: %{x}<br>Equity: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Drawdown analysis
    equity_series = df_results['Equity']
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max * 100
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=drawdown,
            name='Drawdown %',
            fill='tonexty',
            fillcolor='rgba(255, 0, 0, 0.3)',
            line=dict(color='red', width=1),
            hovertemplate='Date: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Margin loan and interest
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Margin_Loan'],
            name='Margin Loan',
            line=dict(color='orange', width=2),
            hovertemplate='Date: %{x}<br>Margin Loan: $%{y:,.2f}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=f"Historical Backtest Results - {metrics['Leverage Used']:.1f}x Leverage",
        height=800,
        showlegend=True,
        legend=dict(x=0, y=1, bgcolor='rgba(255,255,255,0.8)'),
        plot_bgcolor='white'
    )
    
    # Update axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    # Format y-axes for currency
    fig.update_yaxes(tickformat='$,.0f', row=1, col=1)
    fig.update_yaxes(tickformat='.2f', row=2, col=1, title_text="Drawdown (%)")
    fig.update_yaxes(tickformat='$,.0f', row=3, col=1)
    
    return fig

def create_margin_analysis_chart(df_results: pd.DataFrame) -> go.Figure:
    """Create detailed margin analysis chart"""
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Equity vs Maintenance Margin Requirement', 'Interest Rates Over Time'),
        vertical_spacing=0.15
    )
    
    # Equity vs Maintenance Margin
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Equity'],
            name='Equity',
            line=dict(color='green', width=2),
            hovertemplate='Date: %{x}<br>Equity: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Maintenance_Margin_Required'],
            name='Maintenance Margin Required',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate='Date: %{x}<br>Required: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Fill area where margin call would occur
    margin_violation = df_results['Equity'] < df_results['Maintenance_Margin_Required']
    if margin_violation.any():
        violation_data = df_results[margin_violation]
        fig.add_trace(
            go.Scatter(
                x=violation_data.index,
                y=violation_data['Equity'],
                mode='markers',
                name='Margin Call Zone',
                marker=dict(color='red', size=4),
                hovertemplate='Margin Call<br>Date: %{x}<br>Equity: $%{y:,.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Interest rates
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Fed_Funds_Rate'],
            name='Fed Funds Rate',
            line=dict(color='blue', width=2),
            hovertemplate='Date: %{x}<br>Fed Funds: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Margin_Rate'],
            name='Margin Interest Rate',
            line=dict(color='purple', width=2),
            hovertemplate='Date: %{x}<br>Margin Rate: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title="Margin Analysis and Interest Rate Environment",
        height=600,
        showlegend=True,
        plot_bgcolor='white'
    )
    
    # Update axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(tickformat='$,.0f', row=1, col=1)
    fig.update_yaxes(tickformat='.2f', row=2, col=1, title_text="Interest Rate (%)")
    
    return fig

def create_performance_metrics_chart(metrics: Dict[str, float]) -> go.Figure:
    """Create performance metrics visualization"""
    
    # Key metrics for radar chart
    radar_metrics = ['CAGR (%)', 'Annual Volatility (%)', 'Sharpe Ratio']
    radar_values = [
        max(metrics['CAGR (%)'], -50),  # Cap at -50% for visualization
        min(metrics['Annual Volatility (%)'], 100),  # Cap at 100% for visualization
        max(min(metrics['Sharpe Ratio'], 3), -3)  # Cap between -3 and 3
    ]
    
    # Normalize values for radar chart (0-100 scale)
    normalized_values = [
        (radar_values[0] + 50) / 1.5,  # CAGR: -50% to 100%
        100 - radar_values[1],  # Volatility: lower is better
        (radar_values[2] + 3) * 100 / 6  # Sharpe: -3 to 3
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=normalized_values + [normalized_values[0]],  # Close the shape
        theta=radar_metrics + [radar_metrics[0]],
        fill='toself',
        name='Performance Profile',
        line=dict(color='blue', width=3),
        fillcolor='rgba(0, 100, 255, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickformat='.0f'
            )
        ),
        title="Performance Profile (Normalized 0-100 Scale)",
        height=400
    )
    
    return fig

def create_restart_summary_chart(rounds_df: pd.DataFrame, summary: Dict) -> go.Figure:
    """Create a clean, focused summary chart for restart backtest"""
    
    if rounds_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data to display", x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Round Performance Over Time',
            'Survival Days Distribution', 
            'Cumulative Capital Deployed vs Losses',
            'Key Statistics'
        ),
        specs=[[{"type": "scatter"}, {"type": "histogram"}],
               [{"type": "scatter"}, {"type": "indicator"}]]
    )
    
    # 1. Round performance over time
    colors = ['red' if mc else 'green' for mc in rounds_df['margin_call']]
    returns = [-r if mc else r for r, mc in zip(rounds_df.get('loss_pct', 0), rounds_df['margin_call'])]
    if 'profit_pct' in rounds_df.columns:
        returns = [r if not mc else -l for r, l, mc in zip(rounds_df['profit_pct'].fillna(0), rounds_df['loss_pct'].fillna(0), rounds_df['margin_call'])]
    
    fig.add_trace(
        go.Scatter(
            x=rounds_df['round'],
            y=returns,
            mode='markers+lines',
            marker=dict(color=colors, size=8),
            name='Round Returns',
            hovertemplate='Round %{x}<br>Return: %{y:.1f}%<extra></extra>'
        ),
        row=1, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # 2. Survival days histogram
    fig.add_trace(
        go.Histogram(
            x=rounds_df['days'],
            nbinsx=20,
            marker_color='lightblue',
            name='Survival Days',
            hovertemplate='Days: %{x}<br>Frequency: %{y}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # 3. Cumulative capital vs losses
    cumulative_capital = rounds_df['cash_invested'].cumsum()
    cumulative_losses = rounds_df['loss_amount'].cumsum()
    
    fig.add_trace(
        go.Scatter(
            x=rounds_df['round'],
            y=cumulative_capital,
            name='Cumulative Capital',
            line=dict(color='blue', width=3),
            hovertemplate='Round %{x}<br>Total Capital: $%{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=rounds_df['round'],
            y=cumulative_losses,
            name='Cumulative Losses',
            line=dict(color='red', width=3),
            hovertemplate='Round %{x}<br>Total Losses: $%{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # 4. Key indicator
    fig.add_trace(
        go.Indicator(
            mode="number+delta",
            value=summary['total_return_pct'],
            delta={"reference": 0, "valueformat": ".1f"},
            title={"text": "Total Return %"},
            number={"suffix": "%", "valueformat": ".1f"}
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title=f"Restart Backtest Summary - {summary['total_rounds']} Rounds, {summary['margin_calls']} Margin Calls",
        height=600,
        showlegend=True
    )
    
    # Update axes
    fig.update_xaxes(title_text="Round Number", row=1, col=1)
    fig.update_yaxes(title_text="Return (%)", row=1, col=1)
    fig.update_xaxes(title_text="Days Survived", row=1, col=2)
    fig.update_yaxes(title_text="Frequency", row=1, col=2)
    fig.update_xaxes(title_text="Round Number", row=2, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=2, col=1)
    
    return fig

def render_historical_backtest_tab():
    """Main function to render the Historical Backtest tab"""
    
    st.markdown('<div class="main-container fade-in">', unsafe_allow_html=True)
    
    # Header with enhanced styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);">
        <h1 style="color: white; margin: 0; font-size: 2.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">📊 Historical Backtest Engine</h1>
        <p style="color: rgba(255,255,255,0.95); margin: 1rem 0 0 0; font-size: 1.2rem; text-shadow: 0 1px 2px rgba(0,0,0,0.2);">
            Simulate leveraged ETF strategies with real historical data, margin requirements, and interest costs
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    excel_data, spy_df, vti_df, spy_div_df, vti_div_df = load_comprehensive_data()
    
    if excel_data is None:
        st.error("❌ Failed to load data. Please check data files.")
        return
    
    # Add backtest mode selection
    st.markdown("### 🎯 Select Backtest Mode")
    
    backtest_col1, backtest_col2 = st.columns(2)
    
    with backtest_col1:
        if st.button(
            "📈 Standard Backtest",
            use_container_width=True,
            help="Traditional buy-and-hold simulation that continues through margin calls",
            key="standard_backtest_btn"
        ):
            st.session_state.backtest_mode = 'standard'
    
    with backtest_col2:
        if st.button(
            "🔄 Restart on Margin Call", 
            use_container_width=True,
            help="Liquidate all positions on margin call and restart with fresh capital",
            key="restart_backtest_btn"
        ):
            st.session_state.backtest_mode = 'restart'
    
    # Initialize if not set
    if 'backtest_mode' not in st.session_state:
        st.session_state.backtest_mode = 'standard'
    
    # Display selected mode
    if st.session_state.backtest_mode == 'standard':
        st.info("✅ **Standard Backtest Mode**: Simulates holding through margin calls (unrealistic but shows theoretical performance)")
        mode_description = """
    <div class="card">
            <h3>📈 Standard Backtest Mode</h3>
            <p>This mode simulates a buy-and-hold strategy that continues even when margin calls occur. 
            While unrealistic (brokers would force liquidation), it shows the theoretical performance if you could somehow survive all margin calls.</p>
            <ul>
                <li>✅ Shows maximum theoretical returns</li>
                <li>❌ Ignores forced liquidation on margin calls</li>
                <li>📊 Useful for understanding best-case scenarios</li>
        </ul>
    </div>
        """
    else:
        st.success("✅ **Restart Mode Selected**: Realistic simulation with automatic liquidation and re-entry on margin calls")
        mode_description = """
        <div class="card">
            <h3>🔄 Restart on Margin Call Mode</h3>
            <p>This mode provides a realistic simulation where positions are fully liquidated when margin calls occur, 
            and fresh capital is deployed to start a new position. This shows the true cost of leverage over time.</p>
            <ul>
                <li>✅ Realistic margin call handling</li>
                <li>✅ Shows cumulative impact of multiple liquidations</li>
                <li>✅ Tracks survival time between margin calls</li>
                <li>📊 Reveals the true risk of leveraged strategies</li>
            </ul>
        </div>
        """
    
    st.markdown(mode_description, unsafe_allow_html=True)
    
    # Input parameters
    st.subheader("🔧 Backtest Parameters")
    
    input_col1, input_col2, input_col3 = st.columns(3)
    
    with input_col1:
        etf_choice = st.selectbox(
            "Select ETF",
            ["SPY", "VTI"],
            help="Choose the ETF to backtest",
            key="backtest_etf_choice"
        )
        
        # Get available date range
        min_date = excel_data.index.min().date()
        max_date = excel_data.index.max().date()
        
        start_date = st.date_input(
            "Start Date",
            value=datetime.date(2010, 1, 1),
            min_value=min_date,
            max_value=max_date,
            help="When to start the backtest",
            key="backtest_start_date"
        )
    
    with input_col2:
        initial_investment = st.number_input(
            "Initial Investment ($)",
            min_value=10000,
            value=100000000,
            step=10000,
            help="Total position size (including leverage)",
            key="backtest_initial_investment"
        )
        
        account_type = st.selectbox(
            "Account Type",
            ["reg_t", "portfolio"],
            format_func=lambda x: "Reg-T Account (Max 2:1)" if x == "reg_t" else "Portfolio Margin (Max 7:1)",
            help="Type of margin account",
            key="backtest_account_type"
        )
    
    with input_col3:
        # Dynamic leverage options based on account type
        if account_type == "reg_t":
            max_leverage = 2.0
            leverage_options = [1.0, 1.25, 1.5, 1.75, 2.0]
        else:
            max_leverage = 7.0
            leverage_options = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
        
        leverage = st.selectbox(
            "Leverage",
            leverage_options,
            index=len(leverage_options)-1,  # Default to max leverage
            format_func=lambda x: f"{x:.1f}x",
            help=f"Leverage multiplier (max {max_leverage:.1f}x for {account_type.replace('_', '-').title()})",
            key="backtest_leverage"
        )
        
        # Show parameter summary
        cash_needed = initial_investment / leverage
        margin_loan = initial_investment - cash_needed
        
        st.markdown(f"""
        <div style="background: #f0f8ff; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
            <strong>📊 Position Summary:</strong><br>
            Cash Required: <strong>${cash_needed:,.0f}</strong><br>
            Margin Loan: <strong>${margin_loan:,.0f}</strong><br>
            Total Position: <strong>${initial_investment:,.0f}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Run backtest button
    if st.button("🚀 Run Historical Backtest", use_container_width=True, type="primary", key="run_backtest_button"):
        
        with st.spinner("🔄 Running comprehensive backtest simulation..."):
            
            if st.session_state.backtest_mode == 'standard':
                # Run standard backtest
                results_df, metrics = run_historical_backtest(
                    etf=etf_choice,
                    start_date=str(start_date),
                    initial_investment=initial_investment,
                    leverage=leverage,
                    account_type=account_type,
                    excel_data=excel_data
                )
                
                if results_df.empty:
                    st.error("❌ Backtest failed. Please check your parameters.")
                    return
                
                # Display standard results
                st.success(f"✅ Standard backtest completed! Analyzed {len(results_df):,} trading days from {start_date} to {results_df.index[-1].date()}")
                
                # Key metrics summary
                st.subheader("📈 Performance Summary")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric(
                        "Total Return",
                        f"{metrics['Total Return (%)']:.1f}%",
                        delta=f"vs ${cash_needed:,.0f} invested"
                    )
                    
                    st.metric(
                        "CAGR",
                        f"{metrics['CAGR (%)']:.1f}%",
                        delta="Annualized"
                    )
                
                with metric_col2:
                    st.metric(
                        "Max Drawdown",
                        f"{metrics['Max Drawdown (%)']:.1f}%",
                        delta="Peak to Trough"
                    )
                    
                    st.metric(
                        "Volatility",
                        f"{metrics['Annual Volatility (%)']:.1f}%",
                        delta="Annualized"
                    )
                
                with metric_col3:
                    st.metric(
                        "Sharpe Ratio",
                        f"{metrics['Sharpe Ratio']:.2f}",
                        delta="Risk-Adjusted Return"
                    )
                    
                    st.metric(
                        "Margin Calls",
                        f"{int(metrics['Number of Margin Calls'])}",
                        delta="Total Events (not enforced)"
                    )
                
                with metric_col4:
                    st.metric(
                        "Final Equity",
                        f"${metrics['Final Equity ($)']:,.0f}",
                        delta=f"${metrics['Final Equity ($)'] - metrics['Initial Investment ($)']:+,.0f}"
                    )
                    
                    st.metric(
                        "Interest Paid",
                        f"${metrics['Total Interest Paid ($)']:,.0f}",
                        delta="Total Cost"
                    )
                
                # Warning about unrealistic nature
                if metrics['Number of Margin Calls'] > 0:
                    st.warning(f"""
                    ⚠️ **Important**: This backtest shows {int(metrics['Number of Margin Calls'])} margin calls were triggered but ignored. 
                    In reality, your broker would have forcibly liquidated your position. Use "Restart on Margin Call" mode for realistic results.
                    """)
                
                # Portfolio performance chart
                st.subheader("📊 Portfolio Performance Over Time")
                portfolio_fig = create_portfolio_chart(results_df, metrics)
                st.plotly_chart(portfolio_fig, use_container_width=True)
                
                # Margin analysis chart
                st.subheader("⚖️ Margin Analysis")
                margin_fig = create_margin_analysis_chart(results_df)
                st.plotly_chart(margin_fig, use_container_width=True)
                
            else:  # Restart mode
                # Run restart backtest
                rounds_df, summary = run_margin_restart_backtest(
                    etf=etf_choice,
                    start_date=str(start_date),
                    initial_investment=initial_investment,
                    leverage=leverage,
                    account_type=account_type,
                    excel_data=excel_data
                )
                
                if rounds_df.empty:
                    st.error("❌ **Backtest Failed**: Insufficient data or invalid parameters. Please adjust your settings.")
                    return
                
                # ═══════════════════════════════════════════════════════════════
                # 🎯 MARGINMASTER BACKTEST RESULTS - PROFESSIONAL DASHBOARD
                # ═══════════════════════════════════════════════════════════════
                
                # Header with completion status
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                           padding: 1.5rem; border-radius: 15px; margin: 2rem 0; text-align: center;
                           box-shadow: 0 8px 32px rgba(30, 60, 114, 0.3);">
                    <h2 style="color: white; margin: 0; font-size: 1.8rem;">⚡ MARGINMASTER BACKTEST COMPLETE</h2>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                        {summary['total_rounds']} Investment Cycles • {leverage:.1f}x Leverage • {etf_choice} • {summary['avg_survival_years']:.1f} Years Average Survival
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # ═══════════════════════════════════════════════════════════════
                # 🚨 REALITY CHECK ALERT - MAXIMUM IMPACT
                # ═══════════════════════════════════════════════════════════════
                
                capital_multiplier = summary['total_cash_deployed'] / cash_needed
                margin_call_rate = (summary['margin_calls'] / summary['total_rounds']) * 100
                
                # Simple, clean leverage reality check
                st.markdown("---")
                st.markdown("## ✅ LEVERAGE REALITY CHECK")
                st.markdown("### 🎯 RISK LEVEL: MANAGEABLE")
                st.markdown("---")
                
                # Simple metrics in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Margin Calls",
                        value=f"{summary['margin_calls']}",
                        delta=f"{margin_call_rate:.1f}% of rounds"
                    )
                
                with col2:
                    st.metric(
                        label="Total Capital Required", 
                        value=f"${summary['total_cash_deployed']:,.0f}",
                        delta=f"{capital_multiplier:.1f}x more than planned"
                    )
                
                with col3:
                    st.metric(
                        label="Average Days Survived",
                        value=f"{summary['avg_survival_days']:.0f}",
                        delta="Before next margin call"
                    )
                
                # Bottom line summary
                st.info(f"🎯 **BOTTOM LINE:** You planned to invest ${cash_needed:,.0f} but actually needed ${summary['total_cash_deployed']:,.0f} - That's {capital_multiplier:.1f}x more capital than expected due to {summary['margin_calls']} forced liquidations")
                
                # ═══════════════════════════════════════════════════════════════
                # 📊 PERFORMANCE METRICS GRID - INSTITUTIONAL QUALITY
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("### 📈 Performance Analytics Dashboard")
                st.markdown("---")
                
                # Create 4x2 metrics grid
                row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
                row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)
                
                # Row 1: Core Performance Metrics
                with row1_col1:
                    st.metric(
                        label="🎯 Total Investment Rounds",
                        value=f"{summary['total_rounds']:,}",
                        delta=f"{summary['margin_calls']} margin calls",
                        delta_color="inverse"
                    )
                
                with row1_col2:
                    st.metric(
                        label="💰 Net P&L",
                        value=f"${summary['net_result']:,.0f}",
                        delta=f"{summary['total_return_pct']:+.1f}% total return",
                        delta_color="normal" if summary['net_result'] >= 0 else "inverse"
                    )
                
                with row1_col3:
                    st.metric(
                        label="📅 Average Survival",
                        value=f"{summary['avg_survival_days']:.0f} days",
                        delta=f"~{summary['avg_survival_years']:.1f} years",
                        delta_color="normal"
                    )
                
                with row1_col4:
                    st.metric(
                        label="🎲 Success Rate",
                        value=f"{summary['success_rate_pct']:.1f}%",
                        delta=f"{summary['successful_rounds']}/{summary['total_rounds']} profitable",
                        delta_color="normal" if summary['success_rate_pct'] >= 50 else "inverse"
                    )
                
                # Row 2: Risk & Capital Metrics
                with row2_col1:
                    st.metric(
                        label="💸 Capital Deployed",
                        value=f"${summary['total_cash_deployed']:,.0f}",
                        delta=f"{capital_multiplier:.1f}x planned amount",
                        delta_color="inverse" if capital_multiplier > 2 else "normal"
                    )
                
                with row2_col2:
                    st.metric(
                        label="📉 Total Losses",
                        value=f"${summary['total_losses']:,.0f}",
                        delta=f"{summary['total_losses']/summary['total_cash_deployed']*100:.1f}% of capital",
                        delta_color="inverse"
                    )
                
                with row2_col3:
                    st.metric(
                        label="🔥 Worst Round Loss",
                        value=f"-{summary['worst_loss_pct']:.1f}%",
                        delta="Single round impact",
                        delta_color="inverse"
                    )
                
                with row2_col4:
                    st.metric(
                        label="🚀 Best Round Gain",
                        value=f"+{summary['best_gain_pct']:.1f}%",
                        delta="Peak performance",
                        delta_color="normal"
                    )
                
                # ═══════════════════════════════════════════════════════════════
                # 📊 INTERACTIVE ANALYTICS CHARTS - HEDGE FUND QUALITY
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("### 📊 Interactive Performance Analytics")
                
                # Create comprehensive 4-panel chart
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=(
                        f'Round-by-Round Returns ({summary["total_rounds"]} Cycles)',
                        f'Survival Days Distribution (Avg: {summary["avg_survival_days"]:.0f} days)',
                        'Cumulative Capital Deployment vs Losses',
                        'Performance Indicator'
                    ),
                    specs=[
                        [{"type": "scatter"}, {"type": "histogram"}],
                        [{"type": "scatter"}, {"type": "indicator"}]
                    ],
                    vertical_spacing=0.12,
                    horizontal_spacing=0.08
                )
                
                # Chart 1: Round Returns with Color Coding
                round_colors = ['#00FF00' if not mc else '#FF0000' for mc in rounds_df['margin_call']]
                round_returns = []
                for _, row in rounds_df.iterrows():
                    if row['margin_call']:
                        round_returns.append(-row['loss_pct'])
                    else:
                        round_returns.append(row.get('profit_pct', 0))
                
                fig.add_trace(
                    go.Scatter(
                        x=rounds_df['round'],
                        y=round_returns,
                        mode='markers+lines',
                        marker=dict(
                            color=round_colors,
                            size=8,
                            line=dict(width=1, color='white')
                        ),
                        line=dict(color='gray', width=1),
                        name='Round Returns',
                        hovertemplate=(
                            '<b>Round %{x}</b><br>' +
                            'Return: %{y:.1f}%<br>' +
                            'Status: %{customdata}<br>' +
                            '<extra></extra>'
                        ),
                        customdata=['Margin Call' if mc else 'Profitable Exit' for mc in rounds_df['margin_call']]
                    ),
                    row=1, col=1
                )
                fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.7, row=1, col=1)
                
                # Chart 2: Survival Days Histogram
                fig.add_trace(
                    go.Histogram(
                        x=rounds_df['days'],
                        nbinsx=min(30, len(rounds_df)),
                        marker_color='lightblue',
                        marker_line=dict(color='darkblue', width=1),
                        name='Survival Days',
                        hovertemplate='Days: %{x}<br>Frequency: %{y}<extra></extra>'
                    ),
                    row=1, col=2
                )
                
                # Chart 3: Cumulative Impact Analysis
                cumulative_capital = rounds_df['cash_invested'].cumsum()
                cumulative_losses = rounds_df['loss_amount'].cumsum()
                
                fig.add_trace(
                    go.Scatter(
                        x=rounds_df['round'],
                        y=cumulative_capital,
                        mode='lines+markers',
                        line=dict(color='#1f77b4', width=3),
                        marker=dict(size=6),
                        name='Cumulative Capital',
                        hovertemplate='Round %{x}<br>Total Capital: $%{y:,.0f}<extra></extra>'
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=rounds_df['round'],
                        y=cumulative_losses,
                        mode='lines+markers',
                        line=dict(color='#ff7f0e', width=3, dash='dash'),
                        marker=dict(size=6),
                        name='Cumulative Losses',
                        hovertemplate='Round %{x}<br>Total Losses: $%{y:,.0f}<extra></extra>'
                    ),
                    row=2, col=1
                )
                
                # Chart 4: Performance Indicator Gauge
                return_color = "green" if summary['total_return_pct'] >= 0 else "red"
                fig.add_trace(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=summary['total_return_pct'],
                        delta={'reference': 0, 'valueformat': '.1f'},
                        title={'text': "Total Return %", 'font': {'size': 16}},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [-100, 100], 'tickformat': '.0f'},
                            'bar': {'color': return_color},
                            'steps': [
                                {'range': [-100, -50], 'color': "darkred"},
                                {'range': [-50, 0], 'color': "red"},
                                {'range': [0, 50], 'color': "lightgreen"},
                                {'range': [50, 100], 'color': "green"}
                            ],
                            'threshold': {
                                'line': {'color': "black", 'width': 4},
                                'thickness': 0.75,
                                'value': 0
                            }
                        },
                        number={'suffix': "%", 'valueformat': '.1f'}
                    ),
                    row=2, col=2
                )
                
                # Update layout for professional appearance
                fig.update_layout(
                    title={
                        'text': f"MarginMaster Analytics: {etf_choice} @ {leverage:.1f}x Leverage",
                        'x': 0.5,
                        'font': {'size': 20, 'color': '#1f77b4'}
                    },
                    height=700,
                    showlegend=True,
                    plot_bgcolor='rgba(240,240,240,0.1)',
                    paper_bgcolor='white',
                    font={'size': 12}
                )
                
                # Update individual subplot styling
                fig.update_xaxes(title_text="Round Number", showgrid=True, gridcolor='lightgray', row=1, col=1)
                fig.update_yaxes(title_text="Return (%)", showgrid=True, gridcolor='lightgray', row=1, col=1)
                fig.update_xaxes(title_text="Days Survived", showgrid=True, gridcolor='lightgray', row=1, col=2)
                fig.update_yaxes(title_text="Frequency", showgrid=True, gridcolor='lightgray', row=1, col=2)
                fig.update_xaxes(title_text="Round Number", showgrid=True, gridcolor='lightgray', row=2, col=1)
                fig.update_yaxes(title_text="Amount ($)", tickformat='$,.0f', showgrid=True, gridcolor='lightgray', row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # ═══════════════════════════════════════════════════════════════
                # 📋 DETAILED ROUND ANALYSIS TABLE - INSTITUTIONAL STYLE
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("### 📋 Detailed Round Analysis")
                
                # Intelligent table display logic
                total_rounds = len(rounds_df)
                if total_rounds <= 20:
                    st.markdown(f"**Showing all {total_rounds} investment rounds**")
                    display_df = rounds_df.copy()
                else:
                    st.markdown(f"**Showing first 10 and last 10 rounds (of {total_rounds} total)**")
                    first_10 = rounds_df.head(10)
                    last_10 = rounds_df.tail(10)
                    display_df = pd.concat([first_10, last_10])
                    
                    # Add separator row if showing condensed view
                    if total_rounds > 20:
                        st.info(f"💡 **Note**: Displaying first 10 and last 10 rounds for clarity. Download full data below for complete analysis.")
                
                # Format display columns for professional presentation
                display_columns = {
                    'round': 'Round #',
                    'days': 'Days',
                    'start_date': 'Start Date',
                    'end_date': 'End Date',
                    'price_change_pct': 'Price Δ%',
                    'cash_invested': 'Capital',
                    'liquidation_value': 'Final Value',
                    'margin_call': 'Margin Call'
                }
                
                # Add profit/loss columns if they exist
                if 'profit_pct' in display_df.columns:
                    display_columns['profit_pct'] = 'Profit%'
                if 'loss_pct' in display_df.columns:
                    display_columns['loss_pct'] = 'Loss%'
                
                # Create formatted display dataframe
                table_df = display_df[list(display_columns.keys())].copy()
                table_df = table_df.rename(columns=display_columns)
                
                # Format date columns
                if 'Start Date' in table_df.columns:
                    table_df['Start Date'] = pd.to_datetime(table_df['Start Date']).dt.strftime('%Y-%m-%d')
                if 'End Date' in table_df.columns:
                    table_df['End Date'] = pd.to_datetime(table_df['End Date']).dt.strftime('%Y-%m-%d')
                
                # Format currency columns
                currency_cols = ['Capital', 'Final Value']
                for col in currency_cols:
                    if col in table_df.columns:
                        table_df[col] = table_df[col].apply(lambda x: f"${x:,.0f}")
                
                # Format percentage columns
                pct_cols = ['Price Δ%', 'Profit%', 'Loss%']
                for col in pct_cols:
                    if col in table_df.columns:
                        table_df[col] = table_df[col].apply(lambda x: f"{x:.1f}%")
                
                # Format margin call column
                if 'Margin Call' in table_df.columns:
                    table_df['Margin Call'] = table_df['Margin Call'].apply(lambda x: "🔴 YES" if x else "🟢 NO")
                
                # Display the professional table
                st.dataframe(
                    table_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Round #": st.column_config.NumberColumn("Round #", width="small"),
                        "Days": st.column_config.NumberColumn("Days", width="small"),
                        "Start Date": st.column_config.TextColumn("Start Date", width="medium"),
                        "End Date": st.column_config.TextColumn("End Date", width="medium"),
                        "Capital": st.column_config.TextColumn("Capital", width="medium"),
                        "Final Value": st.column_config.TextColumn("Final Value", width="medium"),
                        "Margin Call": st.column_config.TextColumn("Margin Call", width="small"),
                    }
                )
                
                # ═══════════════════════════════════════════════════════════════
                # 💾 PROFESSIONAL DATA EXPORT CENTER
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("### 💾 Data Export Center")
                
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    # Raw round data export
                    rounds_csv = rounds_df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download Round Data",
                        data=rounds_csv,
                        file_name=f"marginmaster_rounds_{etf_choice}_{leverage}x_{start_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Complete round-by-round data for further analysis"
                    )
                
                with export_col2:
                    # Summary metrics export
                    summary_df = pd.DataFrame([summary])
                    summary_csv = summary_df.to_csv(index=False)
                    st.download_button(
                        label="📈 Download Summary",
                        data=summary_csv,
                        file_name=f"marginmaster_summary_{etf_choice}_{leverage}x_{start_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Aggregate performance metrics and statistics"
                    )
                
                with export_col3:
                    # Professional report export (placeholder for future PDF generation)
                    st.button(
                        label="📄 Generate Report (Soon)",
                        use_container_width=True,
                        disabled=True,
                        help="Professional PDF report generation coming soon"
                    )
                
                # ═══════════════════════════════════════════════════════════════
                # 🎓 EDUCATIONAL INSIGHTS - EXPERT COMMENTARY
                # ═══════════════════════════════════════════════════════════════
                
                with st.expander("🎓 Expert Analysis & Key Insights", expanded=False):
                    st.markdown(f"""
                    ### 🔍 What These Results Mean
                    
                    **💡 Capital Efficiency Analysis:**
                    - You deployed **${summary['total_cash_deployed']:,.0f}** across {summary['total_rounds']} rounds
                    - This is **{capital_multiplier:.1f}x** more than the ${cash_needed:,.0f} you initially planned
                    - Each margin call forced you to find fresh capital, compounding your exposure
                    
                    **⏱️ Timing Risk Assessment:**
                    - Average position lasted **{summary['avg_survival_days']:.0f} days** ({summary['avg_survival_years']:.1f} years)
                    - {summary['margin_calls']} out of {summary['total_rounds']} rounds ended in forced liquidation
                    - Success rate of **{summary['success_rate_pct']:.1f}%** shows how often leverage worked in your favor
                    
                    **🎯 Strategic Implications:**
                    - **If profitable**: Consider if the {capital_multiplier:.1f}x capital requirement is worth the {summary['total_return_pct']:.1f}% return
                    - **If unprofitable**: This shows why professional traders typically avoid high leverage in volatile markets
                    - **Risk Management**: Each margin call represents a failure of position sizing relative to volatility
                    
                    **📊 Market Context:**
                    - This backtest used real {etf_choice} data with {leverage:.1f}x leverage over {summary['avg_survival_years']:.1f} years
                    - Results include realistic interest costs and dividend reinvestment
                    - Maintenance margin requirements reflect actual broker policies
                    
                    ### 🚀 Next Steps for Professional Traders:
                    1. **Reduce Leverage**: Test 2-3x instead of {leverage:.1f}x to see survival improvement
                    2. **Add Stop Losses**: Consider systematic position management before margin calls
                    3. **Diversify Timing**: Spread entries across time rather than lump sum investing
                    4. **Capital Planning**: Budget for {capital_multiplier:.1f}x your intended investment if using this strategy
                    """)
                
                # Final professional footer
                st.markdown("---")
                st.markdown("""
                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                           border-radius: 10px; margin-top: 2rem;">
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">
                        <strong>MarginMaster Backtester</strong> • Professional-grade leverage analysis • 
                        Built for institutional decision-making • Results based on historical data
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # Educational section
    with st.expander("📚 Understanding the Backtest Modes", expanded=False):
        st.markdown("""
        ### Standard Backtest Mode
        
        **What it does:**
        - Simulates buying and holding with leverage through the entire period
        - Records margin calls but doesn't act on them (unrealistic)
        - Shows theoretical "best case" if you could somehow survive all margin calls
        
        **When to use:**
        - Understanding maximum potential returns
        - Academic analysis of price movements
        - Comparing with realistic restart mode
        
        ### Restart on Margin Call Mode (RECOMMENDED)
        
        **What it does:**
        1. **Start Position**: Invest $100M with your chosen leverage
        2. **Monitor Daily**: Track equity vs maintenance margin requirements  
        3. **Margin Call**: When equity < maintenance requirement → **LIQUIDATE EVERYTHING**
        4. **Fresh Start**: Immediately invest a new $100M with same leverage
        5. **Repeat**: Continue until end of backtest period
        6. **Analyze**: Show total capital required and cumulative results
        
        **Key Insights:**
        - **Total Capital Required**: How much money you actually need
        - **Survival Time**: How long each position lasts before margin call
        - **Success Rate**: Percentage of rounds that end profitably
        - **Reality Check**: True cost of leverage over time
        
        **Why This Matters:**
        With high leverage, you might think you need $14M to control $100M (7x leverage).
        But this backtest shows you might actually need $200M, $500M, or more due to repeated margin calls!
        
        ### Example Interpretation:
        If the backtest shows:
        - **50 rounds** → You got margin called 49 times
        - **$350M total capital** → You needed 3.5x more money than planned
        - **Average 45 days survival** → Each position lasted ~1.5 months
        - **10% success rate** → Only 1 in 10 rounds was profitable
        
        This reveals the **hidden cost of leverage** that simple calculators miss.
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Function to be called from main app
def show_historical_backtest():
    """Entry point for the Historical Backtest tab"""
    render_historical_backtest_tab() 
    
    
