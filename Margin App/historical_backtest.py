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

# Cushion analytics import
import cushion_analysis

# Parameter sweep import (optional)
try:
    import parameter_sweep
except ImportError:
    parameter_sweep = None

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
            'maintenance_margin_pct': 25.0
        }
    else:  # portfolio margin
        return {
            'max_leverage': 7.0,
            'initial_margin_pct': max(100.0 / leverage, 14.29),  # Dynamic based on leverage
            'maintenance_margin_pct': 15.0
        }

@st.cache_data
def run_liquidation_reentry_backtest(
    etf: str,
    start_date: str,
    end_date: str,
    initial_investment: float,
    leverage: float,
    account_type: str,
    excel_data: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, float], List[Dict]]:
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
    
    # Prepare data with date range
    data = excel_data.loc[start_date:end_date].copy()
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
    round_analysis = []  # Track complete position cycles
    
    # State variables
    in_position = False
    wait_days_remaining = 0
    shares_held = 0.0
    margin_loan = 0.0
    cycle_number = 0
    days_in_current_position = 0
    
    # Round tracking variables
    round_start_date = None
    round_start_price = None
    round_start_portfolio_value = None
    round_start_equity = None
    
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
        
        # Use IBKR rates directly from Excel data
        margin_rate = row['FedFunds + 1.5%'] / 100.0  # Convert percentage to decimal
        daily_interest_rate = margin_rate / 365
        
        # On Day 1 (i==0), we just enter positions at close - no interest/dividends yet
        # Starting Day 2 (i>=1), we calculate interest, dividends, and other changes
        
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
            'Margin_Rate': margin_rate * 100
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
                'Cumulative_Interest_Cost': total_interest_paid,
                'Dividend_Payment': 0,
                'Cumulative_Dividends': total_dividends_received,
                'Position_Status': 'Waiting'
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
            
            # Record round start information
            round_start_date = date
            round_start_price = current_price
            round_start_portfolio_value = position_value
            round_start_equity = current_equity
            
            # Record position entry
            daily_result['Position_Status'] = 'Entered'
            
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
                'Cumulative_Interest_Cost': total_interest_paid,
                'Dividend_Payment': 0,
                'Cumulative_Dividends': total_dividends_received,
                'Position_Status': 'Insufficient_Equity'
            })
            daily_results.append(daily_result)
            continue
        
        # If in position, update position metrics
        if in_position:
            days_in_current_position += 1
            
            # Calculate daily interest cost - ONLY after Day 1
            daily_interest_cost = 0
            if i > 0:
                daily_interest_cost = margin_loan * daily_interest_rate
                margin_loan += daily_interest_cost
                total_interest_paid += daily_interest_cost
            
            # Handle dividend payments - ONLY after Day 1
            dividend_received = 0
            if i > 0 and dividend_payment > 0:
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
                
                # Record complete round analysis
                if round_start_date is not None:
                    price_change_pct = ((current_price - round_start_price) / round_start_price) * 100 if round_start_price > 0 else 0
                    final_portfolio_value = portfolio_value
                    
                    round_analysis.append({
                        'Round': cycle_number,
                        'Days': days_in_current_position,
                        'Start_Date': round_start_date,
                        'End_Date': date,
                        'Start_Price': round_start_price,
                        'End_Price': current_price,
                        'Price_Change_Pct': price_change_pct,
                        'Start_Portfolio_Value': round_start_portfolio_value,
                        'End_Portfolio_Value': final_portfolio_value,
                        'Start_Equity': round_start_equity,
                        'End_Equity': liquidation_value,
                        'Capital_Deployed': round_start_equity,
                        'Final_Value': liquidation_value,
                        'Margin_Call': True,
                        'Loss_Pct': (loss_amount / round_start_equity) * 100 if round_start_equity > 0 else 0,
                        'Profit_Pct': 0.0,
                        'Interest_Paid': daily_interest_cost * days_in_current_position
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
                daily_result['Position_Status'] = 'Active'
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
                'Cumulative_Interest_Cost': total_interest_paid,
                'Dividend_Payment': dividend_received,
                'Cumulative_Dividends': total_dividends_received,
                'Margin_Call_Price': margin_loan / (shares_held * (1 - margin_params['maintenance_margin_pct'] / 100.0)) if shares_held > 0 else 0
            })
        
        daily_results.append(daily_result)
    
    # Handle final round if position still active at end of backtest
    if in_position and round_start_date is not None:
        price_change_pct = ((current_price - round_start_price) / round_start_price) * 100 if round_start_price > 0 else 0
        final_portfolio_value = portfolio_value
        final_equity = current_equity_in_position
        profit_amount = final_equity - round_start_equity
        
        round_analysis.append({
            'Round': cycle_number,
            'Days': days_in_current_position,
            'Start_Date': round_start_date,
            'End_Date': date,
            'Start_Price': round_start_price,
            'End_Price': current_price,
            'Price_Change_Pct': price_change_pct,
            'Start_Portfolio_Value': round_start_portfolio_value,
            'End_Portfolio_Value': final_portfolio_value,
            'Start_Equity': round_start_equity,
            'End_Equity': final_equity,
            'Capital_Deployed': round_start_equity,
            'Final_Value': final_equity,
            'Margin_Call': False,
            'Loss_Pct': 0.0,
            'Profit_Pct': (profit_amount / round_start_equity) * 100 if round_start_equity > 0 else 0,
            'Interest_Paid': daily_interest_cost * days_in_current_position
        })
    
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
        'Equity ($)': initial_cash,
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
    
    return df_results, metrics, round_analysis

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
        
        # Use IBKR rates directly from Excel data
        margin_rate = row['FedFunds + 1.5%'] / 100.0  # Convert percentage to decimal
        daily_interest_rate = margin_rate / 365
        
        # On Day 1 (i==0), we just enter the position at close - no interest/dividends yet
        # Starting Day 2 (i>=1), we calculate interest, dividends, and other changes
        
        # Calculate daily interest cost - ONLY after Day 1
        daily_interest_cost = 0
        if i > 0:
            daily_interest_cost = margin_loan * daily_interest_rate
        
        # Handle dividend reinvestment - ONLY after Day 1
        if i > 0 and dividend_payment > 0:
            dividend_received = shares * dividend_payment
            # Reinvest dividends (buy more shares)
            additional_shares = dividend_received / current_price
            shares += additional_shares
        
        # Calculate portfolio value
        portfolio_value = shares * current_price
        equity = portfolio_value - margin_loan
        
        # Update margin loan with accrued interest - ONLY after Day 1
        if i > 0:
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
            'Margin_Rate': margin_rate * 100,
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
        'Equity ($)': cash_investment,
        'Leverage Used': leverage
    }
    
    return df_results, metrics


