import streamlit as st

# Professional Bloomberg Terminal-style CSS
def load_css():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* CSS Variables for Professional Theme */
        :root {
            --bg-primary: #0a0b0d;
            --bg-secondary: #1a1d21;
            --bg-tertiary: #242831;
            --bg-card: #1e2329;
            --bg-surface: #2b2f36;
            
            --text-primary: #ffffff;
            --text-secondary: #b7bdc8;
            --text-muted: #6c7293;
            --text-accent: #f7931a;
            
            --border-primary: #2b2f36;
            --border-secondary: #404853;
            --border-accent: #f7931a;
            
            --green-primary: #00d4aa;
            --green-secondary: #00b894;
            --red-primary: #ff6b6b;
            --red-secondary: #ee5a52;
            --blue-primary: #74b9ff;
            --blue-secondary: #0984e3;
            --orange-primary: #f7931a;
            --orange-secondary: #e17055;
            
            --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-dark: linear-gradient(135deg, #1e2329 0%, #242831 100%);
            --gradient-accent: linear-gradient(135deg, #f7931a 0%, #e17055 100%);
            
            --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.5);
            --shadow-xl: 0 16px 32px rgba(0, 0, 0, 0.6);
            
            --border-radius-sm: 4px;
            --border-radius-md: 8px;
            --border-radius-lg: 12px;
            --border-radius-xl: 16px;
            
            --transition-fast: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-normal: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Global Overrides */
        .main .block-container {
            padding: 0 !important;
            max-width: 100% !important;
            background: var(--bg-primary);
        }
        
        .stApp {
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        
        .stApp > header {
            background: transparent;
        }
        
        /* Hide Streamlit components */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Typography System */
        .typography-h1 {
            font-family: 'Inter', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-primary);
            line-height: 1.2;
            letter-spacing: -0.025em;
            margin: 0;
        }
        
        .typography-h2 {
            font-family: 'Inter', sans-serif;
            font-size: 1.875rem;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.3;
            letter-spacing: -0.025em;
            margin: 0;
        }
        
        .typography-h3 {
            font-family: 'Inter', sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.4;
            margin: 0;
        }
        
        .typography-h4 {
            font-family: 'Inter', sans-serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-secondary);
            line-height: 1.4;
            margin: 0;
        }
        
        .typography-body {
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 400;
            color: var(--text-secondary);
            line-height: 1.6;
            margin: 0;
        }
        
        .typography-caption {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 400;
            color: var(--text-muted);
            line-height: 1.5;
            margin: 0;
        }
        
        .typography-mono {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-primary);
            line-height: 1.5;
        }
        
        /* Terminal Header */
        .terminal-header {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--border-radius-lg);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
            position: relative;
            overflow: hidden;
        }
        
        .terminal-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient-accent);
        }
        
        .terminal-title {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin: 0 0 0.5rem 0;
        }
        
        .terminal-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            font-weight: 400;
            color: var(--text-muted);
            margin: 0;
        }
        
        .terminal-status {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green-primary);
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Professional Navigation */
        .nav-container {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--border-radius-lg);
            padding: 1rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-md);
        }
        
        .nav-tabs {
            display: flex;
            gap: 0.5rem;
            background: var(--bg-tertiary);
            padding: 0.5rem;
            border-radius: var(--border-radius-md);
            overflow-x: auto;
        }
        
        .nav-tab {
            background: transparent;
            border: 1px solid transparent;
            border-radius: var(--border-radius-sm);
            padding: 0.75rem 1.5rem;
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-muted);
            cursor: pointer;
            transition: var(--transition-fast);
            white-space: nowrap;
            min-width: 0;
            flex-shrink: 0;
        }
        
        .nav-tab:hover {
            background: var(--bg-surface);
            color: var(--text-secondary);
            border-color: var(--border-secondary);
        }
        
        .nav-tab.active {
            background: var(--gradient-accent);
            color: var(--text-primary);
            border-color: var(--border-accent);
            font-weight: 600;
            box-shadow: var(--shadow-sm);
        }
        
        /* Professional Cards */
        .professional-card {
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: var(--border-radius-lg);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow-md);
            transition: var(--transition-normal);
            position: relative;
            overflow: hidden;
        }
        
        .professional-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
            border-color: var(--border-secondary);
        }
        
        .card-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-primary);
        }
        
        .card-title {
            font-family: 'Inter', sans-serif;
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
        }
        
        .card-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            color: var(--text-muted);
            margin: 0.25rem 0 0 0;
        }
        
        /* Financial Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .metric-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-primary);
            border-radius: var(--border-radius-md);
            padding: 1.25rem;
            transition: var(--transition-fast);
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-accent);
            opacity: 0;
            transition: var(--transition-fast);
        }
        
        .metric-card:hover::before {
            opacity: 1;
        }
        
        .metric-label {
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0 0 0.5rem 0;
        }
        
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0 0 0.25rem 0;
        }
        
        .metric-change {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            font-weight: 500;
            margin: 0;
        }
        
        .metric-change.positive {
            color: var(--green-primary);
        }
        
        .metric-change.negative {
            color: var(--red-primary);
        }
        
        .metric-change.neutral {
            color: var(--text-muted);
        }
        
        /* Professional Tables */
        .professional-table {
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: var(--border-radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }
        
        .table-header {
            background: var(--bg-tertiary);
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-primary);
        }
        
        .table-title {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
        }
        
        /* Input Components */
        .input-group {
            margin-bottom: 1.5rem;
        }
        
        .input-label {
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin: 0 0 0.5rem 0;
            display: block;
        }
        
        .input-description {
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin: 0.25rem 0 0 0;
            line-height: 1.4;
        }
        
        /* Streamlit Component Overrides */
        .stSelectbox > div > div {
            background: var(--bg-surface) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: var(--border-radius-md) !important;
            color: var(--text-primary) !important;
        }
        
        .stSelectbox > div > div > div {
            color: var(--text-primary) !important;
        }
        
        .stNumberInput > div > div > input {
            background: var(--bg-surface) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: var(--border-radius-md) !important;
            color: var(--text-primary) !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        .stNumberInput > div > div > input:focus {
            border-color: var(--border-accent) !important;
            box-shadow: 0 0 0 2px rgba(247, 147, 26, 0.2) !important;
        }
        
        .stButton > button {
            background: var(--gradient-accent) !important;
            border: none !important;
            border-radius: var(--border-radius-md) !important;
            padding: 0.75rem 1.5rem !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            color: var(--text-primary) !important;
            transition: var(--transition-fast) !important;
            box-shadow: var(--shadow-sm) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: var(--shadow-md) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) !important;
        }
        
        /* Radio Button Styling for Navigation */
        div[role="radiogroup"] {
            background: var(--bg-tertiary) !important;
            padding: 0.5rem !important;
            border-radius: var(--border-radius-lg) !important;
            display: flex !important;
            gap: 0.5rem !important;
            overflow-x: auto !important;
        }
        
        div[role="radiogroup"] > label {
            background: transparent !important;
            border: 1px solid transparent !important;
            border-radius: var(--border-radius-md) !important;
            padding: 0.875rem 1.5rem !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            color: var(--text-muted) !important;
            transition: var(--transition-fast) !important;
            cursor: pointer !important;
            white-space: nowrap !important;
            min-width: 0 !important;
            flex-shrink: 0 !important;
            margin: 0 !important;
        }
        
        div[role="radiogroup"] > label:hover {
            background: var(--bg-surface) !important;
            color: var(--text-secondary) !important;
            border-color: var(--border-secondary) !important;
        }
        
        div[role="radiogroup"] > label[data-checked="true"] {
            background: var(--gradient-accent) !important;
            color: var(--text-primary) !important;
            border-color: var(--border-accent) !important;
            font-weight: 600 !important;
            box-shadow: var(--shadow-sm) !important;
        }
        
        div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }
        
        /* Alert Styling */
        .stAlert {
            background: var(--bg-surface) !important;
            border: 1px solid var(--border-primary) !important;
            border-radius: var(--border-radius-md) !important;
            color: var(--text-primary) !important;
        }
        
        .stSuccess {
            border-left: 4px solid var(--green-primary) !important;
        }
        
        .stError {
            border-left: 4px solid var(--red-primary) !important;
        }
        
        .stWarning {
            border-left: 4px solid var(--orange-primary) !important;
        }
        
        .stInfo {
            border-left: 4px solid var(--blue-primary) !important;
        }
        
        /* Risk Indicators */
        .risk-indicator {
            border-radius: var(--border-radius-lg);
            padding: 1.5rem;
            margin: 1rem 0;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }
        
        .risk-high {
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(238, 90, 82, 0.05));
            border: 1px solid rgba(255, 107, 107, 0.3);
        }
        
        .risk-medium {
            background: linear-gradient(135deg, rgba(247, 147, 26, 0.1), rgba(225, 112, 85, 0.05));
            border: 1px solid rgba(247, 147, 26, 0.3);
        }
        
        .risk-low {
            background: linear-gradient(135deg, rgba(0, 212, 170, 0.1), rgba(0, 184, 148, 0.05));
            border: 1px solid rgba(0, 212, 170, 0.3);
        }
        
        /* Loading States */
        .loading-skeleton {
            background: linear-gradient(90deg, var(--bg-surface) 25%, var(--bg-tertiary) 50%, var(--bg-surface) 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: var(--border-radius-md);
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* Terminal-style Command Bar */
        .command-bar {
            background: var(--bg-primary);
            border: 1px solid var(--border-secondary);
            border-radius: var(--border-radius-md);
            padding: 0.75rem 1rem;
            margin: 1rem 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .command-prompt {
            color: var(--green-primary);
            font-weight: 600;
        }
        
        .command-text {
            color: var(--text-primary);
            flex: 1;
        }
        
        .command-cursor {
            width: 8px;
            height: 1em;
            background: var(--text-primary);
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .terminal-header {
                padding: 1.5rem;
            }
            
            .terminal-title {
                font-size: 1.25rem;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .nav-tabs {
                flex-direction: column;
                gap: 0.25rem;
            }
            
            .nav-tab {
                padding: 0.75rem 1rem;
                text-align: center;
            }
        }
        
        /* Performance Optimizations */
        * {
            box-sizing: border-box;
        }
        
        .gpu-accelerated {
            transform: translateZ(0);
            backface-visibility: hidden;
            perspective: 1000;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: var(--border-radius-sm);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-secondary);
            border-radius: var(--border-radius-sm);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
    </style>
    """

# Professional Terminal Header
def terminal_header():
    return """
    <div class="terminal-header">
        <div class="terminal-title">MARGIN ANALYTICS TERMINAL</div>
        <div class="terminal-subtitle">Advanced Portfolio Management & Risk Analysis Platform</div>
        <div class="terminal-status">
            <div class="status-indicator">
                <div class="status-dot"></div>
                LIVE DATA
            </div>
            <div class="status-indicator">
                <div class="status-dot"></div>
                SYSTEM OPERATIONAL
            </div>
            <div class="status-indicator">
                <div class="status-dot"></div>
                MARKETS OPEN
            </div>
        </div>
    </div>
    """

# Professional app header
def app_header():
    return terminal_header()

# Professional navigation explanation
def navigation_explanation():
    return """
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">Platform Navigation</div>
        </div>
        <p class="typography-body">
            Navigate through different analytical modules using the tabs above. Each module provides 
            specialized tools for portfolio analysis, risk management, and strategic planning.
        </p>
    </div>
    """

# Explanation card for date range
def date_range_explanation():
    return """
    <div class="input-description">
        Select the analysis period for historical data evaluation. Time range affects all calculations, 
        backtests, and performance metrics across the platform.
    </div>
    """

# Explanation for Market Overview tab
def market_overview_explanation():
    return """
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">Market Intelligence Dashboard</div>
            <div class="card-subtitle">Real-time ETF Performance Analytics</div>
        </div>
        <p class="typography-body">
            Comprehensive analysis of major ETF instruments including S&P 500 (SPY) and Total Market (VTI) 
            exposure. Monitor key performance indicators, volatility metrics, and market trends to inform 
            strategic positioning decisions.
        </p>
    </div>
    """

# Explanation for Price Analysis tab
def price_analysis_explanation():
    return """
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">Technical Price Analysis</div>
            <div class="card-subtitle">Advanced Charting & Pattern Recognition</div>
        </div>
        <p class="typography-body">
            Professional-grade candlestick charts with technical indicators. Green candles indicate 
            bullish periods (close > open), red candles indicate bearish periods (close < open). 
            Wicks represent intraperiod high/low price discovery ranges.
        </p>
        <div class="command-bar">
            <span class="command-prompt">$</span>
            <span class="command-text">analyze --symbol=SPY --timeframe=1M --indicators=MACD,RSI</span>
            <div class="command-cursor"></div>
        </div>
    </div>
    """

# Explanation for Dividend Analysis tab
def dividend_analysis_explanation():
    return """
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">Dividend Flow Analysis</div>
            <div class="card-subtitle">Income Distribution & Yield Tracking</div>
        </div>
        <p class="typography-body">
            Quantitative analysis of dividend distributions and yield patterns. Monitor quarterly 
            payouts, seasonal variations, and income sustainability metrics for portfolio income planning.
        </p>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Analysis Scope</div>
                <div class="metric-value">Quarterly Distributions</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Pattern Recognition</div>
                <div class="metric-value">Seasonal Trends</div>
            </div>
        </div>
    </div>
    """

# Explanation for Margin Calculator tab
def margin_calculator_explanation():
    return """
    <div class="professional-card">
        <div class="card-header">
            <div class="card-title">Leverage & Margin Analytics</div>
            <div class="card-subtitle">Risk Assessment & Position Sizing</div>
        </div>
        <p class="typography-body">
            Advanced margin trading calculator with real-time risk assessment. Calculate optimal 
            leverage ratios, margin requirements, and liquidation thresholds for sophisticated 
            portfolio management strategies.
        </p>
        <div class="risk-indicator risk-medium">
            <strong>Risk Advisory:</strong> Margin trading amplifies both potential returns and losses. 
            Positions may be subject to forced liquidation if maintenance margins are breached.
        </div>
    </div>
    """

# Professional footer
def app_footer():
    import datetime
    return f"""
    <div class="terminal-header" style="margin-top: 3rem;">
        <div class="terminal-title">SYSTEM STATUS</div>
        <div class="terminal-subtitle">Platform Information & Disclaimers</div>
        <div class="command-bar">
            <span class="command-prompt">$</span>
            <span class="command-text">system.status --updated={datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</span>
        </div>
        <p class="typography-caption" style="margin-top: 1rem; text-align: center;">
            Market data sourced from Yahoo Finance API. This platform is for educational and analytical 
            purposes only. Not intended as investment advice. Past performance does not guarantee future results.
        </p>
    </div>
    """
    
    
    