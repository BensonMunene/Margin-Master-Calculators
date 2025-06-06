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
    """Load ALL required data from ONLY the ETFs and Fed Funds Data.xlsx file"""
    try:
        # Define directory paths
        local_dir = r"D:\Benson\aUpWork\Ben Ruff\Implementation\Data"
        github_dir = "Data"
        
        # Choose which directory to use (True for local, False for GitHub)
        use_local = True
        data_dir = local_dir if use_local else github_dir
        
        # Load ONLY the Excel file - it contains everything we need
        excel_path = f"{data_dir}/ETFs and Fed Funds Data.xlsx"
        excel_data = pd.read_excel(excel_path)
        
        # Process the Excel data
        excel_data['Date'] = pd.to_datetime(excel_data['Unnamed: 0'])
        excel_data.set_index('Date', inplace=True)
        excel_data = excel_data.drop('Unnamed: 0', axis=1)
        
        # The Excel file contains everything: SPY, VTI, dividends, and Fed Funds
        # No need for separate CSV files
        return excel_data, None, None, None, None
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.error("Please ensure ETFs and Fed Funds Data.xlsx is in the Data/ directory")
        st.error("This file should contain: SPY prices, VTI prices, dividends, and Fed Funds rates")
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
def run_liquidation_reentry_backtest(
    etf: str,
    start_date: str,
    initial_investment: float,
    leverage: float,
    account_type: str,
    excel_data: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Advanced backtest with realistic margin call liquidation and re-entry logic.
    
    Strategy:
    1. Enter position with specified leverage
    2. Monitor for margin calls daily
    3. On margin call: liquidate immediately, wait 2 days
    4. Re-enter with remaining equity at same leverage
    5. Continue until equity depleted or backtest period ends
    
    Returns comprehensive daily tracking and sophisticated metrics.
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
        st.error("Insufficient data for the selected date range")
        return pd.DataFrame(), {}
    
    # Initialize tracking variables
    current_equity = initial_investment / leverage  # Starting cash
    min_equity_threshold = 1000  # Stop trading if equity falls below this
    wait_days_after_liquidation = 2
    
    # Comprehensive daily tracking
    daily_results = []
    liquidation_events = []
    
    # State variables
    in_position = False
    wait_days_remaining = 0
    shares_held = 0.0
    margin_loan = 0.0
    cycle_number = 0
    days_in_current_position = 0
    
    # Performance tracking
    total_liquidations = 0
    total_interest_paid = 0.0
    total_dividends_received = 0.0
    max_equity_achieved = current_equity
    
    # Main simulation loop
    for i, (date, row) in enumerate(data.iterrows()):
        current_price = row[price_col]
        dividend_payment = row[dividend_col] if pd.notna(row[dividend_col]) else 0.0
        fed_funds_rate = row['FedFunds (%)'] / 100.0
        
        # Calculate interest rate for this day
        daily_interest_rate = (fed_funds_rate + margin_params['margin_rate_spread'] / 100.0) / 365
        
        # Initialize daily result
        daily_result = {
            'Date': date,
            'ETF_Price': current_price,
            'Current_Equity': current_equity,
            'In_Position': in_position,
            'Wait_Days_Remaining': wait_days_remaining,
            'Cycle_Number': cycle_number,
            'Days_In_Position': days_in_current_position,
            'Fed_Funds_Rate': fed_funds_rate * 100,
            'Margin_Rate': (fed_funds_rate + margin_params['margin_rate_spread'] / 100.0) * 100
        }
        
        # Handle waiting period after liquidation
        if wait_days_remaining > 0:
            wait_days_remaining -= 1
            daily_result.update({
                'Shares_Held': 0,
                'Portfolio_Value': 0,
                'Margin_Loan': 0,
                'Equity': current_equity,
                'Maintenance_Margin_Required': 0,
                'Is_Margin_Call': False,
                'Daily_Interest_Cost': 0,
                'Dividend_Payment': 0,
                'Position_Status': 'Waiting_After_Liquidation'
            })
            daily_results.append(daily_result)
            continue
        
        # Check if we should enter a new position
        if not in_position and current_equity >= min_equity_threshold:
            # Enter new position
            position_value = current_equity * leverage
            shares_held = position_value / current_price
            margin_loan = position_value - current_equity
            in_position = True
            cycle_number += 1
            days_in_current_position = 0
            
            # Record position entry
            daily_result['Position_Status'] = 'Position_Entered'
            
        elif not in_position:
            # Insufficient equity to continue trading
            daily_result.update({
                'Shares_Held': 0,
                'Portfolio_Value': 0,
                'Margin_Loan': 0,
                'Equity': current_equity,
                'Maintenance_Margin_Required': 0,
                'Is_Margin_Call': False,
                'Daily_Interest_Cost': 0,
                'Dividend_Payment': 0,
                'Position_Status': 'Insufficient_Equity'
            })
            daily_results.append(daily_result)
            continue
        
        # If in position, update position metrics
        if in_position:
            days_in_current_position += 1
            
            # Calculate daily interest cost
            daily_interest_cost = margin_loan * daily_interest_rate
            margin_loan += daily_interest_cost
            total_interest_paid += daily_interest_cost
            
            # Handle dividend payments
            dividend_received = 0
            if dividend_payment > 0:
                dividend_received = shares_held * dividend_payment
                total_dividends_received += dividend_received
                # Reinvest dividends (buy more shares)
                additional_shares = dividend_received / current_price
                shares_held += additional_shares
            
            # Calculate current position values
            portfolio_value = shares_held * current_price
            current_equity_in_position = portfolio_value - margin_loan
            maintenance_margin_required = portfolio_value * (margin_params['maintenance_margin_pct'] / 100.0)
            
            # Check for margin call
            is_margin_call = current_equity_in_position < maintenance_margin_required
            
            if is_margin_call:
                # LIQUIDATION EVENT
                liquidation_value = max(0, current_equity_in_position)
                loss_amount = current_equity - liquidation_value
                
                # Record liquidation event
                liquidation_events.append({
                    'date': date,
                    'cycle_number': cycle_number,
                    'days_in_position': days_in_current_position,
                    'entry_equity': current_equity,
                    'liquidation_equity': liquidation_value,
                    'loss_amount': loss_amount,
                    'loss_percentage': (loss_amount / current_equity) * 100 if current_equity > 0 else 0,
                    'price_at_entry': data[price_col].iloc[i - days_in_current_position] if i >= days_in_current_position else current_price,
                    'price_at_liquidation': current_price,
                    'interest_paid_this_cycle': daily_interest_cost * days_in_current_position  # Approximation
                })
                
                # Update state after liquidation
                current_equity = liquidation_value
                max_equity_achieved = max(max_equity_achieved, current_equity)
                total_liquidations += 1
                in_position = False
                wait_days_remaining = wait_days_after_liquidation
                shares_held = 0
                margin_loan = 0
                days_in_current_position = 0
                
                daily_result['Position_Status'] = 'Liquidated'
            else:
                daily_result['Position_Status'] = 'Active_Position'
                current_equity = current_equity_in_position  # Update equity
                max_equity_achieved = max(max_equity_achieved, current_equity)
            
            # Update daily result with position data
            daily_result.update({
                'Shares_Held': shares_held,
                'Portfolio_Value': portfolio_value if in_position else 0,
                'Margin_Loan': margin_loan if in_position else 0,
                'Equity': current_equity,
                'Maintenance_Margin_Required': maintenance_margin_required if in_position else 0,
                'Is_Margin_Call': is_margin_call,
                'Daily_Interest_Cost': daily_interest_cost if in_position else 0,
                'Dividend_Payment': dividend_received,
                'Margin_Call_Price': margin_loan / (shares_held * (1 - margin_params['maintenance_margin_pct'] / 100.0)) if shares_held > 0 else 0
            })
        
        daily_results.append(daily_result)
    
    # Convert to DataFrame
    df_results = pd.DataFrame(daily_results)
    df_results.set_index('Date', inplace=True)
    
    if df_results.empty:
        return df_results, {}
    
    # Calculate comprehensive performance metrics
    initial_cash = initial_investment / leverage
    final_equity = df_results['Equity'].iloc[-1]
    total_return = (final_equity - initial_cash) / initial_cash * 100
    
    # Calculate time-based metrics
    total_days = len(df_results)
    years = total_days / 252  # Trading days per year
    
    if years > 0 and final_equity > 0:
        cagr = ((final_equity / initial_cash) ** (1 / years) - 1) * 100
    else:
        cagr = 0
    
    # Risk metrics
    equity_series = df_results['Equity']
    daily_returns = equity_series.pct_change().dropna()
    
    if len(daily_returns) > 1:
        annual_volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = cagr / annual_volatility if annual_volatility > 0 else 0
        
        # Advanced risk metrics
        negative_returns = daily_returns[daily_returns < 0]
        downside_volatility = negative_returns.std() * np.sqrt(252) * 100 if len(negative_returns) > 0 else 0
        sortino_ratio = cagr / downside_volatility if downside_volatility > 0 else 0
        
        # Maximum drawdown analysis
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Drawdown duration analysis
        drawdown_periods = (drawdown < 0).astype(int)
        drawdown_lengths = []
        current_length = 0
        for dd in drawdown_periods:
            if dd == 1:
                current_length += 1
            else:
                if current_length > 0:
                    drawdown_lengths.append(current_length)
                current_length = 0
        if current_length > 0:
            drawdown_lengths.append(current_length)
        
        max_drawdown_duration = max(drawdown_lengths) if drawdown_lengths else 0
        avg_drawdown_duration = np.mean(drawdown_lengths) if drawdown_lengths else 0
    else:
        annual_volatility = 0
        sharpe_ratio = 0
        sortino_ratio = 0
        max_drawdown = 0
        max_drawdown_duration = 0
        avg_drawdown_duration = 0
    
    # Position and liquidation analytics
    active_position_days = len(df_results[df_results['In_Position'] == True])
    waiting_days = len(df_results[df_results['Wait_Days_Remaining'] > 0])
    time_in_market_pct = (active_position_days / total_days) * 100 if total_days > 0 else 0
    
    # Liquidation statistics
    if liquidation_events:
        liquidation_df = pd.DataFrame(liquidation_events)
        avg_days_between_liquidations = liquidation_df['days_in_position'].mean()
        avg_loss_per_liquidation = liquidation_df['loss_percentage'].mean()
        worst_single_loss = liquidation_df['loss_percentage'].max()
    else:
        avg_days_between_liquidations = total_days
        avg_loss_per_liquidation = 0
        worst_single_loss = 0
    
    # Comprehensive metrics dictionary
    metrics = {
        # Core Performance
        'Initial Investment ($)': initial_cash,
        'Final Equity ($)': final_equity,
        'Total Return (%)': total_return,
        'CAGR (%)': cagr,
        'Max Equity Achieved ($)': max_equity_achieved,
        
        # Risk Metrics
        'Max Drawdown (%)': max_drawdown,
        'Annual Volatility (%)': annual_volatility,
        'Downside Volatility (%)': downside_volatility,
        'Sharpe Ratio': sharpe_ratio,
        'Sortino Ratio': sortino_ratio,
        
        # Drawdown Analysis
        'Max Drawdown Duration (days)': max_drawdown_duration,
        'Avg Drawdown Duration (days)': avg_drawdown_duration,
        
        # Trading Statistics
        'Total Liquidations': total_liquidations,
        'Total Cycles': cycle_number,
        'Time in Market (%)': time_in_market_pct,
        'Active Position Days': active_position_days,
        'Waiting Days': waiting_days,
        
        # Liquidation Analytics
        'Avg Days Between Liquidations': avg_days_between_liquidations,
        'Avg Loss Per Liquidation (%)': avg_loss_per_liquidation,
        'Worst Single Loss (%)': worst_single_loss,
        
        # Cost Analysis
        'Total Interest Paid ($)': total_interest_paid,
        'Total Dividends Received ($)': total_dividends_received,
        'Net Interest Cost ($)': total_interest_paid - total_dividends_received,
        
        # Strategy Parameters
        'Leverage Used': leverage,
        'Account Type': account_type,
        'Backtest Days': total_days,
        'Backtest Years': years
    }
    
    return df_results, metrics

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

def create_enhanced_portfolio_chart(df_results: pd.DataFrame, metrics: Dict[str, float]) -> go.Figure:
    """Create sophisticated institutional-grade portfolio performance chart"""
    
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=(
            'Equity Evolution & Liquidation Events', 'Position Status Timeline',
            'Drawdown Analysis & Recovery', 'Daily Returns Distribution', 
            'Rolling Performance Metrics', 'Interest Rate Environment',
            'Cumulative P&L Attribution', 'Risk-Adjusted Performance'
        ),
        specs=[
            [{"colspan": 2}, None],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "histogram"}],
            [{"type": "scatter"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08,
        row_heights=[0.3, 0.25, 0.25, 0.2]
    )
    
    # Main equity chart with enhanced annotations
    equity_line = go.Scatter(
        x=df_results.index,
        y=df_results['Equity'],
        name='Equity',
        line=dict(color='#2E86C1', width=3),
        hovertemplate='Date: %{x}<br>Equity: $%{y:,.0f}<br><extra></extra>'
    )
    fig.add_trace(equity_line, row=1, col=1)
    
    # Add liquidation events as red markers
    liquidations = df_results[df_results['Position_Status'] == 'Liquidated']
    if not liquidations.empty:
        fig.add_trace(
            go.Scatter(
                x=liquidations.index,
                y=liquidations['Equity'],
                mode='markers',
                name='Liquidations',
                marker=dict(
                    color='red', 
                    size=12, 
                    symbol='triangle-down',
                    line=dict(color='darkred', width=2)
                ),
                hovertemplate='LIQUIDATION<br>Date: %{x}<br>Remaining Equity: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Add position entries as green markers
    entries = df_results[df_results['Position_Status'] == 'Position_Entered']
    if not entries.empty:
        fig.add_trace(
            go.Scatter(
                x=entries.index,
                y=entries['Equity'],
                mode='markers',
                name='Position Entries',
                marker=dict(
                    color='green', 
                    size=10, 
                    symbol='triangle-up',
                    line=dict(color='darkgreen', width=2)
                ),
                hovertemplate='NEW POSITION<br>Date: %{x}<br>Entry Equity: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Position status timeline
    position_colors = {
        'Active_Position': '#28B463',
        'Waiting_After_Liquidation': '#F39C12', 
        'Liquidated': '#E74C3C',
        'Position_Entered': '#3498DB',
        'Insufficient_Equity': '#95A5A6'
    }
    
    for status, color in position_colors.items():
        status_data = df_results[df_results['Position_Status'] == status]
        if not status_data.empty:
            display_name = status.replace('_', ' ')
            hover_template = display_name + '<br>Date: %{x}<extra></extra>'
            
            fig.add_trace(
                go.Scatter(
                    x=status_data.index,
                    y=[1] * len(status_data),
                    mode='markers',
                    name=display_name,
                    marker=dict(color=color, size=4),
                    yaxis='y2',
                    hovertemplate=hover_template
                ),
                row=2, col=1
            )
    
    # Enhanced drawdown analysis
    equity_series = df_results['Equity']
    rolling_max = equity_series.expanding().max()
    drawdown = (equity_series - rolling_max) / rolling_max * 100
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=drawdown,
            name='Drawdown',
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.3)',
            line=dict(color='#E74C3C', width=2),
            hovertemplate='Date: %{x}<br>Drawdown: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Daily returns distribution
    daily_returns = equity_series.pct_change().dropna() * 100
    if len(daily_returns) > 0:
        fig.add_trace(
            go.Histogram(
                x=daily_returns,
                nbinsx=50,
                name='Daily Returns',
                marker_color='#5DADE2',
                marker_line=dict(color='#2E86C1', width=1),
                hovertemplate='Return: %{x:.2f}%<br>Frequency: %{y}<extra></extra>'
            ),
            row=3, col=2
        )
    
    # Rolling 30-day Sharpe ratio
    if len(daily_returns) >= 30:
        rolling_mean = daily_returns.rolling(30).mean()
        rolling_std = daily_returns.rolling(30).std()
        
        # Calculate rolling Sharpe ratio, handling division by zero
        rolling_sharpe = np.where(rolling_std > 0, 
                                 (rolling_mean / rolling_std) * np.sqrt(252), 
                                 0)
        
        # Use the daily_returns index for x-axis
        sharpe_dates = daily_returns.index[29:]  # Start after 30-day window
        sharpe_values = rolling_sharpe[29:]
        
        fig.add_trace(
            go.Scatter(
                x=sharpe_dates,
                y=sharpe_values,
                name='30-Day Rolling Sharpe',
                line=dict(color='#8E44AD', width=2),
                hovertemplate='Date: %{x}<br>Rolling Sharpe: %{y:.2f}<extra></extra>'
            ),
            row=3, col=1
        )
    
    # Interest rate environment
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Fed_Funds_Rate'],
            name='Fed Funds Rate',
            line=dict(color='#17A2B8', width=2),
            hovertemplate='Date: %{x}<br>Fed Funds: %{y:.2f}%<extra></extra>'
        ),
        row=4, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Margin_Rate'],
            name='Margin Rate',
            line=dict(color='#DC3545', width=2, dash='dash'),
            hovertemplate='Date: %{x}<br>Margin Rate: %{y:.2f}%<extra></extra>'
        ),
        row=4, col=1
    )
    
    # Cumulative interest costs vs dividends
    cumulative_interest = df_results['Daily_Interest_Cost'].cumsum()
    cumulative_dividends = df_results['Dividend_Payment'].cumsum()
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=-cumulative_interest,  # Negative because it's a cost
            name='Cumulative Interest Cost',
            line=dict(color='#E74C3C', width=2),
            hovertemplate='Date: %{x}<br>Interest Cost: -$%{y:,.0f}<extra></extra>'
        ),
        row=4, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=cumulative_dividends,
            name='Cumulative Dividends',
            line=dict(color='#28B463', width=2),
            hovertemplate='Date: %{x}<br>Dividends: +$%{y:,.0f}<extra></extra>'
        ),
        row=4, col=2
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"Liquidation-Reentry Backtest: {metrics.get('Leverage Used', 0):.1f}x Leverage | {metrics.get('Total Liquidations', 0)} Liquidations | {metrics.get('CAGR (%)', 0):.1f}% CAGR",
            'x': 0.5,
            'font': {'size': 16, 'color': '#2C3E50'}
        },
        height=1000,
        showlegend=True,
        legend=dict(x=1.02, y=1, bgcolor='rgba(255,255,255,0.8)'),
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    # Update axes styling
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    
    # Format specific axes
    fig.update_yaxes(tickformat='$,.0f', row=1, col=1, title_text="Equity ($)")
    fig.update_yaxes(tickformat='.1f', row=2, col=2, title_text="Drawdown (%)")
    fig.update_yaxes(tickformat='.2f', row=3, col=1, title_text="Rolling Sharpe")
    fig.update_yaxes(tickformat='.2f', row=4, col=1, title_text="Interest Rate (%)")
    fig.update_yaxes(tickformat='$,.0f', row=4, col=2, title_text="Cumulative ($)")
    
    return fig

