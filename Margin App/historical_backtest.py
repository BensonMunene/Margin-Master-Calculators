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

# Optional cushion analytics import
try:
    import cushion_analysis
    CUSHION_ANALYTICS_AVAILABLE = False
except ImportError:
    CUSHION_ANALYTICS_AVAILABLE = False

# Cache data loading for performance
@st.cache_data(ttl=3600)
def load_comprehensive_data():
    """Load ALL required data from ONLY the ETFs and Fed Funds Data.xlsx file"""
    try:
        # Define directory paths
        local_dir = r"D:\Benson\aUpWork\Ben Ruff\Implementation\Data"
        github_dir = "Data"
        
        # Choose which directory to use (True for local, False for GitHub)
        use_local = False
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
            
            # Record round start information
            round_start_date = date
            round_start_price = current_price
            round_start_portfolio_value = position_value
            round_start_equity = current_equity
            
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
        'Initial Investment ($)': cash_investment,
        'Leverage Used': leverage
    }
    
    return df_results, metrics

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
            
            # Calculate daily interest cost
            daily_interest_cost = margin_loan * daily_interest_rate
            margin_loan += daily_interest_cost
            total_interest_paid += daily_interest_cost
            
            # Handle dividend payments
            dividend_received = 0
            if dividend_payment > 0:
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
                daily_result['Position_Status'] = 'Active_Position'
            
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
        'Initial Investment ($)': cash_per_round,
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

