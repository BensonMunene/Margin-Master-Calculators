# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains three independent financial analysis applications:

1. **Margin App** - Professional margin trading analytics terminal with Bloomberg Terminal-style UI
2. **ADE App** - Financial terminal application (ADE Financial Terminal)  
3. **Returns Viz App** - ETF CAGR visualization platform with two implementations (Streamlit, Django SQLite)

Additionally, there is a Django implementation of the Margin App:
- **Margin_Django_App** - Django version of Margin App with PostgreSQL support

## Common Development Commands

### Running Applications

```bash
# Margin App (Streamlit)
cd "Margin App"
streamlit run Margin_App.py

# ADE App (Streamlit)  
cd "ADE App"
streamlit run ADE_APP.py

# Returns Viz App - Streamlit Version
cd "Returns Viz App/Streamlit App/Visualization app"
streamlit run "Returns Viz App.py"

# Returns Viz App - Django SQLite Version
cd "Returns Viz App/Django App"
python manage.py migrate
python manage.py test_data  # Test CSV data loading
python manage.py runserver

# Margin Django App - PostgreSQL Version
cd "Margin_Django_App"
python manage.py migrate
python manage.py import_data --clear  # Import data from CSV files
python manage.py runserver
```

### Testing Commands

```bash
# Django app tests
python manage.py test

# Run specific test
python manage.py test calculator.tests.TestMarginCalculations

# Django migrations check (dry run)
python manage.py makemigrations --check --dry-run

# Test API endpoints (Returns Viz Django App)
cd "Returns Viz App/Django App"
python test_api_endpoint.py
python test_fmp_api.py
python test_performance_overview.py
python test_msft_2025.py

# Test browser debugging
python debug_browser_issue.py
```

### Linting and Type Checking

```bash
# Python linting (if ruff is installed)
ruff check .

# Django migrations check
python manage.py makemigrations --check --dry-run
```

## Installation Requirements

### Core Dependencies
- **Python**: 3.8+ (3.11 recommended)
- **Streamlit Apps**: `pip install -r requirements.txt`
  - streamlit>=1.28.0, pandas>=2.0.0, numpy>=1.24.0, matplotlib, seaborn, plotly>=5.17.0
- **Django SQLite**: Django 4.2+, see `Returns Viz App/Django App/requirements.txt`
- **Django PostgreSQL**: Django 5.2, psycopg2-binary, see `Margin_Django_App/requirements.txt`

### Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

## Data Configuration

### Data Directory Structure
```
Data/
├── ETFs and Fed Funds Data.xlsx  # Master data file with historical Fed Funds rates
├── SPY.csv                        # S&P 500 price history (1993+)
├── VTI.csv                        # Total Market price history (2001+)  
├── SPY Dividends.csv              # SPY dividend history
├── VTI Dividends.csv              # VTI dividend history
└── FED_FUNDS.xlsx                 # Federal funds rates
```

### Configuring Data Path
```python
# Margin App/Margin_App.py line ~34
local_dir = r"D:\Benson\aUpWork\Ben Ruff\Implementation\Data"
github_dir = "Data"
use_local = True  # Toggle for deployment
```

### API Integration
- **Financial Modeling Prep API**: Used in `fmp_data_provider.py` (Margin App) and `fmp_api.py` (Returns Viz Django App)
- **Django PostgreSQL**: No local files needed, uses API:
  ```bash
  python manage.py fetch_etf_data --api-key YOUR_KEY --from-date 2000-01-01
  ```
- **FMP API Configuration**: Set `FMP_API_KEY` in Django settings or environment variables
- **API Caching**: All API responses cached (1 hour for historical data, 24 hours for ticker info)
- **Ticker Validation**: Automatic validation against FMP search endpoint

## High-Level Architecture

### Margin App Architecture

```
Margin App/
├── Margin_App.py              # Main entry, tab navigation, UI orchestration
├── historical_backtest.py     # Backtesting engine with liquidation simulation
├── cushion_analysis.py        # Margin cushion risk analytics
├── parameter_sweep.py         # Multi-parameter optimization
├── visualizations.py          # Chart generation (Plotly/Matplotlib)
├── UI_Components.py           # Reusable UI elements, CSS theming
└── fmp_data_provider.py       # Financial Modeling Prep API integration
```

**Key Design Patterns:**
- Tab-based navigation using Streamlit session state
- Modular architecture with clear separation of concerns
- Caching strategy: `@st.cache_data` with TTL for data loading
- Professional Bloomberg Terminal dark theme throughout
- Liquidation simulation with 2-day cooling period
- Three rebalancing strategies in backtesting

**Backtesting Modes:**
- `liquidation_reentry`: Liquidate on margin call, wait 2 days, re-enter
- `profit_threshold`: Exit when profit target reached, re-enter
- `margin_restart`: Track multiple rounds with fresh capital injections

### Returns Viz App Architecture

**Three Progressive Implementations:**
1. **Streamlit**: Rapid prototyping, single-user analysis
2. **Django SQLite**: Multi-user web deployment, REST API
3. **Django PostgreSQL**: Production-ready, real-time data via API

```
Returns Viz App/Django App/
├── etf_analyzer/
│   ├── fmp_api.py              # FMP API integration
│   ├── performance_metrics.py  # Sharpe, Sortino, Max Drawdown calculations
│   ├── utils.py               # Data loading and CAGR matrix creation
│   ├── views.py               # API endpoints and web views
│   └── management/commands/
│       ├── clear_cache.py     # Cache management
│       └── test_data.py       # Data loading validation
├── test_*.py                  # Standalone test scripts
└── debug_browser_issue.py     # Browser debugging utilities
```

