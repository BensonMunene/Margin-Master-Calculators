# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains three independent financial analysis applications:

1. **Margin App** - Professional margin trading analytics terminal with Bloomberg Terminal-style UI
2. **ADE App** - Financial terminal application (ADE Financial Terminal)
3. **Returns Viz App** - ETF CAGR visualization platform with three implementations (Streamlit, Django SQLite, Django PostgreSQL)

## Running the Applications

### Margin App (Streamlit)
```bash
cd "Margin App"
streamlit run Margin_App.py
```

### ADE App (Streamlit)
```bash
cd "ADE App"
streamlit run ADE_APP.py
```

### Returns Viz App

#### Streamlit Version
```bash
cd "Returns Viz App/Streamlit App/Visualization app"
streamlit run "Returns Viz App.py"
```

#### Django SQLite Version
```bash
cd "Returns Viz App/Django App"
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Django PostgreSQL Version
```bash
cd "Returns Viz App/Django App with postgreSQL DB"
pip install -r requirements.txt
python setup_database.py  # Automated setup
python manage.py migrate
python manage.py fetch_etf_data  # Fetch data from API
python manage.py runserver
```

## Installation Requirements

### Core Streamlit Apps
```bash
pip install -r requirements.txt
```

### Django Apps
See individual requirements.txt in each Django app directory. Key differences:
- SQLite version: Basic Django dependencies
- PostgreSQL version: Includes `psycopg2-binary`, `python-decouple`, `requests`

## Data Configuration

### Central Data Directory
All Streamlit apps use `/Data` directory. Configure in each app:

```python
# Margin App/Margin_App.py line ~34
local_dir = r"D:\Benson\aUpWork\Ben Ruff\Implementation\Data"
github_dir = "Data"
use_local = True  # Toggle for deployment
```

### Required Data Files
- `ETFs and Fed Funds Data.xlsx` - Master data file with SPY/VTI prices, dividends, Fed rates
- `SPY.csv`, `VTI.csv` - ETF price history (alternative to Excel)
- `SPY Dividends.csv`, `VTI Dividends.csv` - Dividend history (alternative to Excel)
- `FED_FUNDS.xlsx` - Federal funds rates

### Django PostgreSQL Data
Uses Financial Modeling Prep API instead of local files:
```bash
python manage.py fetch_etf_data --api-key YOUR_KEY --from-date 2000-01-01
```

## High-Level Architecture

### Margin App Architecture

```
Margin App/
├── Margin_App.py              # Main entry, tab navigation, UI orchestration
├── historical_backtest.py     # Backtesting engine with liquidation simulation
├── cushion_analysis.py        # Margin cushion risk analytics
├── parameter_sweep.py         # Multi-parameter optimization
├── visualizations.py          # Chart generation (Plotly/Matplotlib)
└── UI_Components.py           # Reusable UI elements, CSS theming
```

**Key Design Patterns:**
- Tab-based navigation using Streamlit session state
- Modular architecture with clear separation of concerns
- Caching strategy: `@st.cache_data` with TTL for data loading
- Professional Bloomberg Terminal dark theme throughout
- Liquidation simulation with 2-day cooling period
- Three rebalancing strategies in backtesting

### Returns Viz App Architecture

**Three Progressive Implementations:**
1. **Streamlit**: Rapid prototyping, single-user analysis
2. **Django SQLite**: Multi-user web deployment, REST API
3. **Django PostgreSQL**: Production-ready, real-time data via API

**Common CAGR Calculation Logic:**
- Matrix generation: `create_cagr_matrix()` function
- Annual returns from daily data: `(1 + daily_returns).prod() - 1`
- Multi-year CAGR: `(cumulative_return ^ (1/years)) - 1`

### Cross-App Patterns

- **UI Framework**: Streamlit with `layout="wide"`, `initial_sidebar_state="collapsed"`
- **Styling**: Custom CSS, professional financial dashboard appearance
- **Data Processing**: Pandas DataFrames, date-indexed time series
- **Visualization**: Plotly (interactive), Matplotlib/Seaborn (static)
- **Performance**: Caching decorators, efficient data filtering

## Critical Implementation Details

### Margin Calculations
```python
# Reg-T Account
max_leverage = 2.0
maintenance_margin = 25%

# Portfolio Margin
max_leverage = 7.0
maintenance_margin = 15%

# Margin Call Price
P_call = (Margin_Loan / Shares) / (1 - Maintenance_Margin_%)
```

### Interest Calculations
- Uses IBKR formula: Fed Funds Rate + 1.5%
- Daily compounding in backtests
- Historical Fed Funds rates from Excel file

### Liquidation Logic
1. Check for margin call daily
2. If triggered: liquidate position
3. Wait 2 days (cooling period)
4. Re-enter with remaining equity

### Data Format Requirements
**Price Data:**
- Columns: Date, Open, High, Low, Close, Volume
- Date format: YYYY-MM-DD
- Sorted ascending by date

**Dividend Data:**
- Columns: Date, Dividends
- One row per dividend payment

## Django-Specific Commands

### Django SQLite Version
```bash
python manage.py test_data  # Test CSV data loading
```

### Django PostgreSQL Version
```bash
# Database setup
python create_db.sql  # Or use setup_database.py

# Fetch ETF data from API
python manage.py fetch_etf_data --symbols SPY,QQQ,DIA,VTI --from-date 2000-01-01

# Run development server
python manage.py runserver
```

## Testing and Validation

### Manual Testing Points
- Margin calculations: Verify against `Excel workbooks/WSP-Margin-Call-Price-Calculator_vF.xlsx`
- Backtest results: Check liquidation logic and interest calculations
- CAGR matrices: Validate against manual calculations
- UI responsiveness: Test with 20+ years of data

### Performance Considerations
- Use `@st.cache_data(ttl=3600)` for expensive operations
- Filter data before visualization
- Implement database indexing in Django versions
- Consider pagination for large datasets
