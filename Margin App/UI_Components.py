import streamlit as st

# Professional Bloomberg Terminal-inspired CSS
def load_css():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
        
        /* Bloomberg Terminal Dark Theme */
        :root {
            --bg-primary: #000000;
            --bg-secondary: #0a0a0a;
            --bg-tertiary: #141414;
            --bg-card: #1a1a1a;
            --bg-hover: #242424;
            
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --text-muted: #666666;
            
            --accent-orange: #ff8c00;
            --accent-amber: #ffa500;
            --positive-green: #00ff00;
            --negative-red: #ff0000;
            --warning-yellow: #ffff00;
            --info-blue: #00a2ff;
            
            --border-color: #333333;
            --border-light: #404040;
        }
        
        /* Global Dark Background */
        .stApp {
            background-color: var(--bg-primary);
            color: var(--text-primary);
        }
        
        /* Main container */
        .main .block-container {
            padding: 1rem 2rem;
            max-width: 1920px;
            background-color: var(--bg-primary);
        }
        
        /* Typography - Bloomberg style */
        * {
            font-family: 'IBM Plex Mono', 'Consolas', 'Monaco', monospace !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: var(--accent-orange);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 1rem;
        }
        
        h1 {
            font-size: 1.5rem;
            border-bottom: 2px solid var(--accent-orange);
            padding-bottom: 0.5rem;
        }
        
        h2 {
            font-size: 1.25rem;
            color: var(--accent-amber);
        }
        
        h3 {
            font-size: 1.1rem;
            color: var(--text-primary);
        }
        
        p, div, span, li {
            color: var(--text-primary);
            line-height: 1.5;
        }
        
        /* Remove all Streamlit default styling */
        .css-1d391kg, .css-1dp5vir, .css-1cpxqw2 {
            background-color: var(--bg-primary) !important;
        }
        
        /* Professional Card Styling */
        .terminal-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0;
            padding: 1rem;
            margin: 0.5rem 0;
            font-family: 'IBM Plex Mono', monospace;
        }
        
        .terminal-card:hover {
            background-color: var(--bg-hover);
            border-color: var(--accent-orange);
        }
        
        /* Data Display Terminal Style */
        .data-grid {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 0.5rem;
            padding: 0.5rem;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
        }
        
        .data-label {
            color: var(--text-secondary);
            text-transform: uppercase;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .data-value {
            color: var(--text-primary);
            font-weight: 600;
            text-align: right;
        }
        
        .data-value.positive {
            color: var(--positive-green);
        }
        
        .data-value.negative {
            color: var(--negative-red);
        }
        
        /* Terminal-style tabs */
        div[role="radiogroup"] {
            background-color: var(--bg-secondary) !important;
            padding: 0.5rem !important;
            border: 1px solid var(--border-color) !important;
            display: flex !important;
            gap: 0 !important;
        }
        
        div[role="radiogroup"] > label {
            background-color: var(--bg-tertiary) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 0 !important;
            padding: 0.75rem 1.5rem !important;
            margin: 0 !important;
            transition: all 0.2s ease !important;
            color: var(--text-secondary) !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        div[role="radiogroup"] > label:hover {
            background-color: var(--bg-hover) !important;
            color: var(--accent-orange) !important;
            border-color: var(--accent-orange) !important;
        }
        
        div[role="radiogroup"] > label[data-checked="true"] {
            background-color: var(--accent-orange) !important;
            color: var(--bg-primary) !important;
            border-color: var(--accent-orange) !important;
            font-weight: 700 !important;
        }
        
        /* Professional Buttons */
        .stButton > button {
            background-color: var(--bg-tertiary) !important;
            color: var(--accent-orange) !important;
            border: 1px solid var(--accent-orange) !important;
            border-radius: 0 !important;
            padding: 0.5rem 1.5rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            transition: all 0.2s !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        .stButton > button:hover {
            background-color: var(--accent-orange) !important;
            color: var(--bg-primary) !important;
            box-shadow: 0 0 10px rgba(255, 140, 0, 0.5) !important;
        }
        
        .stButton > button:focus {
            background-color: var(--accent-orange) !important;
            color: var(--bg-primary) !important;
            outline: none !important;
        }
        
        .stButton > button:active {
            background-color: var(--accent-amber) !important;
            color: var(--bg-primary) !important;
        }
        
        /* Input fields - White background with BOLD BLACK text for readability */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select,
        .stDateInput > div > div > input,
        .stSlider > div > div > div > div,
        .stSlider input,
        input[type="text"],
        input[type="number"],
        input[type="date"],
        select,
        textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #cccccc !important;
            border-radius: 0 !important;
            font-family: 'IBM Plex Mono', monospace !important;
            padding: 0.5rem !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stDateInput > div > div > input:focus,
        .stSlider > div > div > div > div:focus,
        input[type="text"]:focus,
        input[type="number"]:focus,
        input[type="date"]:focus,
        select:focus,
        textarea:focus {
            border-color: var(--accent-orange) !important;
            box-shadow: 0 0 5px rgba(255, 140, 0, 0.3) !important;
            font-weight: 700 !important;
        }
        
        /* Dropdown options - BOLD BLACK text */
        .stSelectbox option,
        select option {
            background-color: #ffffff !important;
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Force selectbox text to be BOLD BLACK */
        .stSelectbox > div > div > div,
        .stSelectbox > div > div > div > div,
        .stSelectbox span,
        .stSelectbox div[data-baseweb="select"] > div,
        .stSelectbox div[data-baseweb="select"] span {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Target the actual displayed text in selectbox */
        .stSelectbox > div > div > div[data-baseweb="select"] > div > div {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Comprehensive selectbox text targeting - BOLD BLACK nuclear option */
        [data-baseweb="select"] *,
        .stSelectbox *,
        div[data-testid="stSelectbox"] *,
        div[role="combobox"] *,
        div[role="listbox"] * {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Ensure dropdown arrow and container are styled properly */
        .stSelectbox > div > div {
            background-color: #ffffff !important;
        }
        
        /* Force any remaining gray text to BOLD BLACK */
        .stSelectbox div[style*="color"],
        .stSelectbox span[style*="color"] {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Number input increment/decrement buttons - BOLD STYLING */
        .stNumberInput button {
            background-color: #f0f0f0 !important;
            color: #000000 !important;
            border: 1px solid #cccccc !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        .stNumberInput button:hover {
            background-color: #e0e0e0 !important;
            color: #000000 !important;
            font-weight: 700 !important;
        }
        
        /* Ensure number input buttons show + and - clearly with BOLD text */
        .stNumberInput button span {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Slider styling - BOLD BLACK text */
        .stSlider > div > div > div > div {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        .stSlider label {
            color: var(--accent-orange) !important;
            font-weight: 700 !important;
        }
        
        /* Radio button text - BOLD BLACK */
        .stRadio > div > label > div > div {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Checkbox text - BOLD BLACK */
        .stCheckbox > label > div > div {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Text area - BOLD BLACK */
        .stTextArea > div > div > textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
            border: 1px solid #cccccc !important;
        }
        
        /* COMPREHENSIVE INPUT STYLING - Catch all form elements */
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] div,
        div[data-testid="stSlider"] div,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stRadio"] div,
        div[data-testid="stCheckbox"] div {
            color: #000000 !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
        }
        
        /* Input labels should remain orange but bold */
        .stTextInput > label,
        .stNumberInput > label,
        .stSelectbox > label,
        .stDateInput > label,
        .stSlider > label,
        .stTextArea > label,
        .stRadio > label,
        .stCheckbox > label {
            color: var(--accent-orange) !important;
            font-weight: 700 !important;
            font-family: 'IBM Plex Mono', monospace !important;
            text-transform: uppercase !important;
        }
        
        /* Metrics - Bloomberg style */
        [data-testid="metric-container"] {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 0;
            padding: 1rem;
        }
        
        [data-testid="metric-container"] [data-testid="metric-label"] {
            color: var(--text-secondary);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        [data-testid="metric-container"] [data-testid="metric-value"] {
            color: var(--accent-amber);
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        [data-testid="metric-container"] [data-testid="metric-delta"] {
            font-size: 0.9rem;
        }
        
        /* Tables - Terminal style */
        .dataframe {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            font-size: 0.85rem;
        }
        
        .dataframe thead tr th {
            background-color: var(--bg-tertiary);
            color: var(--accent-orange);
            font-weight: 600;
            text-transform: uppercase;
            border-bottom: 2px solid var(--accent-orange);
            padding: 0.5rem;
            text-align: left;
        }
        
        .dataframe tbody tr {
            border-bottom: 1px solid var(--border-color);
        }
        
        .dataframe tbody tr:hover {
            background-color: var(--bg-hover);
        }
        
        .dataframe tbody tr td {
            padding: 0.5rem;
            font-family: 'IBM Plex Mono', monospace;
        }
        
        /* Plotly charts dark theme */
        .js-plotly-plot {
            background-color: var(--bg-secondary) !important;
        }
        
        /* Expander - Terminal style */
        .streamlit-expanderHeader {
            background-color: var(--bg-tertiary) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 0 !important;
            color: var(--text-primary) !important;
        }
        
        .streamlit-expanderHeader:hover {
            border-color: var(--accent-orange) !important;
            color: var(--accent-orange) !important;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
        }
        
        /* Alert boxes - Terminal style */
        .stAlert {
            background-color: var(--bg-card);
            border-radius: 0;
            border-left: 4px solid var(--accent-orange);
            color: var(--text-primary);
        }
        
        .stAlert[data-baseweb="notification"][kind="info"] {
            border-left-color: var(--info-blue);
        }
        
        .stAlert[data-baseweb="notification"][kind="warning"] {
            border-left-color: var(--warning-yellow);
        }
        
        .stAlert[data-baseweb="notification"][kind="error"] {
            border-left-color: var(--negative-red);
        }
        
        .stAlert[data-baseweb="notification"][kind="success"] {
            border-left-color: var(--positive-green);
        }
        
        /* Progress bars */
        .stProgress > div > div > div {
            background-color: var(--accent-orange);
        }
        
        /* Sliders */
        .st-emotion-cache-1inwz65 {
            background-color: var(--bg-secondary) !important;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 0;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-orange);
        }
        
        /* Data terminal header */
        .terminal-header {
            background-color: var(--bg-secondary);
            border: 1px solid var(--accent-orange);
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .terminal-title {
            color: var(--accent-orange);
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: 2px;
            margin: 0;
        }
        
        .terminal-subtitle {
            color: var(--text-secondary);
            font-size: 0.9rem;
            letter-spacing: 1px;
            margin: 0.5rem 0 0 0;
        }
        
        /* Grid layout for metrics */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .metric-box {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 1rem;
            text-align: center;
        }
        
        .metric-label {
            color: var(--text-secondary);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            color: var(--accent-amber);
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        .metric-delta {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 0.25rem;
        }
        
        .metric-delta.positive {
            color: var(--positive-green);
        }
        
        .metric-delta.negative {
            color: var(--negative-red);
        }
        
        /* Backtest mode selection buttons - ensure visibility */
        [data-testid="stHorizontalBlock"] button,
        div[data-testid="column"] button {
            background-color: #1a1a1a !important;
            color: #ff8c00 !important;
            border: 2px solid #ff8c00 !important;
        }
        
        [data-testid="stHorizontalBlock"] button:hover,
        div[data-testid="column"] button:hover {
            background-color: #ff8c00 !important;
            color: #000000 !important;
        }
        
        /* Selected/active button state */
        [data-testid="stHorizontalBlock"] button[data-active="true"],
        div[data-testid="column"] button[data-active="true"] {
            background-color: #ff8c00 !important;
            color: #000000 !important;
            font-weight: 700 !important;
        }
        
        /* Fix any white text issues */
        button span {
            color: inherit !important;
        }
        
        /* Tooltip/help text styling - comprehensive coverage */
        div[data-baseweb="tooltip"],
        div[data-baseweb="tooltip"] > div,
        .st-emotion-cache-1gulkj5,
        [data-testid="tooltipHoverTarget"] + div,
        [role="tooltip"],
        div[data-testid="stTooltipContent"] {
            background-color: var(--accent-orange) !important;
            border: 1px solid var(--accent-amber) !important;
        }
        
        div[data-baseweb="tooltip"] div,
        div[data-baseweb="tooltip"] span,
        div[data-baseweb="tooltip"] p,
        [role="tooltip"] div,
        [role="tooltip"] span,
        [role="tooltip"] p,
        [data-testid="stTooltipContent"] div,
        [data-testid="stTooltipContent"] span,
        [data-testid="stTooltipContent"] p {
            color: var(--bg-primary) !important;
            font-weight: 600 !important;
        }
        
        /* Streamlit tooltip styling - all possible classes */
        [class*="tooltip"],
        [class*="Tooltip"] {
            background-color: var(--accent-orange) !important;
            color: var(--bg-primary) !important;
            border: 1px solid var(--accent-amber) !important;
        }
        
        [class*="tooltip"] *,
        [class*="Tooltip"] * {
            color: var(--bg-primary) !important;
        }
        
        /* Help icon styling */
        [data-testid="stTooltipIcon"],
        [data-testid="tooltipHoverTarget"] {
            color: var(--accent-orange) !important;
        }
        
        /* Popover/popup styling */
        [data-testid="stPopover"],
        .st-emotion-cache-1n76uvr,
        .st-emotion-cache-1n76uvr * {
            background-color: var(--accent-orange) !important;
            color: var(--bg-primary) !important;
        }
        
        /* Spinner styling */
        .stSpinner > div {
            color: var(--accent-orange) !important;
            font-family: 'IBM Plex Mono', monospace !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
        }
        
        .stSpinner svg {
            fill: var(--accent-orange) !important;
        }
        
        /* Force tooltip text to be visible - nuclear option */
        div[style*="position: absolute"][style*="z-index"] {
            background-color: var(--accent-orange) !important;
        }
        
        div[style*="position: absolute"][style*="z-index"] * {
            color: var(--bg-primary) !important;
        }
        
        /* Global tooltip override - last resort */
        body [role="tooltip"],
        body [data-baseweb="tooltip"],
        body .tooltipContainer,
        body .tooltip-text,
        body [class*="tooltip"]:not(button):not(div[data-testid="column"]) {
            background-color: #ff8c00 !important;
            color: #000000 !important;
            border: 2px solid #ffa500 !important;
            font-weight: 700 !important;
        }
        
        body [role="tooltip"] *,
        body [data-baseweb="tooltip"] *,
        body .tooltipContainer *,
        body .tooltip-text *,
        body [class*="tooltip"]:not(button):not(div[data-testid="column"]) * {
            color: #000000 !important;
        }
        
        /* Remove rounded corners everywhere */
        * {
            border-radius: 0 !important;
        }
        
        /* Calendar / Date Picker Styling - Make text readable across all apps */
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
    """

# Professional terminal-style header
def app_header():
    return """
    <div class="terminal-header">
        <div class="terminal-title">PEARSON CREEK CAPITAL MANAGEMENT LLC</div>
        <div class="terminal-title">MARGIN ANALYTICS TERMINAL</div>
        <div class="terminal-subtitle">PROFESSIONAL TRADING ANALYSIS PLATFORM</div>
    </div>
    """

# Remove all other emoji-heavy functions and replace with clean, professional versions
def date_range_explanation():
    return """
    <div class="terminal-card">
        <div class="data-label">DATE RANGE SELECTION</div>
        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            SELECT TIME PERIOD FOR ANALYSIS. HISTORICAL DATA AVAILABLE FROM 2000-PRESENT.
        </div>
    </div>
    """

def market_overview_explanation():
    return """
    <div class="terminal-card">
        <div class="data-label">MARKET OVERVIEW</div>
        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            COMPREHENSIVE ETF PERFORMANCE METRICS. COMPARING S&P 500 (SPY) AND TOTAL MARKET (VTI) INDICES.
        </div>
    </div>
    """

def price_analysis_explanation():
    return """
    <div class="terminal-card">
        <div class="data-label">PRICE ANALYSIS</div>
        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            CANDLESTICK CHARTS DISPLAY OHLC DATA. GREEN: BULLISH CLOSE. RED: BEARISH CLOSE.
        </div>
    </div>
    """

def dividend_analysis_explanation():
    return """
    <div class="terminal-card">
        <div class="data-label">DIVIDEND ANALYSIS</div>
        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            QUARTERLY DIVIDEND DISTRIBUTION PATTERNS. ANALYZE INCOME POTENTIAL AND SEASONAL TRENDS.
        </div>
    </div>
    """

def margin_calculator_explanation():
    return """
    <div class="terminal-card" style="border-color: var(--warning-yellow);">
        <div class="data-label" style="color: var(--warning-yellow);">MARGIN CALCULATOR</div>
        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            CALCULATE LEVERAGE POSITIONS AND MARGIN REQUIREMENTS. WARNING: MARGIN TRADING INVOLVES SIGNIFICANT RISK.
        </div>
    </div>
    """

def kelly_criterion_explanation():
    return """
    <div class="terminal-card" style="border-color: var(--info-blue);">
        <div class="data-label" style="color: var(--info-blue);">KELLY CRITERION</div>
        <div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.5rem;">
            OPTIMAL POSITION SIZING CALCULATOR. KELLY CRITERION DETERMINES THE IDEAL PERCENTAGE OF CAPITAL TO ALLOCATE TO MAXIMIZE LONG-TERM GROWTH WHILE MINIMIZING RISK OF RUIN.
        </div>
    </div>
    """

def app_footer():
    import datetime
    return f"""
    <div style="border-top: 1px solid var(--border-color); margin-top: 2rem; padding-top: 1rem; text-align: center;">
        <div style="color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase;">
            MARGIN ANALYTICS TERMINAL | DATA: YAHOO FINANCE | {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
    """ 
    
def pearson_creek_header():
    """Not used in professional theme"""
    return ""
    
    
    