@st.cache_data
def run_profit_threshold_backtest(
    etf: str,
    start_date: str,
    end_date: str,
    initial_investment: float,
    target_leverage: float,
    account_type: str,
    excel_data: pd.DataFrame,
    profit_threshold_pct: float = 100.0,
    transaction_cost_bps: float = 5.0
) -> Tuple[pd.DataFrame, Dict[str, float], List[Dict]]:
    """
    Profit Threshold Rebalancing Backtest with Liquidation-Reentry Logic
    ===================================================================
    
    This implements a growth-based rebalancing strategy that:
    1. Monitors portfolio growth percentage from initial position
    2. When growth hits threshold (e.g., 100%), rebalances back to target leverage
    3. Only borrows more to buy additional shares (never sells)
    4. Locks in profits by scaling position size with consistent leverage exposure
    5. Continues trading after liquidation with 2-day wait period (like Liquidation-Reentry mode)
    
    Key Logic:
    - Start with target leverage (e.g., 2x)
    - Monitor portfolio value vs growth threshold
    - When portfolio grows by threshold % → check if leverage dropped below target
    - If yes → borrow more to restore target leverage with new equity base
    - **If margin call**: liquidate, wait 2 days, then re-enter with remaining equity
    - Track all rebalancing events and growth milestones
    
    Example:
    - Start: $1M equity @ 2x = $2M position
    - Growth: Portfolio grows to $4M (100% growth)
    - Current leverage: $4M ÷ $3M equity = 1.33x (below 2x target)
    - Rebalance: Borrow $2M more → $6M position @ 2x leverage
    - If liquidated: wait 2 days, restart with remaining equity
    """
    
    # Get margin parameters
    margin_params = calculate_margin_params(account_type, target_leverage)
    
    # Prepare data with date range
    data = excel_data.loc[start_date:end_date].copy()
    if etf == 'SPY':
        price_col, dividend_col = 'SPY', 'SPY_Dividends'
    else:
        price_col, dividend_col = 'VTI', 'VTI_Dividends'
    
    data = data.dropna(subset=[price_col, 'FedFunds (%)'])
    
    if len(data) < 10:
        st.error("Insufficient data for the selected date range")
        return pd.DataFrame(), {}, []
    
    # Initialize portfolio with target leverage
    initial_equity = initial_investment / target_leverage
    current_equity = initial_equity
    min_equity_threshold = 1000  # Stop trading if equity falls below this
    
    # Transaction cost (basis points to decimal)
    transaction_cost_rate = transaction_cost_bps / 10000.0
    
    # Tracking variables for profit threshold strategy
    daily_results = []
    rebalancing_events = []
    liquidation_events = []
    
    # State variables for liquidation-reentry logic
    shares_held = 0.0
    margin_loan = 0.0
    total_transaction_costs = 0.0
    total_rebalances = 0
    total_liquidations = 0
    total_interest_paid = 0.0
    total_dividends_received = 0.0
    days_since_rebalance = 0
    
    # Position tracking for liquidation-reentry
    in_position = False
    wait_days_remaining = 0
    wait_days_after_liquidation = 2
    cycle_number = 0
    days_in_current_position = 0
    
    # Growth tracking
    initial_position_value = 0  # Will be set when first position is actually entered
    last_rebalance_position_value = 0  # Track for next rebalance trigger
    first_position_entered = False  # Track if we've ever entered a position
    max_equity_achieved = current_equity
    
    # Main simulation loop - PROFIT THRESHOLD WITH LIQUIDATION-REENTRY LOGIC
    for i, (date, row) in enumerate(data.iterrows()):
        current_price = row[price_col]
        dividend_payment = row[dividend_col] if pd.notna(row[dividend_col]) else 0.0
        fed_funds_rate = row['FedFunds (%)'] / 100.0
        margin_rate = row['FedFunds + 1.5%'] / 100.0
        daily_interest_rate = margin_rate / 365
        
        # On Day 1 (i==0), we just enter positions at close - no interest/dividends yet
        # Starting Day 2 (i>=1), we calculate interest, dividends, and other changes
        
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
            'Margin_Rate': margin_rate * 100
        }
        
        # Handle waiting period after liquidation
        if wait_days_remaining > 0:
            wait_days_remaining -= 1
            portfolio_value = 0
            actual_leverage = 0
            daily_result.update({
                'Position_Status': 'Waiting'
            })
        
        # Check if we should enter a new position
        elif not in_position and current_equity >= min_equity_threshold:
            # Enter new position with target leverage
            position_value = current_equity * target_leverage
            shares_held = position_value / current_price
            margin_loan = position_value - current_equity
            in_position = True
            cycle_number += 1
            days_in_current_position = 0
            days_since_rebalance = 0
            
            # Set growth tracking baselines correctly
            if not first_position_entered:
                # This is the very first position - set the baseline for total growth tracking
                initial_position_value = position_value
                first_position_entered = True
            
            # Always reset the rebalance tracking for new position
            last_rebalance_position_value = position_value
            
            daily_result.update({
                'Position_Status': 'Entered'
            })
            
        elif not in_position:
            # Insufficient equity to continue trading
            portfolio_value = 0
            actual_leverage = 0
            daily_result.update({
                'Position_Status': 'Insufficient_Equity'
            })
        
        # Initialize variables that will be used in daily results (always define them)
        daily_interest_cost = 0
        dividend_received = 0
        transaction_cost_today = 0
        rebalanced = False
        
        # If in position, update position metrics and check for profit threshold rebalancing
        if in_position:
            days_in_current_position += 1
            days_since_rebalance += 1
            
            # Calculate daily interest cost - ONLY after Day 1
            if i > 0:
                daily_interest_cost = margin_loan * daily_interest_rate
                margin_loan += daily_interest_cost
                total_interest_paid += daily_interest_cost
            
            # Handle dividend payments - ONLY after Day 1
            if i > 0 and dividend_payment > 0:
                dividend_received = shares_held * dividend_payment
                total_dividends_received += dividend_received
                # Reinvest dividends (buy more shares)
                additional_shares = dividend_received / current_price
                shares_held += additional_shares
            
            # Calculate current position values
            portfolio_value = shares_held * current_price
            current_equity_in_position = portfolio_value - margin_loan
            maintenance_margin_required = portfolio_value * (margin_params['maintenance_margin_pct'] / 100.0)
            
            # PROFIT THRESHOLD REBALANCING LOGIC (only if not on entry day)
            if i > 0:  # Don't rebalance on entry day
                # Check for profit threshold trigger
                growth_pct = ((portfolio_value - last_rebalance_position_value) / last_rebalance_position_value) * 100 if last_rebalance_position_value > 0 else 0
                
                # Trigger rebalancing if growth exceeds threshold
                if growth_pct >= profit_threshold_pct:
                    # Calculate current leverage
                    current_leverage = portfolio_value / current_equity_in_position if current_equity_in_position > 0 else 0
                    
                    # Only rebalance if leverage dropped below target (due to growth)
                    if current_leverage < target_leverage * 0.95:  # Small buffer to avoid tiny rebalances
                        # Calculate target portfolio value to maintain leverage
                        target_portfolio_value = current_equity_in_position * target_leverage
                        target_shares = target_portfolio_value / current_price
                        
                        # Calculate additional shares needed
                        shares_change = target_shares - shares_held
                        
                        if shares_change > 0.01:  # Only buy more shares
                            # Calculate transaction cost
                            trade_value = shares_change * current_price
                            transaction_cost_today = trade_value * transaction_cost_rate
                            total_transaction_costs += transaction_cost_today
                            current_equity_in_position -= transaction_cost_today  # Transaction costs reduce equity
                            
                            # Adjust for transaction costs in target calculation
                            adjusted_target_portfolio_value = current_equity_in_position * target_leverage
                            target_shares = adjusted_target_portfolio_value / current_price
                            
                            # Update position - buy more shares
                            shares_held = target_shares
                            margin_loan = adjusted_target_portfolio_value - current_equity_in_position
                            
                            # Record rebalancing event
                            rebalancing_events.append({
                                'date': date,
                                'growth_trigger_pct': growth_pct,
                                'shares_change': shares_change,
                                'transaction_cost': transaction_cost_today,
                                'equity_before': current_equity_in_position + transaction_cost_today,
                                'equity_after': current_equity_in_position,
                                'leverage_before': current_leverage,
                                'leverage_after': target_leverage,
                                'portfolio_value_before': portfolio_value,
                                'portfolio_value_after': adjusted_target_portfolio_value,
                                'rebalance_type': 'PROFIT_THRESHOLD_REBALANCE'
                            })
                            
                            total_rebalances += 1
                            rebalanced = True
                            days_since_rebalance = 0
                            last_rebalance_position_value = adjusted_target_portfolio_value
            
            # Recalculate final values after rebalancing
            portfolio_value = shares_held * current_price
            current_equity_in_position = portfolio_value - margin_loan
            actual_leverage = portfolio_value / current_equity_in_position if current_equity_in_position > 0 else 0
            maintenance_margin_required = portfolio_value * (margin_params['maintenance_margin_pct'] / 100.0)
            
            # Check for margin call
            is_margin_call = current_equity_in_position < maintenance_margin_required
            
            if is_margin_call:
                # LIQUIDATION EVENT - Start waiting period and then re-enter
                liquidation_value = max(0, current_equity_in_position)
                
                liquidation_events.append({
                    'date': date,
                    'cycle_number': cycle_number,
                    'days_in_position': days_in_current_position,
                    'liquidation_equity': liquidation_value,
                    'portfolio_value_before': portfolio_value,
                    'leverage_before': actual_leverage,
                    'maintenance_margin_shortfall': maintenance_margin_required - current_equity_in_position
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
                days_since_rebalance = 0
                last_rebalance_position_value = 0
                
                daily_result.update({
                    'Position_Status': 'Liquidated'
                })
            else:
                daily_result.update({
                    'Position_Status': 'Active'
                })
                current_equity = current_equity_in_position  # Update equity
                max_equity_achieved = max(max_equity_achieved, current_equity)
        
        # Update performance tracking for no-position states
        if not in_position and wait_days_remaining == 0:
            max_equity_achieved = max(max_equity_achieved, current_equity)
        
        # Calculate growth metrics
        total_growth_pct = ((portfolio_value - initial_position_value) / initial_position_value) * 100 if initial_position_value > 0 and portfolio_value > 0 else 0
        since_last_rebalance_pct = ((portfolio_value - last_rebalance_position_value) / last_rebalance_position_value) * 100 if last_rebalance_position_value > 0 and portfolio_value > 0 else 0
        
        # Calculate leverage drift for analytics
        leverage_drift = abs(actual_leverage - target_leverage) if actual_leverage > 0 else 0
        
        # Calculate margin call price
        margin_call_price = 0
        if shares_held > 0 and margin_loan > 0:
            margin_call_price = margin_loan / (shares_held * (1 - margin_params['maintenance_margin_pct'] / 100.0))
        
        # Store comprehensive daily results
        daily_result.update({
            'Shares_Held': shares_held,
            'Portfolio_Value': portfolio_value,
            'Margin_Loan': margin_loan,
            'Equity': current_equity,
            'Target_Leverage': target_leverage,
            'Actual_Leverage': actual_leverage,
            'Leverage_Drift': leverage_drift,
            'Maintenance_Margin_Required': maintenance_margin_required if in_position else 0,
            'Is_Margin_Call': is_margin_call if in_position else False,
            'Daily_Interest_Cost': daily_interest_cost if in_position else 0,
            'Cumulative_Interest_Cost': total_interest_paid,
            'Dividend_Payment': dividend_received if in_position else 0,
            'Cumulative_Dividends': total_dividends_received,
            'Transaction_Cost_Today': transaction_cost_today if in_position else 0,
            'Cumulative_Transaction_Costs': total_transaction_costs,
            'Days_Since_Rebalance': days_since_rebalance,
            'Rebalanced_Today': rebalanced if in_position else False,
            'Total_Growth_Pct': total_growth_pct,
            'Growth_Since_Last_Rebalance_Pct': since_last_rebalance_pct,
            'Profit_Threshold_Pct': profit_threshold_pct,
            'Next_Rebalance_Target': last_rebalance_position_value * (1 + profit_threshold_pct/100) if last_rebalance_position_value > 0 else 0,
            'Margin_Call_Price': margin_call_price
        })
        
        daily_results.append(daily_result)
    
    # Convert to DataFrame
    df_results = pd.DataFrame(daily_results)
    df_results.set_index('Date', inplace=True)
    
    if df_results.empty:
        return df_results, {}, []
    
    # Calculate comprehensive performance metrics
    final_equity = df_results['Equity'].iloc[-1]
    total_return = (final_equity - initial_equity) / initial_equity * 100
    
    # Calculate time-based metrics
    total_days = len(df_results)
    years = total_days / 252
    
    if years > 0 and final_equity > 0:
        cagr = ((final_equity / initial_equity) ** (1 / years) - 1) * 100
    else:
        cagr = 0
    
    # Risk metrics
    equity_series = df_results['Equity']
    daily_returns = equity_series.pct_change().dropna()
    
    if len(daily_returns) > 1:
        annual_volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = cagr / annual_volatility if annual_volatility > 0 else 0
        
        # Maximum drawdown
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Leverage statistics
        leverage_series = df_results['Actual_Leverage']
        # Only calculate leverage stats if we have valid leverage data
        leverage_mask = leverage_series > 0
        if leverage_mask.any():
            avg_leverage = leverage_series[leverage_mask].mean()
            max_leverage = leverage_series.max()
            min_leverage = leverage_series[leverage_mask].min()
            leverage_volatility = leverage_series[leverage_mask].std()
        else:
            avg_leverage = target_leverage
            max_leverage = target_leverage
            min_leverage = target_leverage
            leverage_volatility = 0
        
        # Leverage drift statistics  
        if len(df_results) > 0:
            leverage_drift_avg = df_results['Leverage_Drift'].mean()
        else:
            leverage_drift_avg = 0
        
        # Rebalancing statistics
        if 'Days_Since_Rebalance' in df_results.columns and total_rebalances > 0:
            avg_days_between_rebalance = df_results['Days_Since_Rebalance'].mean()
        else:
            avg_days_between_rebalance = total_days if total_rebalances == 0 else total_days / total_rebalances
        
        # Growth statistics
        max_total_growth = df_results['Total_Growth_Pct'].max()
        final_total_growth = df_results['Total_Growth_Pct'].iloc[-1]
        
    else:
        annual_volatility = 0
        sharpe_ratio = 0
        max_drawdown = 0
        avg_leverage = target_leverage
        max_leverage = target_leverage
        min_leverage = target_leverage
        leverage_volatility = 0
        leverage_drift_avg = 0
        avg_days_between_rebalance = 0
        max_total_growth = 0
        final_total_growth = 0
    
    # Comprehensive metrics
    metrics = {
        # Core Performance
        'Equity ($)': initial_equity,
        'Final Equity ($)': final_equity,
        'Total Return (%)': total_return,
        'CAGR (%)': cagr,
        'Max Equity Achieved ($)': max_equity_achieved,
        
        # Risk Metrics
        'Max Drawdown (%)': max_drawdown,
        'Annual Volatility (%)': annual_volatility,
        'Sharpe Ratio': sharpe_ratio,
        
        # Leverage Analytics
        'Target Leverage': target_leverage,
        'Average Actual Leverage': avg_leverage,
        'Max Leverage': max_leverage,
        'Min Leverage': min_leverage,
        'Leverage Volatility': leverage_volatility,
        'Average Leverage Drift': leverage_drift_avg,
        
        # Profit Threshold Analytics
        'Profit Threshold (%)': profit_threshold_pct,
        'Total Rebalances': total_rebalances,
        'Average Days Between Rebalances': avg_days_between_rebalance,
        'Max Portfolio Growth (%)': max_total_growth,
        'Final Portfolio Growth (%)': final_total_growth,
        'Total Transaction Costs ($)': total_transaction_costs,
        'Transaction Cost (% of Equity)': (total_transaction_costs / initial_equity) * 100,
        
        # Cost Analysis
        'Total Interest Paid ($)': total_interest_paid,
        'Total Dividends Received ($)': total_dividends_received,
        'Net Interest Cost ($)': total_interest_paid - total_dividends_received,
        'All-In Cost ($)': total_interest_paid + total_transaction_costs - total_dividends_received,
        
        # Trading Statistics
        'Total Liquidations': total_liquidations,
        'Backtest Days': total_days,
        'Backtest Years': years,
        'Account Type': account_type,
        'Initial Position Value': initial_position_value
    }
    
    return df_results, metrics, rebalancing_events

@st.cache_data
def run_margin_restart_backtest(
    etf: str,
    start_date: str,
    end_date: str,
    initial_investment: float,
    leverage: float,
    account_type: str,
    excel_data: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, float], List[Dict]]:
    """
    Fresh Capital Restart backtest with daily tracking for complete analysis.
    When margin call occurs: liquidate position, deploy fresh capital immediately.
    Returns same format as liquidation-reentry for consistent display.
    """
    
    # Get margin parameters
    margin_params = calculate_margin_params(account_type, leverage)
    
    # Prepare data with date range
    data = excel_data.loc[start_date:end_date].copy()
    if etf == 'SPY':
        price_col, dividend_col = 'SPY', 'SPY_Dividends'
    else:
        price_col, dividend_col = 'VTI', 'VTI_Dividends'
    
    data = data.dropna(subset=[price_col, 'FedFunds (%)'])
    
    if len(data) < 10:
        st.error("Insufficient data for the selected date range")
        return pd.DataFrame(), {}, []
    
    # Investment parameters - FRESH CAPITAL each round
    cash_per_round = initial_investment / leverage
    
    # Comprehensive daily tracking
    daily_results = []
    liquidation_events = []
    round_analysis = []
    
    # State variables
    current_round = 1
    current_position_start_date = None
    current_position_start_price = None
    shares_held = 0.0
    margin_loan = 0.0
    in_position = False
    days_in_current_position = 0
    wait_days_remaining = 0
    
    # Performance tracking
    total_liquidations = 0
    total_interest_paid = 0.0
    total_dividends_received = 0.0
    total_capital_deployed = 0.0
    
    # Main simulation loop - DAILY tracking with fresh capital restarts
    for i, (date, row) in enumerate(data.iterrows()):
        current_price = row[price_col]
        dividend_payment = row[dividend_col] if pd.notna(row[dividend_col]) else 0.0
        fed_funds_rate = row['FedFunds (%)'] / 100.0
        
        # Use IBKR rates directly from Excel data
        margin_rate = row['FedFunds + 1.5%'] / 100.0
        daily_interest_rate = margin_rate / 365
        
        # On Day 1 (i==0), we just enter positions at close - no interest/dividends yet
        # Starting Day 2 (i>=1), we calculate interest, dividends, and other changes
        
        # Initialize daily result
        daily_result = {
            'Date': date,
            'ETF_Price': current_price,
            'Current_Equity': cash_per_round,  # Always fresh capital available
            'In_Position': in_position,
            'Wait_Days_Remaining': wait_days_remaining,
            'Cycle_Number': current_round,
            'Days_In_Position': days_in_current_position,
            'Fed_Funds_Rate': fed_funds_rate * 100,
            'Margin_Rate': margin_rate * 100
        }
        
        # Handle waiting period after liquidation
        if wait_days_remaining > 0:
            wait_days_remaining -= 1
            daily_result.update({
                'Shares_Held': 0,
                'Portfolio_Value': 0,
                'Margin_Loan': 0,
                'Equity': cash_per_round,
                'Maintenance_Margin_Required': 0,
                'Is_Margin_Call': False,
                'Daily_Interest_Cost': 0,
                'Cumulative_Interest_Cost': total_interest_paid,
                'Dividend_Payment': 0,
                'Cumulative_Dividends': total_dividends_received,
                'Position_Status': 'Waiting_After_Liquidation_Fresh_Capital'
            })
            daily_results.append(daily_result)
            continue
        
        # Start new position if not in one (fresh capital deployment)
        if not in_position:
            # Deploy fresh capital
            position_value = cash_per_round * leverage
            shares_held = position_value / current_price
            margin_loan = position_value - cash_per_round
            in_position = True
            days_in_current_position = 0
            total_capital_deployed += cash_per_round
            
            # Record position start info
            current_position_start_date = date
            current_position_start_price = current_price
            
            daily_result['Position_Status'] = 'Fresh_Capital_Deployed'
        
        # Update position if active
        if in_position:
            days_in_current_position += 1
            
            # Calculate daily interest cost - ONLY after Day 1
            daily_interest_cost = 0
            if i > 0:
                daily_interest_cost = margin_loan * daily_interest_rate
                margin_loan += daily_interest_cost
                total_interest_paid += daily_interest_cost
            
            # Handle dividend payments - ONLY after Day 1
            dividend_received = 0
            if i > 0 and dividend_payment > 0:
                dividend_received = shares_held * dividend_payment
                total_dividends_received += dividend_received
                # Reinvest dividends
                additional_shares = dividend_received / current_price
                shares_held += additional_shares
            
            # Calculate current position values
            portfolio_value = shares_held * current_price
            current_equity_in_position = portfolio_value - margin_loan
            maintenance_margin_required = portfolio_value * (margin_params['maintenance_margin_pct'] / 100.0)
            
            # Check for margin call
            is_margin_call = current_equity_in_position < maintenance_margin_required
            
            if is_margin_call:
                # LIQUIDATION EVENT - but fresh capital available immediately
                liquidation_value = max(0, current_equity_in_position)
                loss_amount = cash_per_round - liquidation_value
                
                # Record liquidation event
                liquidation_events.append({
                    'date': date,
                    'cycle_number': current_round,
                    'days_in_position': days_in_current_position,
                    'entry_equity': cash_per_round,
                    'liquidation_equity': liquidation_value,
                    'loss_amount': loss_amount,
                    'loss_percentage': (loss_amount / cash_per_round) * 100,
                    'price_at_entry': current_position_start_price,
                    'price_at_liquidation': current_price,
                    'interest_paid_this_cycle': daily_interest_cost * days_in_current_position
                })
                
                # Record complete round analysis
                price_change_pct = ((current_price - current_position_start_price) / current_position_start_price) * 100
                
                round_analysis.append({
                    'Round': current_round,
                    'Days': days_in_current_position,
                    'Start_Date': current_position_start_date,
                    'End_Date': date,
                    'Start_Price': current_position_start_price,
                    'End_Price': current_price,
                    'Price_Change_Pct': price_change_pct,
                    'Start_Portfolio_Value': cash_per_round * leverage,
                    'End_Portfolio_Value': portfolio_value,
                    'Start_Equity': cash_per_round,
                    'End_Equity': liquidation_value,
                    'Capital_Deployed': cash_per_round,
                    'Final_Value': liquidation_value,
                    'Margin_Call': True,
                    'Loss_Pct': (loss_amount / cash_per_round) * 100,
                    'Profit_Pct': 0.0,
                    'Interest_Paid': daily_interest_cost * days_in_current_position
                })
                
                # Reset for next round with FRESH CAPITAL after 2-day wait
                total_liquidations += 1
                current_round += 1
                in_position = False
                shares_held = 0
                margin_loan = 0
                days_in_current_position = 0
                wait_days_remaining = 2  # 2-day waiting period
                
                daily_result['Position_Status'] = 'Liquidated_Fresh_Capital_Wait'
            else:
                daily_result['Position_Status'] = 'Active'
            
            # Update daily result with position data
            equity_to_show = current_equity_in_position if in_position else cash_per_round
            daily_result.update({
                'Shares_Held': shares_held,
                'Portfolio_Value': portfolio_value if in_position else 0,
                'Margin_Loan': margin_loan if in_position else 0,
                'Equity': equity_to_show,
                'Maintenance_Margin_Required': maintenance_margin_required if in_position else 0,
                'Is_Margin_Call': is_margin_call,
                'Daily_Interest_Cost': daily_interest_cost if in_position else 0,
                'Cumulative_Interest_Cost': total_interest_paid,
                'Dividend_Payment': dividend_received,
                'Cumulative_Dividends': total_dividends_received,
                'Margin_Call_Price': margin_loan / (shares_held * (1 - margin_params['maintenance_margin_pct'] / 100.0)) if shares_held > 0 else 0
            })
        
        daily_results.append(daily_result)
    
    # Handle final round if position still active
    if in_position and current_position_start_date is not None:
        price_change_pct = ((current_price - current_position_start_price) / current_position_start_price) * 100
        final_portfolio_value = portfolio_value
        final_equity = current_equity_in_position
        profit_amount = final_equity - cash_per_round
        
        round_analysis.append({
            'Round': current_round,
            'Days': days_in_current_position,
            'Start_Date': current_position_start_date,
            'End_Date': date,
            'Start_Price': current_position_start_price,
            'End_Price': current_price,
            'Price_Change_Pct': price_change_pct,
            'Start_Portfolio_Value': cash_per_round * leverage,
            'End_Portfolio_Value': final_portfolio_value,
            'Start_Equity': cash_per_round,
            'End_Equity': final_equity,
            'Capital_Deployed': cash_per_round,
            'Final_Value': final_equity,
            'Margin_Call': False,
            'Loss_Pct': 0.0,
            'Profit_Pct': (profit_amount / cash_per_round) * 100,
            'Interest_Paid': daily_interest_cost * days_in_current_position if 'daily_interest_cost' in locals() else 0
        })
    
    # Convert to DataFrame
    df_results = pd.DataFrame(daily_results)
    df_results.set_index('Date', inplace=True)
    
    if df_results.empty:
        return df_results, {}, []
    
    # Calculate comprehensive performance metrics for fresh capital analysis
    total_rounds = len(round_analysis)
    successful_rounds = len([r for r in round_analysis if not r['Margin_Call']])
    total_losses = sum([r.get('Loss_Pct', 0) * r['Capital_Deployed'] / 100 for r in round_analysis if r['Margin_Call']])
    total_profits = sum([r.get('Profit_Pct', 0) * r['Capital_Deployed'] / 100 for r in round_analysis if not r['Margin_Call']])
    net_result = total_profits - total_losses
    
    # Time-based metrics
    total_days = len(df_results)
    years = total_days / 252
    
    # Fresh capital metrics (different from liquidation-reentry)
    avg_survival_days = np.mean([r['Days'] for r in round_analysis]) if round_analysis else 0
    liquidation_rate = (total_liquidations / total_rounds * 100) if total_rounds > 0 else 0
    
    # Risk metrics based on daily equity fluctuations
    equity_series = df_results['Equity']
    daily_returns = equity_series.pct_change().dropna()
    
    if len(daily_returns) > 1:
        annual_volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # Calculate overall return for fresh capital strategy
        total_return_pct = (net_result / total_capital_deployed * 100) if total_capital_deployed > 0 else 0
        cagr = ((1 + total_return_pct/100) ** (1/years) - 1) * 100 if years > 0 else 0
        sharpe_ratio = cagr / annual_volatility if annual_volatility > 0 else 0
        
        # Drawdown analysis
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Downside metrics
        negative_returns = daily_returns[daily_returns < 0]
        downside_volatility = negative_returns.std() * np.sqrt(252) * 100 if len(negative_returns) > 0 else 0
        sortino_ratio = cagr / downside_volatility if downside_volatility > 0 else 0
        
        # Drawdown duration
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
        total_return_pct = 0
        cagr = 0
    
    # Position analytics
    active_position_days = len(df_results[df_results['In_Position'] == True])
    waiting_days = len(df_results[df_results['Wait_Days_Remaining'] > 0])
    time_in_market_pct = (active_position_days / total_days) * 100 if total_days > 0 else 0
    
    # Fresh capital metrics
    metrics = {
        # Core Performance - Fresh Capital Strategy
        'Equity ($)': cash_per_round,
        'Final Equity ($)': equity_series.iloc[-1] if len(equity_series) > 0 else cash_per_round,
        'Total Return (%)': total_return_pct,
        'CAGR (%)': cagr,
        'Max Equity Achieved ($)': equity_series.max() if len(equity_series) > 0 else cash_per_round,
        
        # Risk Metrics
        'Max Drawdown (%)': max_drawdown,
        'Annual Volatility (%)': annual_volatility,
        'Downside Volatility (%)': downside_volatility,
        'Sharpe Ratio': sharpe_ratio,
        'Sortino Ratio': sortino_ratio,
        
        # Drawdown Analysis  
        'Max Drawdown Duration (days)': max_drawdown_duration,
        'Avg Drawdown Duration (days)': avg_drawdown_duration,
        
        # Trading Statistics - Fresh Capital Focus
        'Total Liquidations': total_liquidations,
        'Total Cycles': total_rounds,
        'Time in Market (%)': time_in_market_pct,
        'Active Position Days': active_position_days,
        'Waiting Days': waiting_days,
        
        # Fresh Capital Analytics
        'Avg Days Between Liquidations': avg_survival_days,
        'Avg Loss Per Liquidation (%)': np.mean([r.get('Loss_Pct', 0) for r in round_analysis if r['Margin_Call']]) if any(r['Margin_Call'] for r in round_analysis) else 0,
        'Worst Single Loss (%)': max([r.get('Loss_Pct', 0) for r in round_analysis if r['Margin_Call']], default=0),
        
        # Cost Analysis
        'Total Interest Paid ($)': total_interest_paid,
        'Total Dividends Received ($)': total_dividends_received,
        'Net Interest Cost ($)': total_interest_paid - total_dividends_received,
        
        # Strategy Parameters
        'Leverage Used': leverage,
        'Account Type': account_type,
        'Backtest Days': total_days,
        'Backtest Years': years,
        
        # Fresh Capital Specific
        'Total Capital Deployed ($)': total_capital_deployed,
        'Liquidation Rate (%)': liquidation_rate,
        'Fresh Capital Per Round ($)': cash_per_round
    }
    
    return df_results, metrics, round_analysis

# Cushion analytics moved to cushion_analysis.py module

def create_enhanced_portfolio_chart(df_results: pd.DataFrame, metrics: Dict[str, float], rebalancing_events: List[Dict] = None) -> go.Figure:
    """Create sophisticated institutional-grade portfolio performance chart"""
    
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=(
            'Portfolio Value, Equity & Margin Components', 'Cumulative P&L Attribution: Dividends and Loan Interests',
            'Drawdown Analysis & Recovery', 'Rolling Performance Metrics', 
            'Daily Returns Distribution', 'Interest Rate Environment',
            'Position Status Timeline', 'Risk-Adjusted Performance'
        ),
        specs=[
            [{"colspan": 2}, None],
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "histogram"}],
            [{"type": "scatter"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08,
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )
    
    # Enhanced main chart with all portfolio components
    
    # Portfolio Value line
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Portfolio_Value'],
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=3),
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Portfolio Value: $%{y:,.0f}<br><extra></extra>'
        ),
        row=1, col=1
    )
    
    # Equity line
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Equity'],
            name='Equity',
            line=dict(color='#2E86C1', width=3),
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Equity: $%{y:,.0f}<br><extra></extra>'
        ),
        row=1, col=1
    )
    
    # Maintenance Margin Required line
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Maintenance_Margin_Required'],
            name='Maintenance Margin Required',
            line=dict(color='#d62728', width=2, dash='dash'),
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Maintenance Margin Required: $%{y:,.0f}<br><extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add profit threshold rebalancing markers (diamond-shaped gold markers)
    if rebalancing_events:
        rebalance_dates = [pd.to_datetime(event['date']) for event in rebalancing_events]
        rebalance_portfolio_values = []
        
        # Get portfolio values at rebalancing dates
        for date in rebalance_dates:
            # Find the closest date in df_results
            closest_date = df_results.index[df_results.index.get_indexer([date], method='nearest')[0]]
            rebalance_portfolio_values.append(df_results.loc[closest_date, 'Portfolio_Value'])
        
        # Create growth percentage labels for hover
        growth_labels = [f"{event['growth_trigger_pct']:.1f}%" for event in rebalancing_events]
        shares_added = [f"{event['shares_change']:+,.0f}" for event in rebalancing_events]
        transaction_costs = [f"${event['transaction_cost']:,.0f}" for event in rebalancing_events]
        
        fig.add_trace(
            go.Scatter(
                x=rebalance_dates,
                y=rebalance_portfolio_values,
                mode='markers',
                name='💎 Profit Threshold Rebalancing',
                marker=dict(
                    symbol='diamond',
                    size=14,
                    color='#FFD700',  # Gold color
                    line=dict(color='#FF8C00', width=2),  # Orange border
                    opacity=0.9
                ),
                customdata=list(zip(growth_labels, shares_added, transaction_costs)),
                hovertemplate=(
                    '<b>💎 PROFIT THRESHOLD REBALANCING</b><br>' +
                    'Date: %{x|%d-%b-%Y}<br>' +
                    'Portfolio Value: $%{y:,.0f}<br>' +
                    'Growth Achieved: %{customdata[0]}<br>' +
                    'Shares Added: %{customdata[1]}<br>' +
                    'Transaction Cost: %{customdata[2]}<br>' +
                    '<extra></extra>'
                )
            ),
            row=1, col=1
        )

    
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
                hovertemplate='LIQUIDATION<br>Date: %{x|%d-%b-%Y}<br>Remaining Equity: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Add position entries as green markers
    entries = df_results[df_results['Position_Status'] == 'Entered']
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
                hovertemplate='NEW POSITION<br>Date: %{x|%d-%b-%Y}<br>Entry Equity: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Cumulative P&L Attribution: Dividends and Loan Interests (moved from row 4, col 2)
    cumulative_interest = df_results['Daily_Interest_Cost'].cumsum()
    cumulative_dividends = df_results['Dividend_Payment'].cumsum()
    
    # Calculate dynamic range for better fill visualization
    min_interest = -cumulative_interest.max() if len(cumulative_interest) > 0 else 0
    max_dividends = cumulative_dividends.max() if len(cumulative_dividends) > 0 else 0
    
    # Add Interest Cost trace with red shaded area below the line
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=-cumulative_interest,  # Negative because it's a cost
            name='Cumulative Interest Cost',
            line=dict(color='#E74C3C', width=3),
            fill='tozeroy',  # Fill from line to zero (and beyond to bottom)
            fillcolor='rgba(231, 76, 60, 0.25)',  # Semi-transparent red
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Interest Cost: -$%{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add Dividends trace with green shaded area above the line  
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=cumulative_dividends,
            name='Cumulative Dividends',
            line=dict(color='#28B463', width=3),
            fill='tonexty',  # Fill from this line to the previous trace (creating layered effect)
            fillcolor='rgba(40, 180, 99, 0.25)',  # Semi-transparent green
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Dividends: +$%{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add subtle zero baseline for better visual reference
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="rgba(108, 117, 125, 0.6)", 
        line_width=1,
        row=2, col=1,
        annotation_text="Break-even Line",
        annotation_position="top right",
        annotation=dict(
            font=dict(size=10, color="rgba(108, 117, 125, 0.8)"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(108, 117, 125, 0.3)",
            borderwidth=1
        )
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
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Drawdown: %{y:.1f}%<extra></extra>'
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
                hovertemplate='Date: %{x|%d-%b-%Y}<br>Rolling Sharpe: %{y:.2f}<extra></extra>'
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
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Fed Funds: %{y:.2f}%<extra></extra>'
        ),
        row=4, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Margin_Rate'],
            name='Margin Rate',
            line=dict(color='#DC3545', width=2, dash='dash'),
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Margin Rate: %{y:.2f}%<extra></extra>'
        ),
        row=4, col=1
    )
    
    # Position Status Timeline (moved from row 2, col 1)
    position_colors = {
        'Active': '#28B463',
        'Waiting': '#F39C12', 
        'Liquidated': '#E74C3C',
        'Entered': '#3498DB',
        'Insufficient_Equity': '#95A5A6'
    }
    
    for status, color in position_colors.items():
        status_data = df_results[df_results['Position_Status'] == status]
        if not status_data.empty:
            display_name = status.replace('_', ' ')
            hover_template = display_name + '<br>Date: %{x|%d-%b-%Y}<extra></extra>'
            
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
                row=4, col=2
            )
    
    # Update layout
    # Handle different leverage key names across backtest modes
    leverage_value = metrics.get('Leverage Used', metrics.get('Target Leverage', 0))
    
    # Add rebalancing count to title if available
    rebalance_info = ""
    if rebalancing_events:
        rebalance_info = f" | {len(rebalancing_events)} Rebalancing Events"
    
    fig.update_layout(
        title={
            'text': f"Comprehensive Portfolio Analysis: {leverage_value:.1f}x Leverage | {metrics.get('Total Liquidations', 0)} Liquidations | {metrics.get('CAGR (%)', 0):.1f}% CAGR{rebalance_info}",
            'x': 0.4,
            'font': {'size': 16, 'color': '#2C3E50'}
        },
        height=1200,
        showlegend=True,
        legend=dict(x=1.02, y=1, bgcolor='rgba(255,255,255,0.8)'),
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    # Update axes styling with yearly grid lines
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='#E8E8E8',
        dtick='M12',  # One year intervals for vertical grid lines
        tickformat='%Y'  # Show only year labels
    )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
    
    # Format specific axes
    fig.update_yaxes(tickformat='$,.0f', row=1, col=1, title_text="Portfolio Components ($)")
    fig.update_yaxes(tickformat='$,.0f', row=2, col=1, title_text="Cumulative ($)")
    fig.update_yaxes(tickformat='.1f', row=2, col=2, title_text="Drawdown (%)")
    fig.update_yaxes(tickformat='.2f', row=3, col=1, title_text="Rolling Sharpe")
    fig.update_yaxes(tickformat='.2f', row=4, col=1, title_text="Interest Rate (%)")
    fig.update_yaxes(tickformat='.0f', row=4, col=2, title_text="Position Status")
    
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
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Equity: $%{y:,.0f}<extra></extra>'
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
                    hovertemplate='Date: %{x|%d-%b-%Y}<br>Trend: $%{y:,.0f}<extra></extra>'
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
                    hovertemplate='Date: %{x|%d-%b-%Y}<br>Correlation: %{y:.3f}<extra></extra>'
                ),
                row=2, col=1
            )
    
    # 5. Performance attribution (Interest vs Dividends vs Price)
    cumulative_interest = df_results['Daily_Interest_Cost'].cumsum()
    cumulative_dividends = df_results['Dividend_Payment'].cumsum()
    
    # Add Interest Cost with red shaded area
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=-cumulative_interest,
            name='Interest Cost',
            line=dict(color='#E74C3C', width=2),
            fill='tozeroy',  # Fill from line to zero
            fillcolor='rgba(231, 76, 60, 0.25)',  # Semi-transparent red
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Interest: -$%{y:,.0f}<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Add Dividend Income with green shaded area  
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=cumulative_dividends,
            name='Dividend Income',
            line=dict(color='#27AE60', width=2),
            fill='tonexty',  # Fill from this line to previous trace
            fillcolor='rgba(39, 174, 96, 0.25)',  # Semi-transparent green
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Dividends: +$%{y:,.0f}<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Add zero baseline for this chart too
    fig.add_hline(
        y=0, 
        line_dash="dot", 
        line_color="rgba(108, 117, 125, 0.4)", 
        line_width=1,
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
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Equity: $%{y:,.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Maintenance_Margin_Required'],
            name='Maintenance Margin Required',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Required: $%{y:,.2f}<extra></extra>'
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
                hovertemplate='Margin Call<br>Date: %{x|%d-%b-%Y}<br>Equity: $%{y:,.2f}<extra></extra>'
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
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Fed Funds: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=df_results['Margin_Rate'],
            name='Margin Interest Rate',
            line=dict(color='purple', width=2),
            hovertemplate='Date: %{x|%d-%b-%Y}<br>Margin Rate: %{y:.2f}%<extra></extra>'
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



def create_restart_summary_chart(rounds_df: pd.DataFrame, summary: Dict, etf_choice: str = "ETF", leverage: float = 1.0) -> go.Figure:
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
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Professional header
    st.markdown("""
    <div class="terminal-header">
        <h1 style="color: var(--accent-orange); margin: 0; font-size: 1.8rem; text-transform: uppercase;">HISTORICAL BACKTEST ENGINE</h1>
        <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0; font-size: 0.9rem; text-transform: uppercase;">
            LEVERAGE SIMULATION WITH MARGIN REQUIREMENTS AND INTEREST CALCULATIONS
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    excel_data, _, _, _, _ = load_comprehensive_data()
    
    if excel_data is None:
        st.error("DATA LOAD FAILURE: ETFs and Fed Funds Data.xlsx not found or corrupted")
        return
    

    
    # Backtest mode selection
    st.markdown("<h2>BACKTEST MODE SELECTION</h2>", unsafe_allow_html=True)
    
    # Add custom CSS for these specific buttons and tooltips
    st.markdown("""
    <style>
    /* Backtest mode selection buttons */
    div[data-testid="column"] button {
        background-color: #1a1a1a !important;
        color: #ff8c00 !important;
        border: 2px solid #ff8c00 !important;
        font-weight: 600 !important;
    }
    
    /* Force text to be visible - target the span inside button */
    div[data-testid="column"] button span {
        color: #ff8c00 !important;
    }
    
    div[data-testid="column"] button:hover {
        background-color: #ff8c00 !important;
        color: #ffffff !important;
        border-color: #ffa500 !important;
    }
    
    div[data-testid="column"] button:hover span {
        color: #ffffff !important;
    }
    
    /* Force all tooltips to be visible */
    [role="tooltip"] {
        background-color: #ff8c00 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        padding: 8px 12px !important;
        border: 2px solid #ffa500 !important;
    }
    
    [role="tooltip"] * {
        color: #000000 !important;
    }
    
    /* Tooltip arrows */
    [role="tooltip"]::before,
    [role="tooltip"]::after {
        border-color: #ff8c00 transparent !important;
    }
    
    /* Parameter inputs - white background with black text */
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
    
    /* Ensure dropdown options are also readable */
    .stSelectbox option {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Number input buttons */
    .stNumberInput button {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
    
    .stNumberInput button:hover {
        background-color: #e0e0e0 !important;
    }
    
    /* Labels should remain in the terminal theme color */
    .stSelectbox label,
    .stDateInput label,
    .stNumberInput label,
    .stTextInput label {
        color: #ff8c00 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Additional CSS specifically for these three buttons
    st.markdown("""
    <style>
    /* Target buttons by their specific keys */
    button[kind="primary"][key="liquidation_backtest_btn"],
    button[kind="primary"][key="restart_backtest_btn"],
    button[kind="primary"][key="profit_threshold_btn"],
    div[data-testid="column"]:nth-child(1) button,
    div[data-testid="column"]:nth-child(2) button,
    div[data-testid="column"]:nth-child(3) button {
        color: #ff8c00 !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
    }
    
    /* FRESH CAPITAL RESTART button - WHITE TEXT */
    div[data-testid="column"]:nth-child(2) button {
        color: #ffffff !important;
        border-color: #ffffff !important;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Button text spans - orange for 1st and 3rd, white for 2nd */
    div[data-testid="column"]:nth-child(1) button span,
    div[data-testid="column"]:nth-child(3) button span,
    div[data-testid="column"] button p {
        color: #ff8c00 !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* FRESH CAPITAL RESTART button span - WHITE TEXT */
    div[data-testid="column"]:nth-child(2) button span {
        color: #ffffff !important;
        display: block !important;
        visibility: visible !important;
        font-weight: 700 !important;
    }
    
    /* On hover effects */
    div[data-testid="column"]:nth-child(1) button:hover span,
    div[data-testid="column"]:nth-child(3) button:hover span {
        color: #000000 !important;
    }
    
    div[data-testid="column"]:nth-child(1) button:hover,
    div[data-testid="column"]:nth-child(3) button:hover {
        background-color: #ff8c00 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.4) !important;
    }
    
    /* FRESH CAPITAL RESTART hover - white background, black text */
    div[data-testid="column"]:nth-child(2) button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.4) !important;
    }
    
    div[data-testid="column"]:nth-child(2) button:hover span {
        color: #000000 !important;
    }
    
    /* Calendar / Date Picker Styling - Make text readable across all modes */
    .stDateInput div[data-baseweb="calendar"] {
        background-color: #ffffff !important;
    }
    
    /* Calendar header, navigation, and all text elements */
    .stDateInput div[data-baseweb="calendar"] button,
    .stDateInput div[data-baseweb="calendar"] span,
    .stDateInput div[data-baseweb="calendar"] div {
        color: #000000 !important;
        font-weight: normal !important;
    }
    
    /* Calendar days */
    .stDateInput div[data-baseweb="calendar"] td,
    .stDateInput div[data-baseweb="calendar"] th {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: normal !important;
    }
    
    /* Calendar navigation buttons */
    .stDateInput div[data-baseweb="calendar"] button:hover {
        background-color: #f0f0f0 !important;
        color: #000000 !important;
    }
    
    /* Selected date */
    .stDateInput div[data-baseweb="calendar"] [aria-selected="true"] {
        background-color: #ff8c00 !important;
        color: #ffffff !important;
    }
    
    /* Today's date */
    .stDateInput div[data-baseweb="calendar"] [aria-label*="Today"] {
        background-color: #e8f4fd !important;
        color: #000000 !important;
    }
    
    /* Calendar month/year dropdowns */
    .stDateInput div[data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    
    .stDateInput div[data-baseweb="select"] div,
    .stDateInput div[data-baseweb="select"] span {
        color: #000000 !important;
        font-weight: normal !important;
    }
    
    /* Comprehensive calendar fix - target all possible calendar elements */
    div[data-baseweb="calendar"] *,
    div[data-baseweb="datepicker"] *,
    .react-datepicker *,
    [class*="calendar"] *,
    [class*="datepicker"] * {
        color: #000000 !important;
        font-weight: normal !important;
    }
    
    /* Calendar container background */
    div[data-baseweb="calendar"],
    div[data-baseweb="datepicker"],
    .react-datepicker {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Calendar popup/overlay positioning */
    div[data-baseweb="calendar"][data-floating-ui-portal] {
        z-index: 999999 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add selected state styling based on current backtest mode
    selected_css = ""
    current_mode = st.session_state.get('backtest_mode', 'standard')
    
    if current_mode == 'standard':
        selected_css = """
        <style>
        /* Highlight LIQUIDATION-REENTRY button */
        div[data-testid="column"]:nth-child(1) button {
            background-color: #ff8c00 !important;
            color: #000000 !important;
            border-color: #ffa500 !important;
            box-shadow: 0 0 15px rgba(255, 140, 0, 0.6) !important;
        }
        div[data-testid="column"]:nth-child(1) button span {
            color: #000000 !important;
            font-weight: 700 !important;
        }
        </style>
        """
    elif current_mode == 'restart':
        selected_css = """
        <style>
        /* Highlight FRESH CAPITAL RESTART button with orange */
        div[data-testid="column"]:nth-child(2) button {
            background-color: #ff8c00 !important;
            color: #000000 !important;
            border-color: #ffa500 !important;
            box-shadow: 0 0 15px rgba(255, 140, 0, 0.6) !important;
        }
        div[data-testid="column"]:nth-child(2) button span {
            color: #000000 !important;
            font-weight: 700 !important;
        }
        </style>
        """
    elif current_mode == 'profit_threshold':
        selected_css = """
        <style>
        /* Highlight PROFIT THRESHOLD button */
        div[data-testid="column"]:nth-child(3) button {
            background-color: #ff8c00 !important;
            color: #000000 !important;
            border-color: #ffa500 !important;
            box-shadow: 0 0 15px rgba(255, 140, 0, 0.6) !important;
        }
        div[data-testid="column"]:nth-child(3) button span {
            color: #000000 !important;
            font-weight: 700 !important;
        }
        </style>
        """
    
    st.markdown(selected_css, unsafe_allow_html=True)
    
    backtest_col1, backtest_col2, backtest_col3 = st.columns(3)
    
    # Create buttons with custom HTML/CSS based on selected mode
    current_mode = st.session_state.get('backtest_mode', 'standard')
    
    with backtest_col1:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 0.5rem;">
            <span style="color: #ffffff; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">LIQUIDATION-REENTRY</span>
        </div>
        """, unsafe_allow_html=True)
        if current_mode == 'standard':
            st.markdown("""
            <div style="background-color: #ff8c00; padding: 0.5rem 1rem; text-align: center; 
                        border-radius: 0.25rem; color: #000000; font-weight: 700; 
                        text-transform: uppercase; letter-spacing: 1px; cursor: default;
                        box-shadow: 0 0 15px rgba(255, 140, 0, 0.6);">
                LIQUIDATION-REENTRY
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(
                "LIQUIDATION-REENTRY",
                use_container_width=True,
                help="Realistic simulation: liquidate on margin call, wait 2 days, re-enter with remaining equity",
                key="liquidation_backtest_btn"
            ):
                st.session_state.backtest_mode = 'standard'
                st.rerun()
    
    with backtest_col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 0.5rem;">
            <span style="color: #ffffff; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">FRESH CAPITAL RESTART</span>
        </div>
        """, unsafe_allow_html=True)
        if current_mode == 'restart':
            st.markdown("""
            <div style="background-color: #ff8c00; padding: 0.5rem 1rem; text-align: center; 
                        border-radius: 0.25rem; color: #000000; font-weight: 700; 
                        text-transform: uppercase; letter-spacing: 1px; cursor: default;
                        box-shadow: 0 0 15px rgba(255, 140, 0, 0.6);">
                FRESH CAPITAL RESTART
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(
                "FRESH CAPITAL RESTART",
                use_container_width=True,
                help="Comparison mode: unlimited fresh capital after each margin call",
                key="restart_backtest_btn"
            ):
                st.session_state.backtest_mode = 'restart'
                st.rerun()
    
    with backtest_col3:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 0.5rem;">
            <span style="color: #ffffff; font-size: 0.8rem; font-weight: bold; text-transform: uppercase;">PROFIT THRESHOLD</span>
        </div>
        """, unsafe_allow_html=True)
        if current_mode == 'profit_threshold':
            st.markdown("""
            <div style="background-color: #ff8c00; padding: 0.5rem 1rem; text-align: center; 
                        border-radius: 0.25rem; color: #000000; font-weight: 700; 
                        text-transform: uppercase; letter-spacing: 1px; cursor: default;
                        box-shadow: 0 0 15px rgba(255, 140, 0, 0.6);">
                PROFIT THRESHOLD
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(
                "PROFIT THRESHOLD", 
                use_container_width=True,
                help="Rebalance back to target leverage when portfolio grows by specified percentage",
                key="profit_threshold_btn"
            ):
                st.session_state.backtest_mode = 'profit_threshold'
                st.rerun()
    
    # Initialize if not set
    if 'backtest_mode' not in st.session_state:
        st.session_state.backtest_mode = 'standard'
    
    # Display selected mode with custom styling
    if st.session_state.backtest_mode == 'standard':
        st.markdown("""
        <div style="background-color: #1a1a1a; border: 1px solid #ff8c00; padding: 1rem; color: #e0e0e0;">
            <strong style="color: #ff8c00;">LIQUIDATION-REENTRY MODE:</strong> Realistic simulation with margin call liquidation and 2-day re-entry delay
        </div>
        """, unsafe_allow_html=True)
        mode_description = """
    <div class="terminal-card">
            <h3 style="color: var(--accent-orange);">LIQUIDATION-REENTRY STRATEGY</h3>
            <div style="color: var(--text-secondary); margin-top: 1rem;">
                <strong>STRATEGY COMPONENTS:</strong><br/>
                • FORCED LIQUIDATION: Immediate position closure on margin call<br/>
                • 2-DAY WAIT PERIOD: Cooling-off period after liquidation<br/>
                • AUTOMATIC RE-ENTRY: Deploy remaining equity at same leverage<br/>
                • CAPITAL TRACKING: Monitor equity depletion over cycles<br/>
                • RISK ANALYTICS: Institutional-grade performance metrics
            </div>
    </div>
        """
    elif st.session_state.backtest_mode == 'profit_threshold':
        st.markdown("""
        <div style="background-color: #1a1a1a; border: 1px solid #00ff00; padding: 1rem; color: #e0e0e0;">
            <strong style="color: #00ff00;">PROFIT THRESHOLD MODE:</strong> Rebalance to target leverage at growth milestones
        </div>
        """, unsafe_allow_html=True)
        mode_description = """
        <div class="terminal-card">
            <h3 style="color: var(--accent-orange);">PROFIT THRESHOLD REBALANCING</h3>
            <div style="color: var(--text-secondary); margin-top: 1rem;">
                <strong>STRATEGY COMPONENTS:</strong><br/>
                • GROWTH MONITORING: Track portfolio growth from initial position<br/>
                • CONFIGURABLE THRESHOLD: User-defined growth target (default: 100%)<br/>
                • LEVERAGE RESTORATION: Rebalance to target when threshold reached<br/>
                • BORROW-ONLY STRATEGY: Add leverage without selling shares<br/>
                • COMPOUND GROWTH: Scale position size with accumulated profits<br/>
                • ANALYTICS TRACKING: Monitor all rebalancing events<br/>
                • CONSISTENT EXPOSURE: Maintain target leverage as wealth grows
            </div>
            <div class="terminal-card" style="border-color: var(--info-blue); margin-top: 1rem;">
                <strong>EXAMPLE:</strong> $1M @ 2X → $4M (100% growth) → LEVERAGE: 1.33X → REBALANCE: BORROW $2M → $6M @ 2X
            </div>
        </div>
        """
    else:  # restart mode
        st.markdown("""
        <div style="background-color: #1a1a1a; border: 1px solid #00ff00; padding: 1rem; color: #e0e0e0;">
            <strong style="color: #00ff00;">FRESH CAPITAL MODE:</strong> Unlimited capital simulation for comparison analysis
        </div>
        """, unsafe_allow_html=True)
        mode_description = """
        <div class="terminal-card">
            <h3 style="color: var(--accent-orange);">FRESH CAPITAL RESTART</h3>
            <div style="color: var(--text-secondary); margin-top: 1rem;">
                <strong>STRATEGY COMPONENTS:</strong><br/>
                • UNLIMITED CAPITAL: Deploy fresh funds after each margin call<br/>
                • 2-DAY WAIT PERIOD: Same cooling-off as liquidation-reentry<br/>
                • FREQUENCY ANALYSIS: Track margin call occurrence patterns<br/>
                • SURVIVAL METRICS: Monitor position duration statistics<br/>
                • COMPARISON TOOL: Benchmark against realistic strategies
            </div>
        </div>
        """
    
    st.markdown(mode_description, unsafe_allow_html=True)
    
    # Input parameters
    st.markdown("<h2>BACKTEST PARAMETERS</h2>", unsafe_allow_html=True)
    
    # Get available date range for validation
    min_date = excel_data.index.min().date()
    max_date = excel_data.index.max().date()
    
    input_col1, input_col2, input_col3 = st.columns([1, 1, 1.2])
    
    with input_col1:
        etf_choice = st.selectbox(
            "Select ETF",
            ["SPY", "VTI"],
            help="Choose the ETF to backtest",
            key="backtest_etf_choice"
        )
        
        start_date = st.date_input(
            "Start Date",
            value=datetime.date(2010, 1, 1),
            min_value=min_date,
            max_value=max_date,
            help="When to start the backtest",
            key="backtest_start_date"
        )
        
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            help="When to end the backtest",
            key="backtest_end_date"
        )
        
        # Equity for Profit Threshold mode ONLY - stays in column 1 below End Date
        if st.session_state.backtest_mode == 'profit_threshold':
            # Custom formatted equity input with commas
            equity_default = "50,000,000"
            if f"equity_formatted_{st.session_state.backtest_mode}" not in st.session_state:
                st.session_state[f"equity_formatted_{st.session_state.backtest_mode}"] = equity_default
            
            equity_input = st.text_input(
                "Equity ($)",
                value=st.session_state[f"equity_formatted_{st.session_state.backtest_mode}"],
                help="Your cash equity (not including leverage). Format: 50,000,000",
                key=f"equity_text_{st.session_state.backtest_mode}",
                placeholder="50,000,000"
            )
            
            # Parse and validate the formatted input
            try:
                # Remove commas and convert to number
                equity_clean = equity_input.replace(",", "").replace("$", "").replace(" ", "")
                equity = float(equity_clean)
                
                # Validate minimum value
                if equity < 5000:
                    st.error("Minimum equity is $5,000")
                    equity = 5000
                
                # Update session state with properly formatted value
                formatted_value = f"{equity:,.0f}"
                if formatted_value != equity_input:
                    st.session_state[f"equity_formatted_{st.session_state.backtest_mode}"] = formatted_value
                    st.rerun()
                    
            except (ValueError, TypeError):
                st.error("Please enter a valid number (e.g., 50,000,000)")
                equity = 50000000  # Default fallback
        
    with input_col2:
        # Equity for Liquidation-Reentry and Fresh Capital Restart modes - goes to column 2
        if st.session_state.backtest_mode in ['standard', 'restart']:
            help_text = "Your cash equity per restart cycle. Format: 50,000,000" if st.session_state.backtest_mode == 'restart' else "Your cash equity (not including leverage). Format: 50,000,000"
            
            # Custom formatted equity input with commas
            equity_default = "50,000,000"
            if f"equity_formatted_{st.session_state.backtest_mode}" not in st.session_state:
                st.session_state[f"equity_formatted_{st.session_state.backtest_mode}"] = equity_default
            
            equity_input = st.text_input(
                "Equity ($)",
                value=st.session_state[f"equity_formatted_{st.session_state.backtest_mode}"],
                help=help_text,
                key=f"equity_text_{st.session_state.backtest_mode}",
                placeholder="50,000,000"
            )
            
            # Parse and validate the formatted input
            try:
                # Remove commas and convert to number
                equity_clean = equity_input.replace(",", "").replace("$", "").replace(" ", "")
                equity = float(equity_clean)
                
                # Validate minimum value
                if equity < 5000:
                    st.error("Minimum equity is $5,000")
                    equity = 5000
                
                # Update session state with properly formatted value
                formatted_value = f"{equity:,.0f}"
                if formatted_value != equity_input:
                    st.session_state[f"equity_formatted_{st.session_state.backtest_mode}"] = formatted_value
                    st.rerun()
                    
            except (ValueError, TypeError):
                st.error("Please enter a valid number (e.g., 50,000,000)")
                equity = 50000000  # Default fallback
        
        account_type = st.selectbox(
            "Account Type",
            ["reg_t", "portfolio"],
            format_func=lambda x: "Reg-T Account (Max 2:1)" if x == "reg_t" else "Portfolio Margin (Max 7:1)",
            help="Type of margin account",
            key="backtest_account_type"
        )
    
        # Dynamic leverage input based on account type
        if account_type == "reg_t":
            max_leverage = 2.0
            min_leverage = 1.0
            default_leverage = 2.0
        else:
            max_leverage = 7.0
            min_leverage = 1.0
            default_leverage = 4.0
        
        leverage = st.number_input(
            "Leverage",
            min_value=min_leverage,
            max_value=max_leverage,
            value=default_leverage,
            step=0.1,
            format="%.1f",
            help=f"Leverage multiplier (min {min_leverage:.1f}x, max {max_leverage:.1f}x for {account_type.replace('_', '-').title()})",
            key="backtest_leverage"
        )
        
        # Additional controls for Profit Threshold mode
        if st.session_state.backtest_mode == 'profit_threshold':
            profit_threshold_pct = st.number_input(
                "Profit Threshold (%)",
                min_value=10.0,
                max_value=500.0,
                value=100.0,
                step=10.0,
                help="Portfolio growth percentage to trigger rebalancing (e.g., 100% = double portfolio value)",
                key="profit_threshold_pct"
            )
            
            transaction_cost_bps = st.number_input(
                "Transaction Cost (bps)",
                min_value=0.0,
                max_value=50.0,
                value=5.0,
                step=0.5,
                help="Transaction cost per trade in basis points (5 bps = 0.05%)",
                key="profit_transaction_cost_bps"
            )
    
    with input_col3:
        # Validate date range
        if start_date >= end_date:
            st.markdown("""
            <div style="background-color: #1a1a1a; border: 2px solid #ff0000; padding: 1rem; color: #e0e0e0;">
                <strong style="color: #ff0000;">ERROR:</strong> Start date must be before end date
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Ensure equity is defined (it should be from either column 1 or 2)
        if 'equity' not in locals():
            equity = 50000000  # Fallback default value
        
        # Calculate total investment from equity and leverage
        initial_investment = equity * leverage
        
        # Calculate summary values (these are now for display purposes)
        cash_needed = equity  # This is the user's equity input
        margin_loan = initial_investment - cash_needed
        
        # Calculate actual trading days by counting data observations
        date_range_data = excel_data.loc[str(start_date):str(end_date)]
        if etf_choice == "SPY":
            trading_days = len(date_range_data.dropna(subset=['SPY']))
        else:
            trading_days = len(date_range_data.dropna(subset=['VTI']))
        
        # Mode-specific parameter summary card
        if st.session_state.backtest_mode == 'constant_leverage':
            st.markdown(f"""
            <div class="terminal-card" style="border-color: var(--accent-orange); margin-top: 1rem;">

            </div>
            """, unsafe_allow_html=True)
        elif st.session_state.backtest_mode == 'profit_threshold':
            st.markdown(f"""
            <div class="terminal-card" style="border-color: var(--accent-orange); margin-top: 1rem; padding: 0.75rem;">
                <div style="color: var(--accent-orange); font-weight: 600; font-size: 0.9rem; margin-bottom: 0.25rem;">PROFIT THRESHOLD REBALANCING SUMMARY</div>
                <div class="data-grid" style="grid-row-gap: 0.25rem;">
                    <div class="data-label" style="font-size: 0.75rem;">PERIOD:</div>
                    <div class="data-value" style="font-size: 0.75rem;">{start_date} TO {end_date}</div>
                    <div class="data-label" style="font-size: 0.75rem;">DURATION:</div>
                    <div class="data-value" style="font-size: 0.75rem;">{trading_days:,} TRADING DAYS</div>
                </div>
                <div style="color: var(--accent-orange); font-weight: 600; font-size: 0.85rem; margin: 0.5rem 0 0.25rem 0;">CONFIGURATION</div>
                <div class="data-grid" style="grid-row-gap: 0.25rem;">
                    <div class="data-label" style="font-size: 0.75rem;">LEVERAGE:</div>
                    <div class="data-value" style="font-size: 0.75rem;">{leverage:.1f}X</div>
                    <div class="data-label" style="font-size: 0.75rem;">THRESHOLD:</div>
                    <div class="data-value" style="font-size: 0.75rem;">{profit_threshold_pct:.0f}%</div>
                    <div class="data-label" style="font-size: 0.75rem;">COSTS:</div>
                    <div class="data-value" style="font-size: 0.75rem;">{transaction_cost_bps} BPS</div>
                </div>
                <div style="color: var(--accent-orange); font-weight: 600; font-size: 0.85rem; margin: 0.5rem 0 0.25rem 0;">POSITION</div>
                <div class="data-grid" style="grid-row-gap: 0.25rem;">
                    <div class="data-label" style="font-size: 0.75rem;">EQUITY:</div>
                    <div class="data-value" style="font-size: 0.75rem;">${cash_needed:,.0f}</div>
                    <div class="data-label" style="font-size: 0.75rem;">LOAN:</div>
                    <div class="data-value" style="font-size: 0.75rem;">${margin_loan:,.0f}</div>
                    <div class="data-label" style="font-size: 0.75rem;">TOTAL:</div>
                    <div class="data-value" style="font-size: 0.75rem;">${initial_investment:,.0f}</div>
                    <div class="data-label" style="font-size: 0.75rem;">REBALANCE AT:</div>
                    <div class="data-value" style="font-size: 0.75rem;">${initial_investment * (1 + profit_threshold_pct/100):,.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
        <div class="terminal-card" style="border-color: var(--accent-orange); margin-top: 1rem;">
            <div style="color: var(--accent-orange); font-weight: 600; margin-bottom: 0.5rem;">BACKTEST SUMMARY</div>
            <div class="data-grid">
                <div class="data-label">PERIOD:</div>
                <div class="data-value">{start_date} TO {end_date}</div>
                <div class="data-label">DURATION:</div>
                <div class="data-value">{trading_days:,} TRADING DAYS</div>
            </div>
            <div style="color: var(--accent-orange); font-weight: 600; margin: 1rem 0 0.5rem 0;">POSITION SUMMARY</div>
            <div class="data-grid">
                <div class="data-label">YOUR EQUITY:</div>
                <div class="data-value">${cash_needed:,.0f}</div>
                <div class="data-label">MARGIN LOAN:</div>
                <div class="data-value">${margin_loan:,.0f}</div>
                <div class="data-label">TOTAL POSITION:</div>
                <div class="data-value">${initial_investment:,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Run backtest button
    if st.button("RUN HISTORICAL BACKTEST", use_container_width=True, type="primary", key="run_backtest_button"):
        
        with st.spinner("RUNNING COMPREHENSIVE BACKTEST SIMULATION..."):
            
            if st.session_state.backtest_mode == 'profit_threshold':
                # Run profit threshold backtest
                results_df, metrics, rebalancing_events = run_profit_threshold_backtest(
                    etf=etf_choice,
                    start_date=str(start_date),
                    end_date=str(end_date),
                    initial_investment=initial_investment,
                    target_leverage=leverage,
                    account_type=account_type,
                    excel_data=excel_data,
                    profit_threshold_pct=profit_threshold_pct,
                    transaction_cost_bps=transaction_cost_bps
                )
                
                if results_df.empty:
                    st.error("❌ Backtest failed. Please check your parameters.")
                    return
                
                # Display profit threshold results
                st.markdown(f"""
                <div style="background-color: #1a1a1a; border: 1px solid #00ff00; padding: 1rem; color: #e0e0e0;">
                    <strong style="color: #00ff00;">PROFIT THRESHOLD BACKTEST COMPLETE:</strong> Analyzed {len(results_df):,} trading days with {metrics.get('Total Rebalances', 0)} profit-based rebalancing events and {metrics.get('Total Liquidations', 0)} liquidations
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced metrics summary for profit threshold
                st.markdown("### 📊 Profit Threshold Performance Dashboard")
                
                # Core Performance Metrics
                st.markdown("#### Core Performance Metrics")
                metric_row1_col1, metric_row1_col2, metric_row1_col3, metric_row1_col4 = st.columns(4)
                
                with metric_row1_col1:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Total Return</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Total Return (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">CAGR: {metrics['CAGR (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row1_col2:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Final Equity</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['Final Equity ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Max: ${metrics['Max Equity Achieved ($)']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_row1_col3:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Portfolio Growth</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Final Portfolio Growth (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Max: {metrics['Max Portfolio Growth (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row1_col4:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Sharpe Ratio</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Sharpe Ratio']:.3f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Max DD: {metrics['Max Drawdown (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("#### Profit Threshold Analytics")
                metric_row2_col1, metric_row2_col2, metric_row2_col3, metric_row2_col4 = st.columns(4)
                
                with metric_row2_col1:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Profit Threshold</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Profit Threshold (%)']:.0f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">{metrics['Total Rebalances']} rebalances</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row2_col2:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Avg Leverage</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Average Actual Leverage']:.2f}x</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Target: {metrics['Target Leverage']:.1f}x</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_row2_col3:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Transaction Costs</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['Total Transaction Costs ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">{metrics['Transaction Cost (% of Equity)']:.2f}% of equity</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row2_col4:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">All-In Costs</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['All-In Cost ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Interest + Trading - Dividends</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Strategy insights
                total_rebalances = metrics['Total Rebalances']
                growth_achieved = metrics['Final Portfolio Growth (%)']
                threshold = metrics['Profit Threshold (%)']
                
                if total_rebalances > 0:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #00ff00; padding: 1rem; color: #e0e0e0; margin-top: 1rem;">
                        <strong style="color: #00ff00;">PROFIT THRESHOLD STRATEGY SUCCESS:</strong> {total_rebalances} rebalancing events triggered by {threshold:.0f}% growth thresholds. 
                        Final portfolio growth: {growth_achieved:.1f}%. Strategy successfully locked in profits by scaling position size.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #00a2ff; padding: 1rem; color: #e0e0e0; margin-top: 1rem;">
                        <strong style="color: #00a2ff;">NO REBALANCING:</strong> Portfolio never reached {threshold:.0f}% growth threshold during backtest period. 
                        Consider lowering threshold or extending backtest period to see strategy in action.
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced portfolio performance chart
                st.markdown("### 📈 Portfolio Performance Analytics")
                portfolio_fig = create_enhanced_portfolio_chart(results_df, metrics, rebalancing_events)
                st.plotly_chart(portfolio_fig, use_container_width=True)
                

                
                # Margin Cushion Analytics Dashboard
                cushion_analysis.render_cushion_analytics_section(results_df, metrics, mode="profit_threshold")
                
                # Detailed Profit Threshold Rebalancing Analysis
                st.markdown("### 📋 Detailed Profit Threshold Analysis")
                
                if rebalancing_events:
                    rebalance_df = pd.DataFrame(rebalancing_events)
                    
                    # Calculate summary statistics
                    total_events = len(rebalance_df)
                    avg_growth = rebalance_df['growth_trigger_pct'].mean()
                    avg_cost = rebalance_df['transaction_cost'].mean()
                    total_cost = rebalance_df['transaction_cost'].sum()
                    
                    st.markdown(f"""
                    **Profit Threshold Summary:** {total_events} rebalancing events • Average trigger growth: {avg_growth:.1f}% • Total costs: ${total_cost:,.0f}
                    """)
                    
                    # Format display DataFrame
                    display_rebalance = rebalance_df.copy()
                    display_rebalance['Date'] = pd.to_datetime(display_rebalance['date']).dt.strftime('%Y-%m-%d')
                    display_rebalance['Growth Trigger'] = display_rebalance['growth_trigger_pct'].apply(lambda x: f"{x:.1f}%")
                    display_rebalance['Shares Added'] = display_rebalance['shares_change'].apply(lambda x: f"{x:+,.0f}")
                    display_rebalance['Transaction Cost'] = display_rebalance['transaction_cost'].apply(lambda x: f"${x:,.0f}")
                    display_rebalance['Equity Before'] = display_rebalance['equity_before'].apply(lambda x: f"${x:,.0f}")
                    display_rebalance['Equity After'] = display_rebalance['equity_after'].apply(lambda x: f"${x:,.0f}")
                    display_rebalance['Leverage Before'] = display_rebalance['leverage_before'].apply(lambda x: f"{x:.2f}x")
                    display_rebalance['Leverage After'] = display_rebalance['leverage_after'].apply(lambda x: f"{x:.2f}x")
                    display_rebalance['Portfolio Before'] = display_rebalance['portfolio_value_before'].apply(lambda x: f"${x:,.0f}")
                    display_rebalance['Portfolio After'] = display_rebalance['portfolio_value_after'].apply(lambda x: f"${x:,.0f}")
                    
                    display_columns = [
                        'Date', 'Growth Trigger', 'Shares Added', 'Transaction Cost', 
                        'Equity Before', 'Equity After', 'Leverage Before', 'Leverage After',
                        'Portfolio Before', 'Portfolio After'
                    ]
                    
                    final_rebalance_display = display_rebalance[display_columns]
                    
                    # Calculate dynamic height based on data rows (35px per row + 50px header)
                    dynamic_height = min(max(len(final_rebalance_display) * 35 + 50, 100), 400)
                    
                    st.dataframe(
                        final_rebalance_display,
                        use_container_width=True,
                        hide_index=True,
                        height=dynamic_height
                    )
                else:
                    st.info(f"No rebalancing events occurred. Portfolio never reached {profit_threshold_pct:.0f}% growth threshold.")
                
                # Detailed data expander for profit threshold
                with st.expander("🔍 Detailed Profit Threshold Data", expanded=False):
                    st.markdown(f"""
                    ### 📊 Complete Profit Threshold Dataset
                    
                    This dataset contains **{len(results_df):,} daily observations** from your {leverage:.1f}x profit threshold {etf_choice} strategy.
                    Tracks portfolio growth and rebalancing triggers based on {profit_threshold_pct:.0f}% profit thresholds.
                    """)
                    
                    # Format and display complete dataset
                    display_df = results_df.copy()
                    
                    # Format currency columns
                    currency_cols = ['Portfolio_Value', 'Margin_Loan', 'Equity', 'Maintenance_Margin_Required', 'Daily_Interest_Cost', 'Cumulative_Interest_Cost', 'Dividend_Payment', 'Cumulative_Dividends', 'Transaction_Cost_Today', 'Cumulative_Transaction_Costs', 'Next_Rebalance_Target']
                    for col in currency_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
                    
                    # Format percentage columns
                    pct_cols = ['Total_Growth_Pct', 'Growth_Since_Last_Rebalance_Pct', 'Profit_Threshold_Pct']
                    for col in pct_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%")
                    
                    # Format other columns
                    if 'Shares_Held' in display_df.columns:
                        display_df['Shares_Held'] = display_df['Shares_Held'].apply(lambda x: f"{x:,.2f}")
                    if 'Target_Leverage' in display_df.columns:
                        display_df['Target_Leverage'] = display_df['Target_Leverage'].apply(lambda x: f"{x:.2f}x")
                    if 'Actual_Leverage' in display_df.columns:
                        display_df['Actual_Leverage'] = display_df['Actual_Leverage'].apply(lambda x: f"{x:.2f}x")
                    
                    st.dataframe(display_df, use_container_width=True, height=400)
            
            elif st.session_state.backtest_mode == 'standard':
                # Run enhanced liquidation-reentry backtest
                results_df, metrics, round_analysis = run_liquidation_reentry_backtest(
                    etf=etf_choice,
                    start_date=str(start_date),
                    end_date=str(end_date),
                    initial_investment=initial_investment,
                    leverage=leverage,
                    account_type=account_type,
                    excel_data=excel_data
                )
                
                if results_df.empty:
                    st.error("❌ Backtest failed. Please check your parameters.")
                    return
                
                # Display enhanced results
                st.markdown(f"""
                <div style="background-color: #1a1a1a; border: 1px solid #00ff00; padding: 1rem; color: #e0e0e0;">
                    <strong style="color: #00ff00;">LIQUIDATION-REENTRY BACKTEST COMPLETE:</strong> Analyzed {len(results_df):,} trading days with {metrics.get('Total Liquidations', 0)} liquidation events
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced metrics summary with institutional-level presentation
                st.markdown("### 📊 Performance Dashboard")
                
                # Create two rows of metrics for comprehensive display
                st.markdown("#### Core Performance Metrics")
                metric_row1_col1, metric_row1_col2, metric_row1_col3, metric_row1_col4 = st.columns(4)
                
                with metric_row1_col1:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Total Return</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Total Return (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">CAGR: {metrics['CAGR (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row1_col2:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Final Equity</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['Final Equity ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Max: ${metrics['Max Equity Achieved ($)']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_row1_col3:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Sharpe Ratio</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Sharpe Ratio']:.3f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Sortino: {metrics['Sortino Ratio']:.3f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row1_col4:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Max Drawdown</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Max Drawdown (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Duration: {metrics['Max Drawdown Duration (days)']:.0f} days</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("#### Trading & Risk Analytics")
                metric_row2_col1, metric_row2_col2, metric_row2_col3, metric_row2_col4 = st.columns(4)
                
                with metric_row2_col1:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Total Liquidations</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{int(metrics['Total Liquidations'])}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Avg every {metrics['Avg Days Between Liquidations']:.0f} days</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row2_col2:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Time in Market</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Time in Market (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">{metrics['Active Position Days']} active days</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_row2_col3:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Avg Loss per Liquidation</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Avg Loss Per Liquidation (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Worst: {metrics['Worst Single Loss (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row2_col4:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Net Interest Cost</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['Net Interest Cost ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Interest: ${metrics['Total Interest Paid ($)']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Reality check and strategy insights
                if metrics['Total Liquidations'] > 0:
                    loss_rate = (metrics['Total Liquidations'] / metrics['Total Cycles']) * 100 if metrics['Total Cycles'] > 0 else 0
                    avg_survival = metrics['Avg Days Between Liquidations']
                    
                    if loss_rate > 80:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 2px solid #ff0000; padding: 1rem; color: #e0e0e0;">
                            <strong style="color: #ff0000;">HIGH RISK STRATEGY:</strong> {loss_rate:.0f}% of positions ended in liquidation. 
                            Average survival time: {avg_survival:.0f} days. Consider reducing leverage significantly.
                        </div>
                        """, unsafe_allow_html=True)
                    elif loss_rate > 50:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px solid #ffff00; padding: 1rem; color: #e0e0e0;">
                            <strong style="color: #ffff00;">MODERATE RISK:</strong> {loss_rate:.0f}% liquidation rate with {avg_survival:.0f} days average survival. 
                            This strategy requires significant capital reserves and risk management.
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #1a1a1a; border: 1px solid #00a2ff; padding: 1rem; color: #e0e0e0;">
                            <strong style="color: #00a2ff;">STRATEGY ANALYSIS:</strong> {loss_rate:.0f}% liquidation rate. Positions survived an average of {avg_survival:.0f} days. 
                            While manageable, consider position sizing and stop-loss strategies.
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background-color: #1a1a1a; border: 1px solid #00ff00; padding: 1rem; color: #e0e0e0; margin-top: 1rem;">
                        <strong style="color: #00ff00;">NO LIQUIDATIONS:</strong> No liquidations occurred during this backtest period
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced portfolio performance chart
                st.markdown("### 📈 Performance Analytics Advanced Visualizations")
                portfolio_fig = create_enhanced_portfolio_chart(results_df, metrics)
                st.plotly_chart(portfolio_fig, use_container_width=True)
                
                # Advanced liquidation and risk analysis
                st.markdown("### 🎯 Advanced Risk & Liquidation Analysis")
                liquidation_fig = create_liquidation_analysis_chart(results_df, metrics)
                st.plotly_chart(liquidation_fig, use_container_width=True)
                
                # Margin Cushion Analytics Dashboard
                cushion_analysis.render_cushion_analytics_section(results_df, metrics, mode="liquidation_reentry")
                
                # Detailed Round Analysis Section
                st.markdown("### 📋 Detailed Round Analysis")
                
                if round_analysis:
                    # Convert round analysis to DataFrame for display
                    rounds_df = pd.DataFrame(round_analysis)
                    
                    # Display summary info
                    total_rounds = len(rounds_df)
                    margin_call_rounds = rounds_df['Margin_Call'].sum()
                    successful_rounds = total_rounds - margin_call_rounds
                    
                    st.markdown(f"""
                    **Position Cycle Summary:** {total_rounds} total rounds • {margin_call_rounds} margin calls • {successful_rounds} successful completions
                    """)
                    
                    # Prepare display DataFrame with proper formatting
                    display_rounds = rounds_df.copy()
                    
                    # Format dates
                    display_rounds['Start Date'] = pd.to_datetime(display_rounds['Start_Date']).dt.strftime('%Y-%m-%d')
                    display_rounds['End Date'] = pd.to_datetime(display_rounds['End_Date']).dt.strftime('%Y-%m-%d')
                    
                    # Format currency columns
                    display_rounds['Capital'] = display_rounds['Capital_Deployed'].apply(lambda x: f"${x:,.0f}")
                    display_rounds['Final Value'] = display_rounds['Final_Value'].apply(lambda x: f"${x:,.0f}")
                    display_rounds['Start Portfolio'] = display_rounds['Start_Portfolio_Value'].apply(lambda x: f"${x:,.0f}")
                    display_rounds['End Portfolio'] = display_rounds['End_Portfolio_Value'].apply(lambda x: f"${x:,.0f}")
                    
                    # Format percentage columns
                    display_rounds['Price Δ%'] = display_rounds['Price_Change_Pct'].apply(lambda x: f"{x:+.1f}%")
                    display_rounds['Profit%'] = display_rounds['Profit_Pct'].apply(lambda x: f"{x:.1f}%" if x > 0 else "")
                    display_rounds['Loss%'] = display_rounds['Loss_Pct'].apply(lambda x: f"{x:.1f}%" if x > 0 else "")
                    
                    # Format margin call column
                    display_rounds['Margin Call'] = display_rounds['Margin_Call'].apply(lambda x: "🔴 YES" if x else "🟢 NO")
                    
                    # Select and order columns for display
                    display_columns = [
                        'Round', 'Days', 'Start Date', 'End Date', 'Price Δ%', 
                        'Capital', 'Final Value', 'Start Portfolio', 'End Portfolio',
                        'Margin Call', 'Profit%', 'Loss%'
                    ]
                    
                    final_display = display_rounds[display_columns]
                    
                    # Display the table
                    st.dataframe(
                        final_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Round": st.column_config.NumberColumn("Round #", width="small"),
                            "Days": st.column_config.NumberColumn("Days", width="small"),
                            "Start Date": st.column_config.TextColumn("Start Date", width="medium"),
                            "End Date": st.column_config.TextColumn("End Date", width="medium"),
                            "Price Δ%": st.column_config.TextColumn("Price Δ%", width="small"),
                            "Capital": st.column_config.TextColumn("Capital", width="medium"),
                            "Final Value": st.column_config.TextColumn("Final Value", width="medium"),
                            "Start Portfolio": st.column_config.TextColumn("Start Portfolio", width="medium"),
                            "End Portfolio": st.column_config.TextColumn("End Portfolio", width="medium"),
                            "Margin Call": st.column_config.TextColumn("Margin Call", width="small"),
                            "Profit%": st.column_config.TextColumn("Profit%", width="small"),
                            "Loss%": st.column_config.TextColumn("Loss%", width="small")
                        }
                    )
                    
                    # Key insights
                    if margin_call_rounds > 0:
                        avg_loss = rounds_df[rounds_df['Margin_Call'] == True]['Loss_Pct'].mean()
                        avg_survival = rounds_df[rounds_df['Margin_Call'] == True]['Days'].mean()
                        
                        st.info(f"""
                        💡 **Round Analysis Insights**: 
                        Average loss per liquidation: {avg_loss:.1f}% • 
                        Average survival time: {avg_survival:.0f} days • 
                        Liquidation rate: {(margin_call_rounds/total_rounds)*100:.1f}%
                        """)
                else:
                    st.info("No position rounds to analyze. Check your backtest parameters.")
                
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
                    | **Cumulative_Interest_Cost** | Running total of all interest costs since backtest start |
                    | **Dividend_Payment** | Dividend cash received (automatically reinvested) |
                    | **Cumulative_Dividends** | Running total of all dividends received since backtest start |
                    | **Fed_Funds_Rate** | Federal Reserve interest rate (%) |
                    | **Margin_Rate** | Your borrowing rate (Fed Funds + spread) |
                    """)
                    
                    # Display the full dataset
                    st.markdown("### 📈 Complete Daily Data")
                    
                    # Format the dataframe for better display
                    display_df = results_df.copy()
                    
                    # Format currency columns
                    currency_cols = ['Portfolio_Value', 'Margin_Loan', 'Equity', 'Maintenance_Margin_Required', 'Daily_Interest_Cost', 'Cumulative_Interest_Cost', 'Cumulative_Dividends']
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
                
            else:  # Fresh Capital Restart mode
                # Run fresh capital restart backtest
                results_df, metrics, round_analysis = run_margin_restart_backtest(
                    etf=etf_choice,
                    start_date=str(start_date),
                    end_date=str(end_date),
                    initial_investment=initial_investment,
                    leverage=leverage,
                    account_type=account_type,
                    excel_data=excel_data
                )
                
                if results_df.empty:
                    st.error("❌ Backtest failed. Please check your parameters.")
                    return
                
                # Display fresh capital restart results with same format as liquidation-reentry
                st.success(f"✅ **Fresh Capital Restart Backtest Complete** - Analyzed {len(results_df):,} trading days with {metrics.get('Total Liquidations', 0)} liquidation events, {metrics.get('Waiting Days', 0)} waiting days, and unlimited fresh capital")
                
                # Enhanced metrics summary with fresh capital focus
                st.markdown("### 📊 Performance Dashboard")
                
                # Core Performance Metrics (same as liquidation-reentry)
                st.markdown("#### Core Performance Metrics")
                metric_row1_col1, metric_row1_col2, metric_row1_col3, metric_row1_col4 = st.columns(4)
                
                with metric_row1_col1:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Total Return</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Total Return (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">CAGR: {metrics['CAGR (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row1_col2:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Final Equity</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['Final Equity ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Max: ${metrics['Max Equity Achieved ($)']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_row1_col3:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Sharpe Ratio</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Sharpe Ratio']:.3f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Sortino: {metrics['Sortino Ratio']:.3f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row1_col4:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Max Drawdown</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Max Drawdown (%)']:.1f}%</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Duration: {metrics['Max Drawdown Duration (days)']:.0f} days</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("#### Fresh Capital Strategy Analytics")
                metric_row2_col1, metric_row2_col2, metric_row2_col3, metric_row2_col4 = st.columns(4)
                
                with metric_row2_col1:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Total Liquidations</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{int(metrics['Total Liquidations'])}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Rate: {metrics['Liquidation Rate (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row2_col2:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Total Capital Deployed</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['Total Capital Deployed ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">${metrics['Fresh Capital Per Round ($)']:,.0f} per round</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_row2_col3:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Avg Survival Days</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">{metrics['Avg Days Between Liquidations']:.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Time in Market: {metrics['Time in Market (%)']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with metric_row2_col4:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #333333; padding: 1rem; text-align: center;">
                        <div style="color: #ff8c00; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Net Interest Cost</div>
                        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">${metrics['Net Interest Cost ($)']:,.0f}</div>
                        <div style="color: #a0a0a0; font-size: 0.9rem;">Interest: ${metrics['Total Interest Paid ($)']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Fresh capital specific insights
                total_capital = metrics['Total Capital Deployed ($)']
                net_result = (metrics['Total Return (%)'] / 100) * total_capital if total_capital > 0 else 0
                liquidation_rate = metrics['Liquidation Rate (%)']
                
                if liquidation_rate > 80:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 2px solid #ff0000; padding: 1rem; color: #e0e0e0; margin-top: 1rem;">
                        <strong style="color: #ff0000;">🚨 HIGH RISK STRATEGY:</strong> {liquidation_rate:.0f}% liquidation rate with fresh capital. 
                        Total capital deployed: ${total_capital:,.0f}. This strategy would require substantial capital reserves.
                    </div>
                    """, unsafe_allow_html=True)
                elif liquidation_rate > 50:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #ffff00; padding: 1rem; color: #e0e0e0; margin-top: 1rem;">
                        <strong style="color: #ffff00;">⚠️ MODERATE RISK:</strong> {liquidation_rate:.0f}% liquidation rate. 
                        Fresh capital deployment: ${total_capital:,.0f}. Consider risk management protocols.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #1a1a1a; border: 1px solid #00a2ff; padding: 1rem; color: #e0e0e0; margin-top: 1rem;">
                        <strong style="color: #00a2ff;">💡 Fresh Capital Analysis:</strong> {liquidation_rate:.0f}% liquidation rate with unlimited capital assumption. 
                        Total deployment: ${total_capital:,.0f}. Compare with liquidation-reentry mode for realistic assessment.
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced portfolio performance chart (same as liquidation-reentry)
                st.markdown("### 📈 Performance Analytics Advanced Visualizations")
                portfolio_fig = create_enhanced_portfolio_chart(results_df, metrics)
                st.plotly_chart(portfolio_fig, use_container_width=True)
                
                # Advanced liquidation and risk analysis (same as liquidation-reentry)
                st.markdown("### 🎯 Advanced Risk & Liquidation Analysis")
                liquidation_fig = create_liquidation_analysis_chart(results_df, metrics)
                st.plotly_chart(liquidation_fig, use_container_width=True)
                
                # Margin Cushion Analytics Dashboard (Fresh Capital Mode)
                cushion_analysis.render_cushion_analytics_section(results_df, metrics, mode="fresh_capital")
                
                # Detailed Round Analysis Section (same as liquidation-reentry)
                st.markdown("### 📋 Detailed Round Analysis")
                
                if round_analysis:
                    # Convert round analysis to DataFrame for display
                    rounds_df = pd.DataFrame(round_analysis)
                    
                    # Display summary info
                    total_rounds = len(rounds_df)
                    margin_call_rounds = rounds_df['Margin_Call'].sum()
                    successful_rounds = total_rounds - margin_call_rounds
                    
                    st.markdown(f"""
                    **Fresh Capital Position Summary:** {total_rounds} total rounds • {margin_call_rounds} margin calls • {successful_rounds} successful completions  
                    ⚡ **Fresh Capital:** ${metrics['Fresh Capital Per Round ($)']:,.0f} deployed per round regardless of previous results
                    """)
                    
                    # Prepare display DataFrame with proper formatting (same as liquidation-reentry)
                    display_rounds = rounds_df.copy()
                    
                    # Format dates
                    display_rounds['Start Date'] = pd.to_datetime(display_rounds['Start_Date']).dt.strftime('%Y-%m-%d')
                    display_rounds['End Date'] = pd.to_datetime(display_rounds['End_Date']).dt.strftime('%Y-%m-%d')
                    
                    # Format currency columns
                    display_rounds['Capital'] = display_rounds['Capital_Deployed'].apply(lambda x: f"${x:,.0f}")
                    display_rounds['Final Value'] = display_rounds['Final_Value'].apply(lambda x: f"${x:,.0f}")
                    display_rounds['Start Portfolio'] = display_rounds['Start_Portfolio_Value'].apply(lambda x: f"${x:,.0f}")
                    display_rounds['End Portfolio'] = display_rounds['End_Portfolio_Value'].apply(lambda x: f"${x:,.0f}")
                    
                    # Format percentage columns
                    display_rounds['Price Δ%'] = display_rounds['Price_Change_Pct'].apply(lambda x: f"{x:+.1f}%")
                    display_rounds['Profit%'] = display_rounds['Profit_Pct'].apply(lambda x: f"{x:.1f}%" if x > 0 else "")
                    display_rounds['Loss%'] = display_rounds['Loss_Pct'].apply(lambda x: f"{x:.1f}%" if x > 0 else "")
                    
                    # Format margin call column
                    display_rounds['Margin Call'] = display_rounds['Margin_Call'].apply(lambda x: "🔴 YES" if x else "🟢 NO")
                    
                    # Select and order columns for display
                    display_columns = [
                        'Round', 'Days', 'Start Date', 'End Date', 'Price Δ%', 
                        'Capital', 'Final Value', 'Start Portfolio', 'End Portfolio',
                        'Margin Call', 'Profit%', 'Loss%'
                    ]
                    
                    final_display = display_rounds[display_columns]
                    
                    # Display the table
                    st.dataframe(
                        final_display,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Round": st.column_config.NumberColumn("Round #", width="small"),
                            "Days": st.column_config.NumberColumn("Days", width="small"),
                            "Start Date": st.column_config.TextColumn("Start Date", width="medium"),
                            "End Date": st.column_config.TextColumn("End Date", width="medium"),
                            "Price Δ%": st.column_config.TextColumn("Price Δ%", width="small"),
                            "Capital": st.column_config.TextColumn("Fresh Capital", width="medium"),
                            "Final Value": st.column_config.TextColumn("Final Value", width="medium"),
                            "Start Portfolio": st.column_config.TextColumn("Start Portfolio", width="medium"),
                            "End Portfolio": st.column_config.TextColumn("End Portfolio", width="medium"),
                            "Margin Call": st.column_config.TextColumn("Margin Call", width="small"),
                            "Profit%": st.column_config.TextColumn("Profit%", width="small"),
                            "Loss%": st.column_config.TextColumn("Loss%", width="small")
                        }
                    )
                    
                    # Fresh capital specific insights
                    if margin_call_rounds > 0:
                        avg_loss = rounds_df[rounds_df['Margin_Call'] == True]['Loss_Pct'].mean()
                        avg_survival = rounds_df[rounds_df['Margin_Call'] == True]['Days'].mean()
                        
                        st.info(f"""
                        💡 **Fresh Capital Round Insights**: 
                        Average loss per liquidation: {avg_loss:.1f}% • 
                        Average survival time: {avg_survival:.0f} days • 
                        Liquidation rate: {(margin_call_rounds/total_rounds)*100:.1f}% •
                        Fresh capital per round: ${metrics['Fresh Capital Per Round ($)']:,.0f}
                        """)
                else:
                    st.info("No position rounds to analyze. Check your backtest parameters.")
                
                # Detailed backtest data expander for fresh capital mode
                with st.expander("🔍 Detailed Backtest Data & Variables", expanded=False):
                    st.markdown(f"""
                    ### 📊 Complete Dataset: Fresh Capital Restart Backtest Results
                    
                    This dataset contains **{len(results_df):,} daily observations** from your {leverage:.1f}x leveraged {etf_choice} fresh capital strategy.
                    Each row represents one trading day with **unlimited fresh capital assumption** after each liquidation.
                    """)
                    
                    # Enhanced variable explanations for fresh capital mode
                    st.markdown(f"""
                    **📋 Fresh Capital Variable Definitions:**
                    
                    | Variable | Description |
                    |----------|-------------|
                    | **ETF_Price** | Daily closing price of the selected ETF |
                    | **Current_Equity** | Fresh capital available (always equals cash per round in this mode) |
                    | **Position_Status** | Fresh_Capital_Deployed, Active_Position, Liquidated_Fresh_Capital_Ready |
                    | **Cycle_Number** | Sequential fresh capital deployment number |
                    | **Days_In_Position** | Days in current fresh capital position |
                    | **Wait_Days_Remaining** | Days remaining in 2-day cooling period after liquidation |
                    | **Shares_Held** | Number of shares in current fresh capital position |
                    | **Portfolio_Value** | Total market value of fresh capital holdings |
                    | **Margin_Loan** | Outstanding loan balance for current fresh capital position |
                    | **Equity** | Current equity value in active position |
                    | **Is_Margin_Call** | TRUE when fresh capital position liquidated |
                    | **Daily_Interest_Cost** | Interest charged on margin loan for that day |
                    | **Cumulative_Interest_Cost** | Running total of all interest costs since backtest start |
                    | **Dividend_Payment** | Dividend cash received (automatically reinvested) |
                    | **Cumulative_Dividends** | Running total of all dividends received since backtest start |
                    | **Fresh Capital Per Round** | Amount of fresh capital deployed per round |
                    | **Total Capital Deployed** | Cumulative fresh capital used across all rounds |
                    
                    **🔄 Fresh Capital Logic:**
                    - After each margin call → Deploy new ${metrics['Fresh Capital Per Round ($)']:,.0f}
                    - No equity depletion → Unlimited capital assumption
                    - 2-day waiting period → Same as liquidation-reentry mode
                    """)
                    
                    # Display the full dataset (same formatting as liquidation-reentry)
                    st.markdown("### 📈 Complete Daily Data")
                    
                    # Format the dataframe for better display
                    display_df = results_df.copy()
                    
                    # Format currency columns
                    currency_cols = ['Portfolio_Value', 'Margin_Loan', 'Equity', 'Maintenance_Margin_Required', 'Daily_Interest_Cost', 'Cumulative_Interest_Cost', 'Dividend_Payment', 'Cumulative_Dividends']
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
    
    # Parameter sweep section
    if parameter_sweep is not None:
        try:
            parameter_sweep.render_parameter_sweep_section(etf_choice, start_date, end_date, equity, leverage, account_type, excel_data)
        except Exception as e:
            st.error(f"Parameter sweep error: {str(e)}")
            st.info("📊 Parameter sweep functionality temporarily unavailable. Please use individual backtests above.")
    else:
        st.info("📊 Parameter sweep module not found. Individual backtests are available above.")
    
    # Educational section
    with st.expander("📚 Understanding the Enhanced Backtest Modes", expanded=False):
        st.markdown("""
        ### 📈 Profit Threshold Rebalancing Mode (GROWTH-BASED STRATEGY)
        
        **Growth-Based Leverage Rebalancing:**
        This sophisticated strategy locks in profits by rebalancing back to target leverage when portfolio growth hits specified thresholds.
        
        **Exact Process:**
        1. **Initial Setup**: Start with target leverage (e.g., 2x) using initial equity
        2. **Growth Monitoring**: Track portfolio value vs growth threshold (e.g., 100% growth)
        3. **Threshold Trigger**: When portfolio grows by threshold percentage → check current leverage
        4. **Leverage Assessment**: If leverage dropped below target due to gains → rebalance
        5. **Borrow More Strategy**: Only borrows additional capital to buy more shares (never sells)
        6. **Lock in Profits**: Scales position size with new equity base at target leverage
        7. **Compound Growth**: Maintains consistent leverage exposure as wealth grows
        
        **Key Strategy Logic:**
        - 🎯 **Profit Monitoring**: Tracks portfolio growth from last rebalance point
        - 📈 **Threshold Trigger**: User-configurable growth percentage (default 100%)
        - ⚖️ **Leverage Restoration**: Rebalances back to target leverage with new equity base
        - 💰 **Growth Capture**: Only borrows more to scale up (never sells winners)
        - 🔄 **Compound Effect**: Each rebalance uses higher equity base for next threshold
        - 📊 **Growth Analytics**: Tracks all rebalancing events and growth milestones
        
        **Example Walkthrough:**
        1. **Start**: 1M equity @ 2x leverage = 2M position
        2. **Growth**: Portfolio grows to $4M (100% growth threshold hit!)
        3. **Current State**: 3M equity, 1M loan, 1.33x leverage (below 2x target)
        4. **Rebalance Action**: Borrow 2M more → 6M total position @ 2x leverage
        5. **Result**: Locked in profits by scaling position size with target leverage
        
        **When to Use:**
        - Systematic profit-taking with continued market exposure
        - Wealth building through leveraged growth compounding
        - Maintaining consistent risk exposure as portfolio grows
        - Testing growth-based rebalancing strategies
        

        
        ### ⚡ Liquidation-Reentry Mode (REALISTIC SIMULATION)
        
        **Advanced Realistic Simulation:**
        This is the **most sophisticated and realistic** backtest mode for understanding margin call impact.
        
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
        3. **2-Day Wait**: Same cooling-off period as liquidation-reentry mode
        4. **Fresh Capital**: Deploy NEW full position (unlimited money assumption)
        5. **Frequency Analysis**: Track how often margin calls occur
        
        **When to Use:**
        - Academic comparison with liquidation-reentry mode
        - Understanding margin call frequency patterns
        - Analyzing market volatility impact on leverage strategies
        
        ### 🎯 Professional Strategy Comparison Guide
        
        **Which Strategy Should You Choose?**
        """)
        
        # Add CSS for table styling with bright gray borders
        st.markdown("""
        <style>
        /* Style the strategy comparison table with bright gray borders */
        .stMarkdown table {
            border-collapse: collapse;
            margin: 1rem 0;
        }
        .stMarkdown table th, .stMarkdown table td {
            border: 1px solid #a0a0a0 !important;
            padding: 8px 12px;
        }
        .stMarkdown table th {
            background-color: rgba(160, 160, 160, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        | Strategy | Best For | Risk Level | Capital Requirement |
        |----------|----------|------------|-------------------|
        | **Liquidation-Reentry** | Realistic testing | High | Limited (depletes over time) |
        | **Fresh Capital Restart** | Academic analysis | High | Unlimited (theoretical) |
        | **Profit Threshold** | Wealth building | Medium | Growing (compounds profits) |
        """)
        
        st.markdown("""
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
        <h3 style="color: white; margin: 0;">🎯 Advanced Historical Backtest Engine</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 1rem 0 0 0; font-size: 1.1rem;">
                    <strong>Advanced Features:</strong> Profit Threshold Rebalancing | Growth-Based Strategies | Liquidation-Reentry Logic<br/>
        <strong>Professional Analysis:</strong> Fresh Capital Analysis | Compound Growth Analytics | Advanced Risk Metrics<br/>
        <strong>Research Tools:</strong> Sortino Ratio | Drawdown Duration | Portfolio Growth Analytics | Cost Attribution
        </p>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Professional-grade implementation | Real market data | Hedge fund-level analytics | Custom leverage visualization
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Function to be called from main app
def show_historical_backtest():
    """Entry point for the Historical Backtest tab"""
    render_historical_backtest_tab() 
    
    
