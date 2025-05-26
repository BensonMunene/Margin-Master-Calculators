# ETF Margin Calculator & Analytics Platform

A professional-grade Streamlit application designed for ETF analysis and margin trading calculations. This platform provides comprehensive tools for analyzing S&P 500 (SPY) and Total Market (VTI) ETFs with advanced margin trading calculators and sophisticated visualization capabilities.

## 📊 Overview

The ETF Margin Calculator App is a powerful financial analysis tool that combines real-time ETF market data visualization with advanced margin trading calculations. Built for Pearson Creek Capital Management LLC, this application helps investors make informed decisions by providing:

- Real-time ETF price analysis with professional candlestick charts
- Comprehensive dividend distribution tracking and analysis
- Advanced margin calculator with multiple account types support
- Risk assessment tools and margin call price calculations
- Performance simulation capabilities
- Historical data analysis from 2010 to present

## 🚀 Key Features

### 1. **Advanced Margin Calculator** 
The flagship feature provides sophisticated margin trading analysis:

- **Dual Account Type Support**
  - Reg-T Account (standard 2:1 leverage)
  - Portfolio Margin Account (up to 7:1 leverage)
  
- **Real-Time Calculations**
  - Investment breakdown (cash vs. borrowed funds)
  - Shares purchasable at current market prices
  - Daily, monthly, and annual interest costs
  - Breakeven price calculations
  - Margin call price and risk assessment
  
- **Interactive Parameters**
  - Synchronized leverage and initial margin sliders
  - Custom ETF price input capability
  - Long/Short position selection
  - Adjustable interest rates and holding periods

### 2. **Market Overview Dashboard**
Comprehensive ETF performance metrics at a glance:

- Latest price tracking with percentage changes
- 52-week high/low indicators
- Average volume statistics
- Total dividend summaries
- Side-by-side comparison of SPY and VTI

### 3. **Price Analysis Module**
Professional-grade visualization tools:

- Interactive candlestick charts with monthly aggregation
- Bullish/bearish trend indicators
- Customizable date range selection
- Responsive chart design with hover details
- Premium color schemes for enhanced readability

### 4. **Dividend Analysis System**
Detailed dividend distribution tracking:

- Quarterly dividend bar charts with growth indicators
- Year-over-year growth rate calculations
- Annual dividend summaries
- Trend line analysis
- Color-coded growth/decline visualization

### 5. **Additional Features** (In Development)
- **Kelly Criterion Calculator**: Optimal position sizing based on probability
- **Historical Backtest Engine**: Test strategies against historical data
- **Performance Simulation**: Monte Carlo simulations and stress testing

## 🛠️ Technical Architecture

### Core Technologies
- **Frontend**: Streamlit 1.28+
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly (interactive charts), Matplotlib/Seaborn (static charts)
- **Styling**: Custom CSS with responsive design
- **Data Source**: Yahoo Finance historical data (CSV format)

### Project Structure
```
Margin App/
├── Margin_App.py           # Main application file
├── visualizations.py       # Chart generation functions
├── UI_Components.py        # UI elements and styling
├── image/                  # Logo and image assets
│   └── Margin_App/        # App-specific images
└── assets/                # Additional resources
```

### Data Files Required
```
Data/
├── SPY.csv                 # S&P 500 ETF price history
├── SPY Dividends.csv       # SPY dividend history
├── VTI.csv                 # Total Market ETF price history
└── VTI Dividends.csv       # VTI dividend history
```

## 📋 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Windows, macOS, or Linux operating system

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/etf-margin-calculator.git
   cd etf-margin-calculator
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Data Path**
   - Open `Margin App/Margin_App.py`
   - Locate the data directory configuration (around line 215)
   - Update paths if necessary:
     ```python
     local_dir = r"your/local/data/path"
     github_dir = "Data"  # For repository deployment
     ```

5. **Run the Application**
   ```bash
   cd "Margin App"
   streamlit run Margin_App.py
   ```

6. **Access the Application**
   - Open your web browser
   - Navigate to `http://localhost:8501`
   - The app should load automatically

## 💻 Usage Guide

### Getting Started

1. **Launch the Application**
   - Upon startup, you'll see the Pearson Creek Capital Management header
   - Six main tabs are available for different analysis functions

2. **Navigate the Interface**
   - **Tab 1: Margin Calculator** - Primary margin trading analysis tool
   - **Tab 2: Market Overview** - Quick ETF performance summary
   - **Tab 3: Price Analysis** - Detailed price charts
   - **Tab 4: Dividend Analysis** - Dividend distribution patterns
   - **Tab 5: Kelly Criterion** - Coming soon
   - **Tab 6: Historical Backtest** - Coming soon

### Using the Margin Calculator

1. **Select Account Type**
   - Click either "Reg-T Account" or "Portfolio Margin Account"
   - This determines your maximum leverage and margin requirements

