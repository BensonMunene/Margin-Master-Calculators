import pandas as pd
import streamlit as st
import json
import base64
import datetime
import io

def get_session_state_key():
    """
    Generate a unique key for storing session state based on the date
    
    Returns:
        str: Unique key
    """
    today = datetime.date.today().strftime('%Y-%m-%d')
    return f"margin_master_{today}"

def save_scenario_to_local_storage(investment_amount, leverage_percentage, interest_rate, 
                                  maintenance_margin_percentage, purchase_date=None):
    """
    Save current scenario settings to session state
    
    Args:
        investment_amount (float): Investment amount
        leverage_percentage (float): Leverage percentage
        interest_rate (float): Interest rate percentage
        maintenance_margin_percentage (float): Maintenance margin percentage
        purchase_date (datetime.date, optional): Date of purchase
        
    Returns:
        dict: Saved scenario data
    """
    scenario_data = {
        "investment_amount": investment_amount,
        "leverage_percentage": leverage_percentage,
        "interest_rate": interest_rate,
        "maintenance_margin_percentage": maintenance_margin_percentage,
        "purchase_date": purchase_date.strftime('%Y-%m-%d') if purchase_date else None,
        "saved_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Get current saved scenarios or initialize empty list
    if "saved_scenarios" not in st.session_state:
        st.session_state.saved_scenarios = []
    
    # Add current scenario
    st.session_state.saved_scenarios.append(scenario_data)
    
    # Keep only last 10 scenarios
    if len(st.session_state.saved_scenarios) > 10:
        st.session_state.saved_scenarios = st.session_state.saved_scenarios[-10:]
    
    return scenario_data

def load_saved_scenarios():
    """
    Load saved scenarios from session state
    
    Returns:
        list: List of saved scenarios
    """
    if "saved_scenarios" not in st.session_state:
        st.session_state.saved_scenarios = []
    
    return st.session_state.saved_scenarios

def export_to_csv(data_dict):
    """
    Export calculation data to CSV
    
    Args:
        data_dict (dict): Dictionary containing calculation data
        
    Returns:
        str: Base64 encoded CSV data for download
    """
    # Create DataFrame from dictionary
    df = pd.DataFrame(data_dict)
    
    # Convert to CSV
    csv = df.to_csv(index=False)
    
    # Encode to base64 for download
    b64 = base64.b64encode(csv.encode()).decode()
    
    return b64

def generate_report_for_export(investment_amount, leverage_percentage, interest_rate, 
                              maintenance_margin_percentage, results):
    """
    Generate a report dictionary for exporting to CSV
    
    Args:
        investment_amount (float): Investment amount
        leverage_percentage (float): Leverage percentage
        interest_rate (float): Interest rate percentage
        maintenance_margin_percentage (float): Maintenance margin percentage
        results (dict): Calculation results
        
    Returns:
        dict: Report data ready for CSV export
    """
    # Create header information
    report_data = {
        "Timestamp": [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        "Investment Amount": [f"${investment_amount:,.2f}"],
        "Leverage": [f"{leverage_percentage}%"],
        "Interest Rate": [f"{interest_rate}%"],
        "Maintenance Margin": [f"{maintenance_margin_percentage}%"]
    }
    
    # Add calculation results
    for key, value in results.items():
        if isinstance(value, (int, float)):
            report_data[key] = [f"${value:,.2f}" if key != "Liquidation Price" else f"{value}%"]
        else:
            report_data[key] = [str(value)]
    
    return report_data

def init_default_settings():
    """
    Initialize default app settings in session state
    
    Returns:
        dict: Default settings
    """
    if "app_settings" not in st.session_state:
        st.session_state.app_settings = {
            "theme": "light",
            "data_source": "local",
            "notifications_enabled": False,
            "email": "",
            "phone": ""
        }
    
    return st.session_state.app_settings

def save_settings(settings_dict):
    """
    Save settings to session state
    
    Args:
        settings_dict (dict): Dictionary of settings
        
    Returns:
        dict: Updated settings
    """
    st.session_state.app_settings = settings_dict
    return st.session_state.app_settings 