def create_liquidation_analysis_chart(df_results: pd.DataFrame, metrics: Dict[str, float]) -> go.Figure:
    """Create comprehensive liquidation and risk analysis chart"""
    
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            'Liquidation Frequency Analysis', 'Position Survival Times', 'Equity Decay Pattern',
            'Interest Rate Impact', 'Performance Attribution', 'Risk Metrics Dashboard'
        ),
        specs=[
            [{"type": "bar"}, {"type": "histogram"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "scatter"}, {"type": "indicator"}]
        ],
        vertical_spacing=0.20,
        horizontal_spacing=0.08
    )
    
    # 1. Monthly liquidation frequency
    liquidations = df_results[df_results['Position_Status'] == 'Liquidated']
    if not liquidations.empty:
        monthly_liquidations = liquidations.groupby(liquidations.index.to_period('M')).size()
        
        fig.add_trace(
            go.Bar(
                x=[str(period) for period in monthly_liquidations.index],
                y=monthly_liquidations.values,
                name='Monthly Liquidations',
                marker_color='#E74C3C',
                hovertemplate='Month: %{x}<br>Liquidations: %{y}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # 2. Position survival time histogram
    if 'Days_In_Position' in df_results.columns:
        active_days = df_results[df_results['Days_In_Position'] > 0]['Days_In_Position']
        if not active_days.empty:
            fig.add_trace(
                go.Histogram(
                    x=active_days,
                    nbinsx=30,
                    name='Survival Days',
                    marker_color='#3498DB',
                    marker_line=dict(color='#2980B9', width=1),
                    hovertemplate='Days: %{x}<br>Frequency: %{y}<extra></extra>'
                ),
                row=1, col=2
            )
    
    # 3. Equity decay pattern with trend line
    equity_series = df_results['Equity']
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=equity_series,
            mode='lines',
            name='Equity',
            line=dict(color='#2E86C1', width=2),
            hovertemplate='Date: %{x}<br>Equity: $%{y:,.0f}<extra></extra>'
        ),
        row=1, col=3
    )
    
    # Add exponential decay trend line if equity is declining
    if len(equity_series) > 10:
        x_numeric = np.arange(len(equity_series))
        try:
            # Fit exponential decay
            log_equity = np.log(equity_series.replace(0, 1))  # Avoid log(0)
            coeffs = np.polyfit(x_numeric, log_equity, 1)
            trend_line = np.exp(coeffs[1] + coeffs[0] * x_numeric)
            
            fig.add_trace(
                go.Scatter(
                    x=df_results.index,
                    y=trend_line,
                    mode='lines',
                    name='Decay Trend',
                    line=dict(color='#E74C3C', width=2, dash='dash'),
                    hovertemplate='Trend: $%{y:,.0f}<extra></extra>'
                ),
                row=1, col=3
            )
        except:
            pass  # Skip trend line if calculation fails
    
    # 4. Interest rate impact on performance
    if 'Fed_Funds_Rate' in df_results.columns:
        # Calculate rolling correlation between fed funds rate and daily returns
        daily_returns = df_results['Equity'].pct_change() * 100
        rolling_window = 60  # 60-day window
        
        if len(daily_returns) > rolling_window:
            rolling_corr = daily_returns.rolling(rolling_window).corr(df_results['Fed_Funds_Rate'])
            
            fig.add_trace(
                go.Scatter(
                    x=df_results.index[rolling_window:],
                    y=rolling_corr.iloc[rolling_window:],
                    name='Returns-Rate Correlation',
                    line=dict(color='#9B59B6', width=2),
                    hovertemplate='Date: %{x}<br>Correlation: %{y:.3f}<extra></extra>'
                ),
                row=2, col=1
            )
    
    # 5. Performance attribution (Interest vs Dividends vs Price)
    cumulative_interest = df_results['Daily_Interest_Cost'].cumsum()
    cumulative_dividends = df_results['Dividend_Payment'].cumsum()
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=-cumulative_interest,
            name='Interest Cost',
            line=dict(color='#E74C3C', width=2),
            fill='tonexty',
            hovertemplate='Date: %{x}<br>Interest: -$%{y:,.0f}<extra></extra>'
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=cumulative_dividends,
            name='Dividend Income',
            line=dict(color='#27AE60', width=2),
            hovertemplate='Date: %{x}<br>Dividends: +$%{y:,.0f}<extra></extra>'
        ),
        row=2, col=2
    )
    
    # 6. Risk metrics gauge
    sharpe_ratio = metrics.get('Sharpe Ratio', 0)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=sharpe_ratio,
            delta={'reference': 1.0, 'valueformat': '.2f'},
            title={'text': "Sharpe Ratio", 'font': {'size': 14}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [-2, 3], 'tickformat': '.1f'},
                'bar': {'color': '#3498DB'},
                'steps': [
                    {'range': [-2, 0], 'color': "#E74C3C"},
                    {'range': [0, 1], 'color': "#F39C12"},
                    {'range': [1, 2], 'color': "#27AE60"},
                    {'range': [2, 3], 'color': "#2ECC71"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 1.0
                }
            },
            number={'valueformat': '.3f'}
        ),
        row=2, col=3
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"Advanced Risk & Liquidation Analysis | {metrics.get('Total Liquidations', 0)} Total Liquidations",
            'x': 0.5,
            'font': {'size': 16, 'color': '#2C3E50'}
        },
        height=600,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    # Update axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    
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
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.7, row=1, col=1)
    
    # 2. Survival days histogram
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
    
    # 3. Cumulative capital vs losses
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
    
    # Load data - ONLY from ETFs and Fed Funds Data.xlsx
    excel_data, _, _, _, _ = load_comprehensive_data()
    
    if excel_data is None:
        st.error("❌ Failed to load ETFs and Fed Funds Data.xlsx. Please check the Excel file.")
        return
    
    # Add backtest mode selection
    st.markdown("### 🎯 Select Backtest Mode")
    
    backtest_col1, backtest_col2 = st.columns(2)
    
    with backtest_col1:
        if st.button(
            "⚡ Liquidation-Reentry (RECOMMENDED)",
            use_container_width=True,
            help="Realistic simulation: liquidate on margin call, wait 2 days, re-enter with remaining equity",
            key="liquidation_backtest_btn"
        ):
            st.session_state.backtest_mode = 'standard'
    
    with backtest_col2:
        if st.button(
            "🔄 Fresh Capital Restart", 
            use_container_width=True,
            help="Comparison mode: unlimited fresh capital after each margin call",
            key="restart_backtest_btn"
        ):
            st.session_state.backtest_mode = 'restart'
    
    # Initialize if not set
    if 'backtest_mode' not in st.session_state:
        st.session_state.backtest_mode = 'standard'
    
    # Display selected mode
    if st.session_state.backtest_mode == 'standard':
        st.info("✅ **Enhanced Liquidation-Reentry Mode**: Realistic simulation with margin call liquidation and 2-day re-entry delay")
        mode_description = """
    <div class="card">
            <h3>⚡ Enhanced Liquidation-Reentry Strategy</h3>
            <p>This advanced backtest simulates realistic margin trading with forced liquidation and strategic re-entry:</p>
            <ul>
                <li>✅ <strong>Forced Liquidation</strong>: Immediate position closure when margin call triggered</li>
                <li>✅ <strong>2-Day Wait Period</strong>: Realistic cooling-off period after liquidation</li>
                <li>✅ <strong>Smart Re-entry</strong>: Re-enters with remaining equity using same leverage</li>
                <li>✅ <strong>Capital Tracking</strong>: Shows true cost of leverage over time</li>
                <li>✅ <strong>Institutional Metrics</strong>: Advanced risk analytics and performance attribution</li>
        </ul>
    </div>
        """
    else:
        st.success("✅ **Restart Mode Selected**: Alternative simulation with unlimited fresh capital (for comparison)")
        mode_description = """
        <div class="card">
            <h3>🔄 Restart with Fresh Capital Mode</h3>
            <p>This mode provides comparison analysis by assuming unlimited fresh capital for each restart:</p>
            <ul>
                <li>✅ Fresh $100M deployed after each margin call</li>
                <li>✅ Shows frequency and timing of margin calls</li>
                <li>✅ Tracks survival time between margin calls</li>
                <li>📊 Useful for understanding leverage frequency patterns</li>
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
                # Run enhanced liquidation-reentry backtest
                results_df, metrics = run_liquidation_reentry_backtest(
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
                
                # Display enhanced results
                st.success(f"🎯 **Liquidation-Reentry Backtest Complete!** Analyzed {len(results_df):,} trading days with {metrics.get('Total Liquidations', 0)} liquidation events")
                
                # Enhanced metrics summary with institutional-level presentation
                st.markdown("### 📊 Institutional Performance Dashboard")
                
                # Create two rows of metrics for comprehensive display
                st.markdown("#### Core Performance Metrics")
                metric_row1_col1, metric_row1_col2, metric_row1_col3, metric_row1_col4 = st.columns(4)
                
                with metric_row1_col1:
                    st.metric(
                        "Total Return",
                        f"{metrics['Total Return (%)']:.1f}%",
                        delta=f"CAGR: {metrics['CAGR (%)']:.1f}%"
                    )
                    
                with metric_row1_col2:
                    st.metric(
                        "Final Equity",
                        f"${metrics['Final Equity ($)']:,.0f}",
                        delta=f"Max: ${metrics['Max Equity Achieved ($)']:,.0f}"
                    )
                
                with metric_row1_col3:
                    st.metric(
                        "Sharpe Ratio",
                        f"{metrics['Sharpe Ratio']:.3f}",
                        delta=f"Sortino: {metrics['Sortino Ratio']:.3f}"
                    )
                    
                with metric_row1_col4:
                    st.metric(
                        "Max Drawdown",
                        f"{metrics['Max Drawdown (%)']:.1f}%",
                        delta=f"Duration: {metrics['Max Drawdown Duration (days)']:.0f} days"
                    )
                
                st.markdown("#### Trading & Risk Analytics")
                metric_row2_col1, metric_row2_col2, metric_row2_col3, metric_row2_col4 = st.columns(4)
                
                with metric_row2_col1:
                    st.metric(
                        "Total Liquidations",
                        f"{int(metrics['Total Liquidations'])}",
                        delta=f"Avg every {metrics['Avg Days Between Liquidations']:.0f} days"
                    )
                    
                with metric_row2_col2:
                    st.metric(
                        "Time in Market",
                        f"{metrics['Time in Market (%)']:.1f}%",
                        delta=f"{metrics['Active Position Days']} active days"
                    )
                
                with metric_row2_col3:
                    st.metric(
                        "Avg Loss per Liquidation",
                        f"{metrics['Avg Loss Per Liquidation (%)']:.1f}%",
                        delta=f"Worst: {metrics['Worst Single Loss (%)']:.1f}%",
                        delta_color="inverse"
                    )
                    
                with metric_row2_col4:
                    st.metric(
                        "Net Interest Cost",
                        f"${metrics['Net Interest Cost ($)']:,.0f}",
                        delta=f"Interest: ${metrics['Total Interest Paid ($)']:,.0f}"
                    )
                
                # Reality check and strategy insights
                if metrics['Total Liquidations'] > 0:
                    loss_rate = (metrics['Total Liquidations'] / metrics['Total Cycles']) * 100 if metrics['Total Cycles'] > 0 else 0
                    avg_survival = metrics['Avg Days Between Liquidations']
                    
                    if loss_rate > 80:
                        st.error(f"""
                        🚨 **HIGH RISK STRATEGY**: {loss_rate:.0f}% of positions ended in liquidation. 
                        Average survival time: {avg_survival:.0f} days. Consider reducing leverage significantly.
                        """)
                    elif loss_rate > 50:
                        st.warning(f"""
                        ⚠️ **MODERATE RISK**: {loss_rate:.0f}% liquidation rate with {avg_survival:.0f} days average survival. 
                        This strategy requires significant capital reserves and risk management.
                        """)
                    else:
                        st.info(f"""
                        💡 **Strategy Insight**: {loss_rate:.0f}% liquidation rate. Positions survived an average of {avg_survival:.0f} days. 
                        While manageable, consider position sizing and stop-loss strategies.
                        """)
                else:
                    st.success("✅ **Excellent**: No liquidations occurred during this backtest period!")
                
                # Enhanced portfolio performance chart
                st.markdown("### 📈 Institutional-Grade Performance Analytics")
                portfolio_fig = create_enhanced_portfolio_chart(results_df, metrics)
                st.plotly_chart(portfolio_fig, use_container_width=True)
                
                # Advanced liquidation and risk analysis
                st.markdown("### 🎯 Advanced Risk & Liquidation Analysis")
                liquidation_fig = create_liquidation_analysis_chart(results_df, metrics)
                st.plotly_chart(liquidation_fig, use_container_width=True)
                
                # Detailed backtest data expander for liquidation-reentry mode
                with st.expander("🔍 Detailed Backtest Data & Variables", expanded=False):
                    st.markdown(f"""
                    ### 📊 Complete Dataset: Liquidation-Reentry Backtest Results
                    
                    This dataset contains **{len(results_df):,} daily observations** from your {leverage:.1f}x leveraged {etf_choice} strategy.
                    Each row represents one trading day showing position status, liquidation events, and comprehensive metrics.
                    """)
                    
                    # Enhanced variable explanations
                    st.markdown("""
                    **📋 Variable Definitions:**
                    
                    | Variable | Description |
                    |----------|-------------|
                    | **ETF_Price** | Daily closing price of the selected ETF |
                    | **Current_Equity** | Available equity for trading (decreases with losses, increases with gains) |
                    | **In_Position** | TRUE when actively holding leveraged position |
                    | **Position_Status** | Current state: Active_Position, Liquidated, Position_Entered, Waiting_After_Liquidation |
                    | **Cycle_Number** | Sequential number of position cycles (restarts after each liquidation) |
                    | **Days_In_Position** | Number of days current position has been held |
                    | **Wait_Days_Remaining** | Days remaining in cooling-off period after liquidation |
                    | **Shares_Held** | Number of shares in current position (0 when not in position) |
                    | **Portfolio_Value** | Total market value of holdings (Shares × Price) |
                    | **Margin_Loan** | Outstanding loan balance (0 when not in position) |
                    | **Equity** | Current equity value (Portfolio_Value - Margin_Loan when in position) |
                    | **Maintenance_Margin_Required** | Minimum equity required to avoid liquidation |
                    | **Is_Margin_Call** | TRUE when liquidation is triggered |
                    | **Daily_Interest_Cost** | Interest charged on margin loan for that day |
                    | **Fed_Funds_Rate** | Federal Reserve interest rate (%) |
                    | **Margin_Rate** | Your borrowing rate (Fed Funds + spread) |
                    | **Dividend_Payment** | Dividend cash received (automatically reinvested) |
                    """)
                    
                    # Display the full dataset
                    st.markdown("### 📈 Complete Daily Data")
                    
                    # Format the dataframe for better display
                    display_df = results_df.copy()
                    
                    # Format currency columns
                    currency_cols = ['Portfolio_Value', 'Margin_Loan', 'Equity', 'Maintenance_Margin_Required', 'Daily_Interest_Cost', 'Cumulative_Dividends']
                    for col in currency_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
                    
                    # Format percentage columns
                    pct_cols = ['Fed_Funds_Rate', 'Margin_Rate']
                    for col in pct_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")
                    
                    # Format price and share columns
                    if 'ETF_Price' in display_df.columns:
                        display_df['ETF_Price'] = display_df['ETF_Price'].apply(lambda x: f"${x:.2f}")
                    if 'Shares_Held' in display_df.columns:
                        display_df['Shares_Held'] = display_df['Shares_Held'].apply(lambda x: f"{x:,.2f}")
                    if 'Margin_Call_Price' in display_df.columns:
                        display_df['Margin_Call_Price'] = display_df['Margin_Call_Price'].apply(lambda x: f"${x:.2f}")
                    if 'Dividend_Payment' in display_df.columns:
                        display_df['Dividend_Payment'] = display_df['Dividend_Payment'].apply(lambda x: f"${x:.4f}")
                    
                    # Format boolean column
                    if 'Is_Margin_Call' in display_df.columns:
                        display_df['Is_Margin_Call'] = display_df['Is_Margin_Call'].apply(lambda x: "🔴 YES" if x else "🟢 NO")
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        height=400,
                        column_config={
                            "ETF_Price": st.column_config.TextColumn("ETF Price", width="small"),
                            "Shares_Held": st.column_config.TextColumn("Shares", width="medium"),
                            "Portfolio_Value": st.column_config.TextColumn("Portfolio Value", width="medium"),
                            "Margin_Loan": st.column_config.TextColumn("Margin Loan", width="medium"),
                            "Equity": st.column_config.TextColumn("Equity", width="medium"),
                            "Is_Margin_Call": st.column_config.TextColumn("Margin Call", width="small"),
                        }
                    )
                    
                    # Download option for detailed data
                    detailed_csv = results_df.to_csv()
                    st.download_button(
                        label="📊 Download Complete Dataset",
                        data=detailed_csv,
                        file_name=f"detailed_backtest_data_{etf_choice}_{leverage}x_{start_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download all daily calculations for external analysis"
                    )
                
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
                # 🔍 DETAILED BACKTEST DATA & VARIABLES - RESTART MODE
                # ═══════════════════════════════════════════════════════════════
                
                with st.expander("🔍 Detailed Backtest Data & Variables", expanded=False):
                    st.markdown(f"""
                    ### 📊 Complete Dataset: Restart Backtest Results
                    
                    This dataset contains **{len(rounds_df):,} investment rounds** from your {leverage:.1f}x leveraged {etf_choice} strategy.
                    Each row represents one complete investment cycle from entry to liquidation/profit-taking.
                    """)
                    
                    # Variable explanations for restart mode
                    st.markdown("""
                    **📋 Variable Definitions:**
                    
                    | Variable | Description |
                    |----------|-------------|
                    | **round** | Sequential round number (1, 2, 3...) |
                    | **start_date** | Date when this round's position was opened |
                    | **end_date** | Date when position was closed (margin call or end of data) |
                    | **days** | Number of calendar days the position was held |
                    | **start_price** | ETF price when position opened |
                    | **end_price** | ETF price when position closed |
                    | **price_change_pct** | Percentage change in ETF price during this round |
                    | **cash_invested** | Your cash contribution for this round |
                    | **liquidation_value** | Final equity value when position closed |
                    | **loss_amount** | Dollar loss if margin call occurred |
                    | **loss_pct** | Percentage loss relative to cash invested |
                    | **interest_paid** | Total interest costs during this round |
                    | **dividends_received** | Total dividends collected during this round |
                    | **margin_call** | TRUE if round ended due to margin call |
                    """)
                    
                    # Add profit columns if they exist
                    if 'profit_amount' in rounds_df.columns:
                        st.markdown("| **profit_amount** | Dollar profit if round ended successfully |")
                    if 'profit_pct' in rounds_df.columns:
                        st.markdown("| **profit_pct** | Percentage profit relative to cash invested |")
                    
                    # Display the full dataset
                    st.markdown("### 📈 Complete Round-by-Round Data")
                    
                    # Format the dataframe for better display
                    display_df = rounds_df.copy()
                    
                    # Format date columns
                    date_cols = ['start_date', 'end_date']
                    for col in date_cols:
                        if col in display_df.columns:
                            display_df[col] = pd.to_datetime(display_df[col]).dt.strftime('%Y-%m-%d')
                    
                    # Format currency columns
                    currency_cols = ['cash_invested', 'liquidation_value', 'loss_amount', 'interest_paid', 'dividends_received']
                    if 'profit_amount' in display_df.columns:
                        currency_cols.append('profit_amount')
                    
                    for col in currency_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
                    
                    # Format percentage columns
                    pct_cols = ['price_change_pct', 'loss_pct']
                    if 'profit_pct' in display_df.columns:
                        pct_cols.append('profit_pct')
                    
                    for col in pct_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")
                    
                    # Format price columns
                    price_cols = ['start_price', 'end_price']
                    for col in price_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"${x:.2f}")
                    
                    # Format boolean column
                    if 'margin_call' in display_df.columns:
                        display_df['margin_call'] = display_df['margin_call'].apply(lambda x: "🔴 YES" if x else "🟢 NO")
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        height=400,
                        column_config={
                            "round": st.column_config.NumberColumn("Round", width="small"),
                            "days": st.column_config.NumberColumn("Days", width="small"),
                            "start_date": st.column_config.TextColumn("Start Date", width="medium"),
                            "end_date": st.column_config.TextColumn("End Date", width="medium"),
                            "start_price": st.column_config.TextColumn("Start Price", width="small"),
                            "end_price": st.column_config.TextColumn("End Price", width="small"),
                            "cash_invested": st.column_config.TextColumn("Cash Invested", width="medium"),
                            "liquidation_value": st.column_config.TextColumn("Final Value", width="medium"),
                            "margin_call": st.column_config.TextColumn("Margin Call", width="small"),
                        }
                    )
                    
                    # Download option for detailed data
                    detailed_csv = rounds_df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download Complete Round Data",
                        data=detailed_csv,
                        file_name=f"detailed_rounds_data_{etf_choice}_{leverage}x_{start_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download all round-by-round calculations for external analysis"
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
    with st.expander("📚 Understanding the Enhanced Backtest Modes", expanded=False):
        st.markdown("""
        ### ⚡ Liquidation-Reentry Mode (RECOMMENDED)
        
        **Advanced Realistic Simulation:**
        This is the **most sophisticated and realistic** backtest mode, designed by quants for institutional-level analysis.
        
        **Exact Process:**
        1. **Initial Entry**: Start with your cash investment, leverage up to desired position size
        2. **Daily Monitoring**: Track equity vs maintenance margin requirements with real interest costs
        3. **Forced Liquidation**: When equity < maintenance requirement → **IMMEDIATE LIQUIDATION**
        4. **Cooling Period**: Wait 2 trading days (simulates broker restrictions and emotional recovery)
        5. **Smart Re-entry**: Re-enter with remaining equity using same leverage ratio
        6. **Cycle Tracking**: Continue until equity depleted or backtest period ends
        
        **Key Advantages:**
        - ✅ **Realistic Capital Requirements**: Shows true capital needed vs theoretical
        - ✅ **Psychological Modeling**: 2-day wait simulates real trader behavior
        - ✅ **Compound Impact**: Reveals how losses compound over multiple cycles
        - ✅ **Risk Attribution**: Separates interest costs, dividends, and price impact
        - ✅ **Institutional Metrics**: Advanced risk analytics (Sortino, drawdown duration, etc.)
        
        ### 🔄 Fresh Capital Restart Mode (COMPARISON)
        
        **Theoretical Analysis Tool:**
        This mode assumes unlimited capital for comparison purposes.
        
        **Process:**
        1. **Start Position**: Deploy full position size with leverage
        2. **Margin Call**: Liquidate when margin call triggered
        3. **Fresh Capital**: Immediately deploy NEW full position (unlimited money assumption)
        4. **Frequency Analysis**: Track how often margin calls occur
        
        **When to Use:**
        - Academic comparison with liquidation-reentry mode
        - Understanding margin call frequency patterns
        - Analyzing market volatility impact on leverage strategies
        
        ### 🎯 Professional Interpretation Guide
        
        **Liquidation-Reentry Results Analysis:**
        
        **If Total Return > 0%:**
        - Strategy worked but analyze capital efficiency
        - Check if returns justify the liquidation frequency
        - Consider if same returns achievable with lower leverage
        
        **If Total Return < -50%:**
        - High-risk strategy requiring significant capital reserves
        - Consider reducing leverage by 50% and re-testing
        - Evaluate if strategy suitable for your risk tolerance
        
        **Key Metrics to Watch:**
        - **Liquidation Rate**: <30% good, 30-70% moderate risk, >70% high risk
        - **Average Survival Days**: >180 days stable, 30-180 moderate, <30 very risky
        - **Sharpe Ratio**: >1.0 good risk-adjusted returns, <0 poor strategy
        - **Max Drawdown Duration**: <90 days recoverable, >365 days concerning
        
        **Professional Risk Management:**
        - Use **position sizing**: Start with 25% of planned capital to test
        - Implement **stop losses**: Exit at -20% to -30% loss levels
        - Consider **leverage stepping**: Start at 2x, gradually increase if successful
        - **Diversify timing**: Dollar-cost average entries instead of lump sum
        """)

    # Professional Summary Footer
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; margin: 2rem 0; text-align: center;">
        <h3 style="color: white; margin: 0;">🎯 Quant-Level Historical Backtest Engine</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 1rem 0 0 0; font-size: 1.1rem;">
            <strong>Enhanced Features:</strong> Liquidation-Reentry Logic | 2-Day Cooling Periods | Advanced Risk Analytics<br/>
            <strong>Institutional Metrics:</strong> Sortino Ratio | Drawdown Duration Analysis | Performance Attribution<br/>
            <strong>Sophisticated Visualization:</strong> 8-Panel Analytics Dashboard | Interactive Risk Analysis | Position Status Tracking
        </p>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Built for professional traders and institutional analysts | Real market data | Comprehensive risk modeling
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Function to be called from main app
def show_historical_backtest():
    """Entry point for the Historical Backtest tab"""
    render_historical_backtest_tab() 
    
    
