import streamlit as st
import base64
from PIL import Image
import matplotlib.pyplot as plt
import io
import numpy as np

def set_page_config():
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="Margin Master App",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

def apply_custom_css():
    """Apply custom CSS to enhance the app appearance."""
    st.markdown("""
    <style>
    .main {
        padding-top: 0;
    }
    .stApp {
        background-color: #f5f7fa;
    }
    .section-header {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        color: #1f4e79;
    }
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .highlight-card {
        border-left: 5px solid #1f77b4;
    }
    .warning-card {
        border-left: 5px solid #ff9800;
    }
    .danger-card {
        border-left: 5px solid #e74c3c;
    }
    .metric-label {
        font-size: 14px;
        color: #555;
        font-weight: 500;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f4e79;
    }
    .calculator-section {
        background-color: #e8f1f8;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 30px;
    }
    .settings-section {
        background-color: #f0f5ea;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 30px;
    }
    .sticky-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: rgba(245, 247, 250, 0.9);
        backdrop-filter: blur(5px);
        padding: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    .btn-preset {
        background-color: #1f4e79;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px 15px;
        cursor: pointer;
        margin-right: 10px;
        font-size: 14px;
    }
    .btn-preset:hover {
        background-color: #173d5f;
    }
    </style>
    """, unsafe_allow_html=True)

def generate_banner():
    """Generate an AI-style banner for the app header."""
    fig, ax = plt.subplots(figsize=(12, 2))
    ax.set_facecolor("#1f4e79")
    
    # Generate a gradient background
    x = np.linspace(0, 1, 100)
    y = np.linspace(0, 1, 100)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X*10) * np.cos(Y*10) * 0.2 + 0.8
    
    ax.imshow(Z, cmap='Blues', extent=[0, 1, 0, 1], alpha=0.7)
    ax.text(0.5, 0.5, "MARGIN MASTER", 
            fontsize=30, color='white', ha='center', va='center', 
            fontweight='bold', family='monospace')
    
    # Remove all axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Save the figure to a BytesIO object
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    plt.close(fig)
    
    # Convert to base64 for HTML embedding
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_str}"

def render_header():
    """Render the app header with banner and global controls."""
    banner_url = generate_banner()
    
    st.markdown(f"""
    <div class="sticky-header">
        <img src="{banner_url}" style="width:100%; height:auto; max-height:100px; object-fit:cover; border-radius:5px;">
        <div style="padding: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.date_input("Analysis Date", value=None, key="global_date")
    with col2:
        st.selectbox("ETF Type", options=["SPY", "QQQ", "DIA", "IWM"], key="global_etf")

def render_summary_card(title, value, description=None, card_type="highlight"):
    """Render a summary metric card."""
    st.markdown(f"""
    <div class="card {card_type}-card">
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
        {f'<div style="font-size:12px; color:#777;">{description}</div>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title):
    """Render a section header with styling."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

def render_separator():
    """Render a visual separator between sections."""
    st.markdown("""<hr style="height:2px; border:none; background-color:#ddd; margin:40px 0;">""", unsafe_allow_html=True)

def get_dummy_data():
    """Generate dummy data for initial app rendering."""
    price_range = np.linspace(0.7, 1.3, 100)
    base_price = 100
    prices = base_price * price_range
    
    # Generate dummy data for Reg-T margin
    reg_t_equity = []
    for p in price_range:
        if p < 0.8:  # Margin call territory
            eq = base_price * (2*p - 0.6)  # Simplified formula
        else:
            eq = base_price * (2*p - 0.8)
        reg_t_equity.append(max(0, eq))
    
    # Generate dummy data for Portfolio margin
    portfolio_equity = []
    for p in price_range:
        if p < 0.85:  # Margin call territory
            eq = base_price * (1.5*p - 0.275)  # Different formula
        else:
            eq = base_price * (1.5*p - 0.2)
        portfolio_equity.append(max(0, eq))
    
    return prices, reg_t_equity, portfolio_equity 