2. **Configure Investment Parameters**
   - **Select ETF**: Choose between SPY or VTI
   - **Input Price**: Use current market price or enter custom value
   - **Position Type**: Select Long or Short
   - **Investment Amount**: Enter total position size desired

3. **Adjust Leverage Settings**
   - Use either the Leverage slider or Initial Margin slider
   - Values are synchronized automatically
   - See real-time updates to all calculations

4. **Review Results**
   - **Investment Breakdown**: Shows cash vs. borrowed amounts
   - **Shares Purchasable**: Number of shares you can buy
   - **Interest Costs**: Daily, monthly, and annual borrowing costs
   - **Maintenance Margin**: Required equity to avoid margin calls
   - **Risk Assessment**: Visual indicator of margin call risk

5. **Advanced Settings** (Optional)
   - Click "Advanced Settings" expander
   - Adjust annual interest rate
   - Set expected holding period
   - View customized interest calculations

### Analyzing Price Data

1. **Select Date Range**
   - Use the date pickers to set analysis period
   - Click "Apply Filter" to update charts
   - Default range is 2010 to present

2. **Interpret Candlestick Charts**
   - Green candles: Closing price higher than opening
   - Red candles: Closing price lower than opening
   - Wicks show high/low prices for the period

3. **Interactive Features**
   - Hover over candles for detailed price information
   - Use Plotly controls to zoom, pan, or save charts

### Understanding Dividend Analysis

1. **Reading the Charts**
   - Bar height represents dividend per share
   - Colors indicate different years
   - Q1-Q4 labels show quarterly distributions

2. **Growth Indicators**
   - Green arrows: Year-over-year increase
   - Red arrows: Year-over-year decrease
   - Trend line shows overall dividend trajectory

3. **Summary Statistics**
   - Total dividends paid over selected period
   - Latest annual dividend amount
   - Year-over-year growth percentage

## 📈 Best Practices

### Risk Management
- Always understand maintenance margin requirements
- Monitor margin call prices closely
- Consider interest costs in profit calculations
- Use stop-loss orders when trading on margin

### Data Analysis Tips
- Compare SPY and VTI for diversification insights
- Analyze dividend trends for income planning
- Use longer date ranges for trend identification
- Consider seasonal patterns in dividend distributions

### Performance Optimization
- The app caches data for faster loading
- Calculations are optimized for real-time updates
- Charts use responsive design for any screen size

## 🔧 Troubleshooting

### Common Issues and Solutions

1. **"Error loading data" message**
   - Verify CSV files exist in the Data directory
   - Check file permissions
   - Ensure correct path configuration

2. **Charts not displaying**
   - Clear browser cache
   - Refresh the page (F5)
   - Check browser console for errors

3. **Slow performance**
   - Reduce date range for analysis
   - Close other browser tabs
   - Restart the Streamlit server

4. **Margin calculations seem incorrect**
   - Verify account type selection
   - Check interest rate settings
   - Ensure leverage is within allowed limits

## 📊 Data Requirements

### File Format Specifications

**Price Data Files (SPY.csv, VTI.csv)**
- Columns: Date, Open, High, Low, Close, Volume
- Date format: YYYY-MM-DD
- Sorted by date (ascending)

**Dividend Files (SPY Dividends.csv, VTI Dividends.csv)**
- Columns: Date, Dividends
- Date format: YYYY-MM-DD
- One row per dividend payment

### Data Update Process
1. Download latest data from Yahoo Finance
2. Ensure CSV format matches specifications
3. Replace existing files in Data directory
4. Restart the application

## 🚧 Roadmap & Future Enhancements

### Q1 2025
- ✅ Core margin calculator functionality
- ✅ ETF price and dividend visualization
- ⏳ Kelly Criterion implementation
- ⏳ Basic backtesting engine

### Q2 2025
- 🔄 Monte Carlo simulation engine
- 🔄 Advanced risk metrics (Sharpe, Sortino)
- 🔄 Portfolio optimization tools
- 🔄 Export functionality for reports

### Q3 2025
- 📅 Real-time data integration
- 📅 Multi-asset portfolio analysis
- 📅 Mobile-responsive enhancements
- 📅 API for external integrations

## 🤝 Contributing

While this is a proprietary application for Pearson Creek Capital Management LLC, bug reports and feature suggestions are welcome through the official channels.

## 📄 License

This software is proprietary and confidential. All rights reserved by Pearson Creek Capital Management LLC.

## 📞 Support

For technical support or questions about the application:
- Contact your system administrator
- Refer to internal documentation
- Submit tickets through the company portal

---

**Disclaimer**: This application is for informational purposes only and should not be considered investment advice. Margin trading involves substantial risk, including the potential loss of more than your initial investment. Always consult with a qualified financial advisor before making investment decisions.

*Last Updated: November 2024*