def create_enhanced_portfolio_chart(df_results: pd.DataFrame, metrics: Dict[str, float]) -> go.Figure:
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
            hovertemplate='Date: %{x}<br>Portfolio Value: $%{y:,.0f}<br><extra></extra>'
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
            hovertemplate='Date: %{x}<br>Equity: $%{y:,.0f}<br><extra></extra>'
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
            hovertemplate='Date: %{x}<br>Maintenance Margin Required: $%{y:,.0f}<br><extra></extra>'
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
    
    # Cumulative P&L Attribution: Dividends and Loan Interests (moved from row 4, col 2)
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
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_results.index,
            y=cumulative_dividends,
            name='Cumulative Dividends',
            line=dict(color='#28B463', width=2),
            hovertemplate='Date: %{x}<br>Dividends: +$%{y:,.0f}<extra></extra>'
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
    
    # Position Status Timeline (moved from row 2, col 1)
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
                row=4, col=2
            )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"Comprehensive Portfolio Analysis: {metrics.get('Leverage Used', 0):.1f}x Leverage | {metrics.get('Total Liquidations', 0)} Liquidations | {metrics.get('CAGR (%)', 0):.1f}% CAGR",
            'x': 0.5,
            'font': {'size': 16, 'color': '#2C3E50'}
        },
        height=1200,
        showlegend=True,
        legend=dict(x=1.02, y=1, bgcolor='rgba(255,255,255,0.8)'),
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    # Update axes styling
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E8E8E8')
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
    
    # Display cushion analytics availability status
    if CUSHION_ANALYTICS_AVAILABLE:
        st.success("🛡️ **Cushion Analytics**: Advanced margin risk management features enabled")
    else:
        st.info("ℹ️ **Cushion Analytics**: Optional module not found. Basic backtest functionality available.")
    
    # Add backtest mode selection
    st.markdown("### 🎯 Select Backtest Mode")
    
    backtest_col1, backtest_col2 = st.columns(2)
    
    with backtest_col1:
        if st.button(
            "⚡ Liquidation-Reentry",
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
                <li>✅ Fresh capital deployed after each margin call (based on Initial Investment)</li>
                <li>✅ 2-day waiting period after liquidation (same as liquidation-reentry)</li>
                <li>✅ Shows frequency and timing of margin calls with unlimited resources</li>
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
        
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            help="When to end the backtest",
            key="backtest_end_date"
        )
        
        # Validate date range
        if start_date >= end_date:
            st.error("❌ Start date must be before end date!")
            return
    
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
        
        # Show parameter summary
        cash_needed = initial_investment / leverage
        margin_loan = initial_investment - cash_needed
        
        # Calculate actual trading days by counting data observations
        date_range_data = excel_data.loc[str(start_date):str(end_date)]
        if etf_choice == "SPY":
            trading_days = len(date_range_data.dropna(subset=['SPY']))
        else:
            trading_days = len(date_range_data.dropna(subset=['VTI']))
        
        st.markdown(f"""
        <div style="background: #f0f8ff; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
            <strong>📊 Backtest Summary:</strong><br>
            Period: <strong>{start_date} to {end_date}</strong><br>
            Duration: <strong>{trading_days:,} trading days</strong><br><br>
            <strong>💰 Position Summary:</strong><br>
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
                
                # Margin Cushion Analytics Dashboard (Optional)
                if CUSHION_ANALYTICS_AVAILABLE:
                    cushion_analysis.render_cushion_analytics_section(results_df, metrics, mode="liquidation_reentry")
                else:
                    st.info("💡 **Cushion Analytics**: Optional module not available. To enable advanced cushion risk management, ensure cushion_analysis.py is present.")
                
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
                    
                    # Download option for round analysis
                    rounds_csv = rounds_df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download Round Analysis",
                        data=rounds_csv,
                        file_name=f"round_analysis_{etf_choice}_{leverage:.1f}x_{start_date}_to_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download complete round-by-round analysis data"
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
                    
                    # Download option for detailed data
                    detailed_csv = results_df.to_csv()
                    st.download_button(
                        label="📊 Download Complete Dataset",
                        data=detailed_csv,
                        file_name=f"detailed_backtest_data_{etf_choice}_{leverage:.1f}x_{start_date}_to_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download all daily calculations for external analysis"
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
                st.success(f"🔄 **Fresh Capital Restart Backtest Complete!** Analyzed {len(results_df):,} trading days with {metrics.get('Total Liquidations', 0)} liquidation events, {metrics.get('Waiting Days', 0)} waiting days, and unlimited fresh capital")
                
                # Enhanced metrics summary with fresh capital focus
                st.markdown("### 📊 Institutional Performance Dashboard")
                
                # Core Performance Metrics (same as liquidation-reentry)
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
                
                st.markdown("#### Fresh Capital Strategy Analytics")
                metric_row2_col1, metric_row2_col2, metric_row2_col3, metric_row2_col4 = st.columns(4)
                
                with metric_row2_col1:
                    st.metric(
                        "Total Liquidations",
                        f"{int(metrics['Total Liquidations'])}",
                        delta=f"Rate: {metrics['Liquidation Rate (%)']:.1f}%"
                    )
                    
                with metric_row2_col2:
                    st.metric(
                        "Total Capital Deployed",
                        f"${metrics['Total Capital Deployed ($)']:,.0f}",
                        delta=f"${metrics['Fresh Capital Per Round ($)']:,.0f} per round"
                    )
                
                with metric_row2_col3:
                    st.metric(
                        "Avg Survival Days",
                        f"{metrics['Avg Days Between Liquidations']:.0f}",
                        delta=f"Time in Market: {metrics['Time in Market (%)']:.1f}%"
                    )
                    
                with metric_row2_col4:
                    st.metric(
                        "Net Interest Cost",
                        f"${metrics['Net Interest Cost ($)']:,.0f}",
                        delta=f"Interest: ${metrics['Total Interest Paid ($)']:,.0f}"
                    )
                
                # Fresh capital specific insights
                total_capital = metrics['Total Capital Deployed ($)']
                net_result = (metrics['Total Return (%)'] / 100) * total_capital if total_capital > 0 else 0
                liquidation_rate = metrics['Liquidation Rate (%)']
                
                if liquidation_rate > 80:
                    st.error(f"""
                    🚨 **HIGH RISK STRATEGY**: {liquidation_rate:.0f}% liquidation rate with fresh capital. 
                    Total capital deployed: ${total_capital:,.0f}. This strategy would require massive capital reserves.
                    """)
                elif liquidation_rate > 50:
                    st.warning(f"""
                    ⚠️ **MODERATE RISK**: {liquidation_rate:.0f}% liquidation rate. 
                    Fresh capital deployment: ${total_capital:,.0f}. Consider risk management protocols.
                    """)
                else:
                    st.info(f"""
                    💡 **Fresh Capital Analysis**: {liquidation_rate:.0f}% liquidation rate with unlimited capital assumption. 
                    Total deployment: ${total_capital:,.0f}. Compare with liquidation-reentry mode for realistic assessment.
                    """)
                
                # Enhanced portfolio performance chart (same as liquidation-reentry)
                st.markdown("### 📈 Institutional-Grade Performance Analytics")
                portfolio_fig = create_enhanced_portfolio_chart(results_df, metrics)
                st.plotly_chart(portfolio_fig, use_container_width=True)
                
                # Advanced liquidation and risk analysis (same as liquidation-reentry)
                st.markdown("### 🎯 Advanced Risk & Liquidation Analysis")
                liquidation_fig = create_liquidation_analysis_chart(results_df, metrics)
                st.plotly_chart(liquidation_fig, use_container_width=True)
                
                # Margin Cushion Analytics Dashboard (Optional - Fresh Capital Mode)
                if CUSHION_ANALYTICS_AVAILABLE:
                    cushion_analysis.render_cushion_analytics_section(results_df, metrics, mode="fresh_capital")
                else:
                    st.info("💡 **Cushion Analytics**: Optional module not available. To enable advanced cushion risk management, ensure cushion_analysis.py is present.")
                
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
                    
                    # Download option for round analysis
                    rounds_csv = rounds_df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download Fresh Capital Round Analysis",
                        data=rounds_csv,
                        file_name=f"fresh_capital_analysis_{etf_choice}_{leverage:.1f}x_{start_date}_to_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download complete fresh capital round-by-round analysis data"
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
                    
                    # Download option for detailed data
                    detailed_csv = results_df.to_csv()
                    st.download_button(
                        label="📊 Download Complete Fresh Capital Dataset",
                        data=detailed_csv,
                        file_name=f"fresh_capital_backtest_data_{etf_choice}_{leverage:.1f}x_{start_date}_to_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download all daily calculations for fresh capital strategy analysis"
                    )
    
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
        3. **2-Day Wait**: Same cooling-off period as liquidation-reentry mode
        4. **Fresh Capital**: Deploy NEW full position (unlimited money assumption)
        5. **Frequency Analysis**: Track how often margin calls occur
        
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
    
    
