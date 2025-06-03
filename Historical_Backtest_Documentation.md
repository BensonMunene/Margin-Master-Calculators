# 📊 Historical Backtest Engine Documentation

## 🎯 Overview

The Historical Backtest Engine is a sophisticated, institutional-grade backtesting tool that simulates leveraged ETF trading strategies using real historical market data. It provides comprehensive analysis of margin trading performance with realistic interest costs, dividend reinvestment, and margin call detection.

## 🚀 Key Features

### 📈 **Realistic Market Simulation**

- **Real Historical Data**: Uses actual SPY and VTI price data from 1993/2001 onwards
- **Fed Funds Rate Integration**: Dynamic interest rate calculations based on historical Fed Funds rates
- **Dividend Reinvestment**: Automatic quarterly dividend reinvestment for compound growth
- **Margin Requirements**: Accurate Reg-T and Portfolio Margin account modeling

### ⚖️ **Advanced Margin Modeling**

- **Account Types**:
  - **Reg-T Account**: 50% initial margin, 25% maintenance margin, max 2:1 leverage
  - **Portfolio Margin**: Dynamic requirements, 15% maintenance margin, max 7:1 leverage
- **Interest Calculation**: Daily compounding interest on margin loans
- **Margin Call Detection**: Real-time monitoring of equity vs. maintenance requirements
- **Risk Assessment**: Comprehensive margin call analysis and warning systems

### 📊 **Comprehensive Analytics**

- **Performance Metrics**: CAGR, total return, Sharpe ratio, maximum drawdown
- **Risk Metrics**: Annual volatility, margin call frequency, interest costs
- **Visualization Suite**: Multi-layered interactive charts with Plotly
- **Export Functionality**: Full data export for further analysis

## 🔧 Technical Implementation

### **Data Architecture**

```
Data Sources:
├── ETFs and Fed Funds Data.xlsx (Primary data source)
│   ├── SPY/VTI daily prices
│   ├── Dividend payments
│   └── Historical Fed Funds rates
├── SPY.csv (Backup price data)
├── VTI.csv (Backup price data)
├── SPY Dividends.csv (Backup dividend data)
└── VTI Dividends.csv (Backup dividend data)
```

### **Core Functions**

#### `load_comprehensive_data()`

- **Purpose**: Loads and preprocesses all required data
- **Caching**: 1-hour TTL for optimal performance
- **Data Validation**: Ensures data integrity and completeness
- **Returns**: Excel data, SPY/VTI price data, dividend data

#### `run_historical_backtest()`

- **Purpose**: Core backtesting engine
- **Parameters**: ETF, start date, investment amount, leverage, account type
- **Process**:
  1. Daily portfolio value calculation
  2. Interest cost application
  3. Dividend reinvestment
  4. Margin requirement monitoring
  5. Performance metric calculation
- **Returns**: Complete time series DataFrame and summary metrics

#### `calculate_margin_params()`

- **Purpose**: Dynamic margin parameter calculation
- **Account-Specific**: Different rules for Reg-T vs Portfolio Margin
- **Parameters**: Initial margin, maintenance margin, interest rate spread

### **Performance Optimization**

- **Caching Strategy**: Strategic use of `@st.cache_data` for expensive operations
- **Vectorized Operations**: Pandas-based calculations for speed
- **Memory Management**: Efficient data structures and cleanup
- **Responsive UI**: Progressive loading and real-time feedback

## 📈 User Interface

### **Input Parameters**

1. **ETF Selection**: SPY or VTI
2. **Date Range**: Start date from available historical data
3. **Investment Amount**: Total position size (default: $100M)
4. **Account Type**: Reg-T or Portfolio Margin
5. **Leverage**: Dynamic options based on account type

### **Output Visualizations**

#### **Portfolio Performance Chart**

- **Top Panel**: Portfolio value and equity over time with margin call markers
- **Middle Panel**: Drawdown analysis with peak-to-trough visualization
- **Bottom Panel**: Margin loan evolution and interest costs

#### **Margin Analysis Chart**

- **Top Panel**: Equity vs. maintenance margin requirements
- **Bottom Panel**: Interest rate environment (Fed Funds vs. Margin rates)

#### **Performance Metrics Dashboard**

- **Financial Metrics**: Returns, CAGR, final values, costs
- **Risk Metrics**: Volatility, drawdowns, Sharpe ratio, margin calls
- **Interactive Elements**: Expandable detailed metrics and explanations

## 🎲 Mathematical Framework

### **Interest Calculation**

```
Daily Interest Rate = (Fed Funds Rate + Margin Spread) / 365
Daily Interest Cost = Margin Loan × Daily Interest Rate
```

### **Margin Requirements**

```
Portfolio Value = Shares × Current Price
Equity = Portfolio Value - Margin Loan
Maintenance Margin = Portfolio Value × Maintenance %
Margin Call = Equity < Maintenance Margin
```

### **Performance Metrics**

```
Total Return = (Final Equity - Initial Cash) / Initial Cash × 100
CAGR = ((Final Equity / Initial Cash)^(1/years) - 1) × 100
Sharpe Ratio = CAGR / Annual Volatility
Max Drawdown = min((Equity - Rolling Max) / Rolling Max × 100)
```

