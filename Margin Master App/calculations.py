import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_required_margin(investment_amount, leverage_percentage, margin_type="reg-t"):
    """
    Calculate required margin based on investment amount and leverage
    
    Args:
        investment_amount (float): Total investment amount
        leverage_percentage (float): Leverage as a percentage (e.g., 50 for 50%)
        margin_type (str): Type of margin calculation ('reg-t' or 'portfolio')
        
    Returns:
        float: Required margin amount
    """
    leverage_ratio = leverage_percentage / 100
    
    if margin_type.lower() == "reg-t":
        # Reg-T requires 50% initial margin
        initial_margin_requirement = 0.50
        required_margin = investment_amount * initial_margin_requirement / leverage_ratio
    elif margin_type.lower() == "portfolio":
        # Portfolio margin is typically 15-20% for broad market indices
        initial_margin_requirement = 0.20
        required_margin = investment_amount * initial_margin_requirement / leverage_ratio
    else:
        raise ValueError("Margin type must be either 'reg-t' or 'portfolio'")
    
    return round(required_margin, 2)

def calculate_buying_power(investment_amount, leverage_percentage):
    """
    Calculate buying power based on investment and leverage
    
    Args:
        investment_amount (float): Total investment amount
        leverage_percentage (float): Leverage as a percentage
        
    Returns:
        float: Buying power
    """
    leverage_ratio = leverage_percentage / 100
    buying_power = investment_amount / leverage_ratio
    return round(buying_power, 2)

def calculate_interest_accrual(investment_amount, leverage_percentage, interest_rate, days=365):
    """
    Calculate estimated interest accrual
    
    Args:
        investment_amount (float): Total investment amount
        leverage_percentage (float): Leverage as a percentage
        interest_rate (float): Annual interest rate percentage
        days (int): Number of days to calculate interest for
        
    Returns:
        float: Estimated interest accrual
    """
    leverage_ratio = leverage_percentage / 100
    borrowed_amount = investment_amount * (1 - 1/leverage_ratio) if leverage_ratio > 1 else 0
    daily_interest_rate = interest_rate / 100 / 365
    interest_accrual = borrowed_amount * daily_interest_rate * days
    return round(interest_accrual, 2)

def calculate_maintenance_cushion(investment_amount, leverage_percentage, maintenance_margin_percentage, current_price_percentage=100):
    """
    Calculate maintenance margin cushion
    
    Args:
        investment_amount (float): Total investment amount
        leverage_percentage (float): Leverage as a percentage
        maintenance_margin_percentage (float): Maintenance margin percentage
        current_price_percentage (float): Current price as a percentage of purchase price
        
    Returns:
        tuple: (cushion_amount, cushion_percentage)
    """
    leverage_ratio = leverage_percentage / 100
    maintenance_ratio = maintenance_margin_percentage / 100
    position_value = investment_amount * leverage_ratio * (current_price_percentage / 100)
    
    # If leveraged, calculate equity
    if leverage_ratio > 1:
        loan_amount = investment_amount * (1 - 1/leverage_ratio)
        equity = position_value - loan_amount
    else:
        equity = position_value
    
    maintenance_requirement = position_value * maintenance_ratio
    cushion_amount = equity - maintenance_requirement
    
    # Calculate as percentage of position value
    if position_value > 0:
        cushion_percentage = 100 * cushion_amount / position_value
    else:
        cushion_percentage = 0
    
    return round(cushion_amount, 2), round(cushion_percentage, 2)

