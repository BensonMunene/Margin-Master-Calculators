import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
from datetime import date

# Import custom modules
import ui
import calculations
import charts
import utils

# Set page configuration
ui.set_page_config()
ui.apply_custom_css()

# Initialize session state for settings
settings = utils.init_default_settings()

# Render the header section
ui.render_header()

# Main application logic
def main():
    # Main content container
    with st.container():
        # ------------------------
        # Margin Calculator Section
        # ------------------------
        st.markdown('<div class="calculator-section">', unsafe_allow_html=True)
        ui.render_section_header("Margin Calculator")
        
        # Input form
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # Input form in a card-like container
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # Investment amount input
            investment_amount = st.number_input(
                "Investment Amount ($)",
                min_value=1000.0,
                max_value=10000000.0,
                value=100000.0,
                step=1000.0,
                format="%.2f"
            )
            
            # Leverage percentage with slider and numeric input
            leverage_col1, leverage_col2 = st.columns([3, 2])
            with leverage_col1:
                leverage_percentage = st.slider(
                    "Leverage %",
                    min_value=0.0,
                    max_value=200.0,
                    value=50.0,
                    step=5.0
                )
            with leverage_col2:
                leverage_percentage = st.number_input(
                    "Leverage Value",
                    min_value=0.0,
                    max_value=200.0,
                    value=leverage_percentage,
                    step=1.0,
                    label_visibility="collapsed"
                )
            
            # Interest rate
            interest_rate = st.number_input(
                "Interest Rate (Annual %)",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.1,
                format="%.2f"
            )
            
            # Maintenance margin
            maintenance_margin_percentage = st.number_input(
                "Maintenance Margin %",
                min_value=0.0,
                max_value=100.0,
                value=25.0,
                step=5.0
            )
            
            # Date of purchase
            purchase_date = st.date_input(
                "Date of Purchase",
                value=date.today(),
                max_value=date.today()
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Save & Export buttons
            saved_btn_col, export_btn_col = st.columns(2)
            with saved_btn_col:
                if st.button("Save Scenario", use_container_width=True):
                    utils.save_scenario_to_local_storage(
                        investment_amount,
                        leverage_percentage,
                        interest_rate,
                        maintenance_margin_percentage,
                        purchase_date
                    )
                    st.success("Scenario saved!")
            
            with export_btn_col:
                # Calculate necessary values for export
                required_margin_reg_t = calculations.calculate_required_margin(
                    investment_amount, leverage_percentage, "reg-t"
                )
                required_margin_portfolio = calculations.calculate_required_margin(
                    investment_amount, leverage_percentage, "portfolio"
                )
                buying_power = calculations.calculate_buying_power(
                    investment_amount, leverage_percentage
                )
                interest_accrual = calculations.calculate_interest_accrual(
                    investment_amount, leverage_percentage, interest_rate
                )
                cushion_amount, cushion_percentage = calculations.calculate_maintenance_cushion(
                    investment_amount, leverage_percentage, maintenance_margin_percentage
                )
                liquidation_price = calculations.calculate_liquidation_price(
                    investment_amount, leverage_percentage, maintenance_margin_percentage
                )
                
                # Generate report
                export_data = utils.generate_report_for_export(
                    investment_amount,
                    leverage_percentage,
                    interest_rate,
                    maintenance_margin_percentage,
                    {
                        "Required Margin (Reg-T)": required_margin_reg_t,
                        "Required Margin (Portfolio)": required_margin_portfolio,
                        "Buying Power": buying_power,
                        "Interest Accrual (Annual)": interest_accrual,
                        "Maintenance Cushion": cushion_amount,
                        "Cushion Percentage": cushion_percentage,
                        "Liquidation Price": liquidation_price
                    }
                )
                
                # Generate download link
                csv = utils.export_to_csv(export_data)
                href = f'<a href="data:file/csv;base64,{csv}" download="margin_calculations.csv" class="btn-preset" style="text-decoration:none;padding:8px 15px;background-color:#1f4e79;color:white;border-radius:5px;display:block;text-align:center;">Export CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            
        with col2:
            # Calculate metrics for summary cards
            required_margin_reg_t = calculations.calculate_required_margin(
                investment_amount, leverage_percentage, "reg-t"
            )
            required_margin_portfolio = calculations.calculate_required_margin(
                investment_amount, leverage_percentage, "portfolio"
            )
            buying_power = calculations.calculate_buying_power(
                investment_amount, leverage_percentage
            )
            interest_accrual = calculations.calculate_interest_accrual(
                investment_amount, leverage_percentage, interest_rate
            )
            cushion_amount, cushion_percentage = calculations.calculate_maintenance_cushion(
                investment_amount, leverage_percentage, maintenance_margin_percentage
            )
            liquidation_price = calculations.calculate_liquidation_price(
                investment_amount, leverage_percentage, maintenance_margin_percentage
            )
            
            # Summary cards in a grid
            metric_cols = st.columns(2)
            
            with metric_cols[0]:
                st.markdown(f"""
                <div class="card highlight-card">
                    <div class="metric-label">Required Margin (Reg-T)</div>
                    <div class="metric-value">${required_margin_reg_t:,.2f}</div>
                    <div style="font-size:12px; color:#777;">Based on 50% initial requirement</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="card highlight-card">
                    <div class="metric-label">Buying Power</div>
                    <div class="metric-value">${buying_power:,.2f}</div>
                    <div style="font-size:12px; color:#777;">Total position value possible</div>
                </div>
                """, unsafe_allow_html=True)
                
                card_type = "danger-card" if cushion_percentage < 0 else ("warning-card" if cushion_percentage < 10 else "highlight-card")
                st.markdown(f"""
                <div class="card {card_type}">
                    <div class="metric-label">Maintenance Cushion</div>
                    <div class="metric-value">${cushion_amount:,.2f}</div>
                    <div style="font-size:12px; color:#777;">{cushion_percentage:.2f}% above requirement</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_cols[1]:
                st.markdown(f"""
                <div class="card highlight-card">
                    <div class="metric-label">Required Margin (Portfolio)</div>
                    <div class="metric-value">${required_margin_portfolio:,.2f}</div>
                    <div style="font-size:12px; color:#777;">Based on 20% initial requirement</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="card highlight-card">
                    <div class="metric-label">Interest Accrual (Annual)</div>
                    <div class="metric-value">${interest_accrual:,.2f}</div>
                    <div style="font-size:12px; color:#777;">At {interest_rate:.2f}% APR</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="card highlight-card">
                    <div class="metric-label">Liquidation Price</div>
                    <div class="metric-value">{liquidation_price:.2f}%</div>
                    <div style="font-size:12px; color:#777;">Percentage of purchase price</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Danger-Zone Gauge
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            gauge_fig = charts.create_danger_zone_gauge(cushion_percentage)
            st.plotly_chart(gauge_fig, use_container_width=True)
        
        # What-If Chart
        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        prices, reg_t_equity, portfolio_equity, liquidation_points = calculations.calculate_margin_data_for_chart(
            investment_amount, leverage_percentage, maintenance_margin_percentage
        )
        what_if_chart = charts.create_margin_what_if_chart(
            prices, reg_t_equity, portfolio_equity, liquidation_points, investment_amount
        )
        st.plotly_chart(what_if_chart, use_container_width=True)
        
        # Stress-Test Presets
        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        stress_col1, stress_col2, stress_col3, _ = st.columns([1, 1, 1, 2])
        
        # Track current active scenario in session state
        if 'active_scenario' not in st.session_state:
            st.session_state.active_scenario = None
        
        with stress_col1:
            if st.button("2020 Crash", use_container_width=True):
                st.session_state.active_scenario = "2020_crash"
        
        with stress_col2:
            if st.button("2022 Bear", use_container_width=True):
                st.session_state.active_scenario = "2022_bear"
        
        with stress_col3:
            if st.button("Custom Date...", use_container_width=True):
                st.session_state.active_scenario = "custom"
        
        # Show stress test chart if a scenario is selected
        if st.session_state.active_scenario:
            scenario = calculations.get_stress_test_scenario(st.session_state.active_scenario)
            stress_chart = charts.create_stress_test_chart(
                scenario, investment_amount, leverage_percentage, maintenance_margin_percentage
            )
            st.plotly_chart(stress_chart, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Separator
        ui.render_separator()
        
        # ------------------------
        # Settings & Theming Section
        # ------------------------
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)
        ui.render_section_header("Settings & Theming")
        
        settings_col1, settings_col2 = st.columns(2)
        
        with settings_col1:
            # Theme selection
            theme = st.selectbox(
                "Theme",
                options=["Light", "Dark"],
                index=0 if settings["theme"].lower() == "light" else 1
            )
            settings["theme"] = theme.lower()
            
            # Data source selection
            data_source = st.selectbox(
                "Data Source",
                options=["Local CSV", "Live API"],
                index=0 if settings["data_source"].lower() == "local" else 1
            )
            settings["data_source"] = "local" if data_source == "Local CSV" else "api"
        
        with settings_col2:
            # Notification settings
            notifications_enabled = st.checkbox(
                "Enable Margin Call Notifications",
                value=settings["notifications_enabled"]
            )
            settings["notifications_enabled"] = notifications_enabled
            
            if notifications_enabled:
                email = st.text_input("Email for Notifications", value=settings["email"])
                settings["email"] = email
                
                phone = st.text_input("Phone for SMS Notifications", value=settings["phone"])
                settings["phone"] = phone
        
        # Apply settings button
        if st.button("Save Settings", use_container_width=False):
            utils.save_settings(settings)
            st.success("Settings saved!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="text-align:center; margin-top:30px; color:#777; font-size:12px;">
            Margin Master App v1.0 | Created with Streamlit | Calculations are for educational purposes only
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    