### **Dividend Reinvestment**

```
Dividend Received = Shares × Dividend Per Share
Additional Shares = Dividend Received / Current Price
New Total Shares = Previous Shares + Additional Shares
```

## 🔍 Advanced Features

### **Margin Call Analysis**

- **Detection Algorithm**: Real-time monitoring of equity ratios
- **Historical Tracking**: Complete log of all margin call events
- **Risk Visualization**: Red markers on performance charts
- **Detailed Reporting**: Date, equity level, and required margin for each event

### **Interest Rate Environment**

- **Historical Fed Funds**: Actual rates from Excel data source
- **Margin Rate Calculation**: Fed Funds + account-specific spread
- **Visual Timeline**: Interest rate evolution over backtest period
- **Cost Analysis**: Total interest paid throughout holding period

### **Dividend Impact Analysis**

- **Reinvestment Modeling**: Automatic dividend reinvestment
- **Compound Growth**: Shares accumulation over time
- **Performance Impact**: Isolation of dividend contribution to returns
- **Tax Considerations**: (Future enhancement for tax-adjusted returns)

## 🛠️ Configuration Options

### **Account Type Settings**

```python
Reg-T Account:
- Max Leverage: 2.0x
- Initial Margin: 50%
- Maintenance Margin: 25%
- Interest Spread: Fed Funds + 1.5%

Portfolio Margin:
- Max Leverage: 7.0x
- Initial Margin: Dynamic (14.29% - 100%)
- Maintenance Margin: 15%
- Interest Spread: Fed Funds + 2.0%
```

### **Performance Tuning**

- **Cache TTL**: 1 hour for data functions
- **Calculation Frequency**: Daily (can be adjusted)
- **Chart Resolution**: Optimized for web display
- **Memory Usage**: Efficient DataFrame operations

## 📋 Usage Examples

### **Conservative Strategy Example**

```
ETF: SPY
Start Date: 2010-01-01
Investment: $1,000,000
Account: Reg-T
Leverage: 1.5x
Expected: Lower volatility, moderate returns
```

### **Aggressive Strategy Example**

```
ETF: VTI
Start Date: 2008-01-01
Investment: $10,000,000
Account: Portfolio Margin
Leverage: 4.0x
Expected: Higher returns, increased risk
```

## ⚠️ Risk Considerations

### **Margin Call Risks**

- **Frequency**: Higher leverage = more frequent margin calls
- **Market Stress**: Increased calls during market downturns
- **Interest Burden**: Compounding costs reduce returns over time
- **Forced Liquidation**: Simulated but not modeled in current version

### **Model Limitations**

- **Perfect Execution**: No slippage or execution delays
- **Infinite Liquidity**: No impact from large position sizes
- **No Taxes**: Tax implications not currently modeled
- **Static Rates**: Interest rates updated daily but assumed constant intraday

## 🔮 Future Enhancements

### **Planned Features**

1. **Monte Carlo Simulations**: Probabilistic outcome modeling
2. **Tax-Adjusted Returns**: After-tax performance analysis
3. **Transaction Costs**: Bid-ask spreads and commissions
4. **Options Strategies**: Covered calls and protective puts
5. **Multi-Asset Portfolios**: Correlation analysis and optimization
6. **Real-Time Integration**: Live market data feeds
7. **Custom Scenarios**: User-defined market stress tests

### **Technical Roadmap**

- **Performance Optimization**: GPU acceleration for large datasets
- **Database Integration**: PostgreSQL for faster data access
- **API Development**: RESTful API for programmatic access
- **Mobile Optimization**: Responsive design improvements
- **Cloud Deployment**: AWS/Azure hosting options

## 📞 Support and Documentation

### **Getting Started**

1. Navigate to the "Historical Backtest" tab
2. Select your ETF (SPY or VTI)
3. Choose your start date and investment amount
4. Configure account type and leverage
5. Click "Run Historical Backtest"
6. Analyze results and export data if needed

### **Troubleshooting**

- **Data Loading Issues**: Ensure Excel file paths are correct
- **Performance Lag**: Reduce date range for faster processing
- **Chart Display**: Refresh browser if visualizations don't load
- **Export Problems**: Check browser download settings

### **Best Practices**

- **Start Conservative**: Begin with lower leverage to understand behavior
- **Multiple Scenarios**: Test different date ranges and parameters
- **Risk Assessment**: Pay attention to margin call frequency and costs
- **Documentation**: Export results for further analysis and record-keeping

---

## 🏆 Conclusion

The Historical Backtest Engine represents a quantum leap in retail trading analysis tools, bringing institutional-grade backtesting capabilities to individual investors. By combining real historical data, accurate margin modeling, and comprehensive risk analysis, it provides unprecedented insights into leveraged ETF trading strategies.

Whether you're a conservative investor looking to understand the impact of modest leverage or an aggressive trader evaluating high-leverage strategies, this tool provides the analytical framework to make informed decisions based on historical evidence rather than speculation.

**Built with precision. Powered by data. Designed for success.**