def calculate_liquidation_price(investment_amount, leverage_percentage, maintenance_margin_percentage):
    """
    Calculate liquidation price as a percentage of purchase price
    
    Args:
        investment_amount (float): Total investment amount
        leverage_percentage (float): Leverage as a percentage
        maintenance_margin_percentage (float): Maintenance margin percentage
        
    Returns:
        float: Liquidation price as percentage of purchase price
    """
    leverage_ratio = leverage_percentage / 100
    maintenance_ratio = maintenance_margin_percentage / 100
    
    if leverage_ratio <= 1:  # No leverage means no liquidation
        return 0
    
    # Formula: liquidation happens when equity = maintenance requirement
    # equity = position_value - loan
    # position_value * maintenance_ratio = position_value - loan
    # position_value * (1 - maintenance_ratio) = loan
    # position_value = loan / (1 - maintenance_ratio)
    # liquidation_price_ratio = position_value / original_position_value
    
    loan_amount = investment_amount * (1 - 1/leverage_ratio)
    original_position_value = investment_amount * leverage_ratio
    
    if maintenance_ratio < 1:
        liquidation_position_value = loan_amount / (1 - maintenance_ratio)
        liquidation_price_ratio = liquidation_position_value / original_position_value
    else:
        # If maintenance ratio is 100% or more, any price drop would trigger
        liquidation_price_ratio = 0.99  # Almost immediate liquidation
    
    return round(liquidation_price_ratio * 100, 2)

def calculate_margin_data_for_chart(investment_amount, leverage_percentage, maintenance_margin_percentage, price_range=None):
    """
    Calculate margin data across a range of price scenarios for charting
    
    Args:
        investment_amount (float): Total investment amount
        leverage_percentage (float): Leverage as a percentage
        maintenance_margin_percentage (float): Maintenance margin percentage
        price_range (list): Optional list of price percentages to calculate for
        
    Returns:
        tuple: (prices, reg_t_equity, portfolio_equity, liquidation_points)
    """
    if price_range is None:
        price_range = np.linspace(70, 130, 100)  # Default 70% to 130% of price
    
    leverage_ratio = leverage_percentage / 100
    maintenance_ratio = maintenance_margin_percentage / 100
    base_position = investment_amount * leverage_ratio
    loan_amount = investment_amount * (1 - 1/leverage_ratio) if leverage_ratio > 1 else 0
    
    # Calculate data for both margin types
    reg_t_equity = []
    portfolio_equity = []
    prices = []
    
    # Calculate liquidation points
    reg_t_liquidation = calculate_liquidation_price(investment_amount, leverage_percentage, 25)  # Reg-T typically 25%
    portfolio_liquidation = calculate_liquidation_price(investment_amount, leverage_percentage, maintenance_margin_percentage)
    
    for price_pct in price_range:
        current_price_ratio = price_pct / 100
        position_value = base_position * current_price_ratio
        
        # Calculate equity
        equity = position_value - loan_amount
        
        # For Reg-T (typically fixed at 25% maintenance)
        reg_t_maintenance = position_value * 0.25
        reg_t_eq = max(0, equity)  # Can't go below zero
        
        # For Portfolio margin (uses the provided maintenance value)
        portfolio_maintenance = position_value * maintenance_ratio
        portfolio_eq = max(0, equity)  # Can't go below zero
        
        prices.append(price_pct)
        reg_t_equity.append(reg_t_eq)
        portfolio_equity.append(portfolio_eq)
    
    liquidation_points = {
        'reg_t': reg_t_liquidation,
        'portfolio': portfolio_liquidation
    }
    
    return prices, reg_t_equity, portfolio_equity, liquidation_points

def get_stress_test_scenario(scenario_name):
    """
    Get predefined stress test scenarios
    
    Args:
        scenario_name (str): Name of the scenario ('2020_crash', '2022_bear', or custom date)
        
    Returns:
        dict: Scenario details including price changes
    """
    scenarios = {
        '2020_crash': {
            'name': 'COVID-19 Crash (2020)',
            'description': 'Feb 19 - Mar 23, 2020: SPY dropped ~34%',
            'price_changes': [0, -5, -10, -15, -20, -25, -30, -34],
            'timeframe_days': 33
        },
        '2022_bear': {
            'name': '2022 Bear Market',
            'description': 'Jan 3 - Oct 12, 2022: SPY dropped ~25%',
            'price_changes': [0, -5, -10, -15, -20, -25],
            'timeframe_days': 282
        }
    }
    
    if scenario_name in scenarios:
        return scenarios[scenario_name]
    else:
        # Return a default scenario for custom date
        return {
            'name': 'Custom Scenario',
            'description': 'Custom date range analysis',
            'price_changes': [0, -5, -10, -15, -20],
            'timeframe_days': 30
        } 