**Common CAGR Calculation Logic:**
- Matrix generation: `create_cagr_matrix()` function in `utils.py`
- Annual returns from daily data: `(1 + daily_returns).prod() - 1`
- Multi-year CAGR: `(cumulative_return ^ (1/years)) - 1`
- Performance metrics: Sharpe ratio, Sortino ratio, Max Drawdown in `performance_metrics.py`

### Cross-App Patterns

- **UI Framework**: Streamlit with `layout="wide"`, `initial_sidebar_state="collapsed"`
- **Styling**: Custom CSS, professional financial dashboard appearance
- **Data Processing**: Pandas DataFrames, date-indexed time series
- **Visualization**: Plotly (interactive), Matplotlib/Seaborn (static)
- **Performance**: Caching decorators, efficient data filtering
- **API Integration**: FMP API with automatic caching and validation
- **Error Handling**: Comprehensive try-catch blocks with user-friendly messages
- **Testing**: Standalone test scripts for API validation and debugging

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
- Uses IBKR formula: Fed Funds Rate + 1.5% (Reg-T) or + 2.0% (Portfolio Margin)
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

## Database Setup

### Django SQLite (Returns Viz App)
- Automatic with `python manage.py migrate`
- Test data loading: `python manage.py test_data`

### Django PostgreSQL (Margin Django App)
```bash
# Option 1: Manual setup
psql -U postgres
CREATE DATABASE margin_calculator_db;
CREATE USER margin_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE margin_calculator_db TO margin_user;

# Option 2: Automated setup (if setup_database.py exists)
python setup_database.py

# Configure .env file
DB_NAME=margin_calculator_db
DB_USER=margin_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Alternative database name from README_POSTGRES.md
DB_NAME=margin_calculator  # simpler name used in docs
```

### Django Management Commands
```bash
# Import data from CSV files (Margin Django App)
python manage.py import_data --clear  # Clear existing data first
python manage.py import_data         # Keep existing data

# Test data loading (Returns Viz Django App)
python manage.py test_data

# Cache management (Returns Viz Django App)
python manage.py clear_cache        # Clear all cached data

# API data fetching (if FMP API configured)
python manage.py fetch_etf_data --api-key YOUR_KEY --from-date 2000-01-01
```

## Deployment

### Docker Deployment (Margin App)
```bash
# Build and run with Docker Compose
cd "Margin App"
docker-compose up -d

# View logs
docker-compose logs -f app
```

### AWS Deployment Architecture
- **Infrastructure**: EC2 t2.micro instance (Free Tier eligible)
- **Containerization**: Docker with Nginx reverse proxy
- **Security**: Multi-layer authentication (Nginx Basic Auth + Streamlit)
- **Monitoring**: CloudWatch integration for logs and metrics
- **SSL**: Let's Encrypt certificates via Nginx
- **Storage**: 20GB EBS root volume (app + data + logs)
- See `Margin App/DEPLOYMENT_PLAN.md` for detailed AWS deployment guide

### Key Deployment Files
- `Margin App/DEPLOYMENT_PLAN.md`: Complete AWS deployment architecture
- `Margin App/Liquidation_Reentry_Methodology.md`: Detailed backtest logic documentation

## Testing and Validation

### Key Testing Areas
- **Margin Calculations**: Verify against `Excel workbooks/WSP-Margin-Call-Price-Calculator_vF.xlsx`
- **Liquidation Logic**: 2-day cooling period in backtests
- **CAGR Matrices**: Annual returns from daily data
- **Interest Calculations**: IBKR formula (Fed Funds + 1.5%)
- **API Integration**: FMP API validation, ticker validation, data caching
- **Performance Metrics**: Sharpe ratio, Sortino ratio, Max Drawdown calculations
- **Django API Endpoints**: Test with `test_api_endpoint.py` and other test scripts

### Performance Optimization
- Streamlit caching: `@st.cache_data(ttl=3600)`
- Django queries: Use `select_related()` and `prefetch_related()`
- Database indexes on date columns
- Pagination for large datasets

## Important File Locations

### Documentation
- `Historical_Backtest_Documentation.md`: Backtest implementation details
- `Implementation_Summary.md`: Project overview and status
- `Returns Viz App/Streamlit App/Visualization app/Returns_Calculation_Guide.md`: CAGR calculation methodology

### Notebooks
- `Codes and Notebooks/Data Preparation.ipynb`: Data processing workflows
- `Codes and Notebooks/Margin Call Notes.ipynb`: Margin calculation formulas
- `Margin App/App Logic.ipynb`: Application logic documentation

## Important Reminders

- **File Paths**: Use absolute paths in Django, relative paths in Streamlit
- **Data Loading**: Check `use_local` flag in Streamlit apps
- **Authentication**: Streamlit apps use st.secrets, Django uses environment variables
- **Deployment**: Docker containers include data files, no volume mounts needed
- **API Keys**: Store in `.env` files (Django) or `.streamlit/secrets.toml` (Streamlit)
- **Windows Paths**: Use raw strings (r"path") or forward slashes for Windows paths
- **API Testing**: Always run `test_fmp_api.py` before deploying to validate API integration
- **Cache Management**: Use `python manage.py clear_cache` when troubleshooting data issues
- **Performance Testing**: Use standalone test scripts to isolate and debug specific functionality