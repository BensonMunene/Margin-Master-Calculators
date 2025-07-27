# Returns Viz Django App

This is a Django implementation of the Returns Viz ETF CAGR Analysis application, providing the same functionality as the Streamlit version.

## Features

- Interactive CAGR (Compound Annual Growth Rate) matrix visualization
- ETF performance comparison (SPY, QQQ, DIA, VTI)
- Professional Bloomberg Terminal-style UI
- Export functionality for CAGR matrices and annual returns
- Responsive design with Bootstrap 5

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Test data loading:
```bash
python manage.py test_data
```

4. Run the development server:
```bash
python manage.py runserver
```

5. Access the application at: http://localhost:8000

## Project Structure

```
Django App/
├── etf_analyzer/          # Main Django app
│   ├── templates/         # HTML templates
│   ├── utils.py          # Data processing utilities
│   ├── views.py          # View functions
│   └── urls.py           # URL routing
├── returns_viz/          # Django project settings
├── static/               # Static files directory
├── manage.py            # Django management script
└── requirements.txt     # Python dependencies
```

## API Endpoints

- `/` - Main dashboard
- `/api/get-data/` - Get CAGR matrix and statistics
- `/api/download-matrix/` - Download CAGR matrix as CSV
- `/api/download-returns/` - Download annual returns as CSV

## Data Requirements

The app expects historical ETF data files in the following location:
`../Streamlit App/Historical Data/`

Required files:
- SPY.csv
- QQQ.csv
- DIA.csv
- VTI.csv

Each CSV file should contain columns: Date, Adj Close

## Differences from Streamlit Version

While the functionality is identical, the Django version provides:
- Better performance through proper caching
- RESTful API endpoints
- Enhanced security with CSRF protection
- More scalable architecture
- Easier deployment options

## Technical Documentation: Calculations and Algorithms

### CAGR (Compound Annual Growth Rate) Calculation

The core calculation of this application is the CAGR matrix, which shows annualized returns between any two years.

#### Mathematical Formula:
```
CAGR = (Ending Value / Beginning Value)^(1/Number of Years) - 1
```

#### Implementation in `utils.py`:

```python
def create_cagr_matrix(annual_returns_series, start_year=None, end_year=None):
    """
    Creates a matrix of Compound Annual Growth Rates (CAGR) between different year ranges.
    """
    returns_decimal = annual_returns_series / 100  # Convert percentages to decimals
    
    for start_yr in years:
        for end_yr in years:
            if end_yr >= start_yr:
                period_returns = returns_filtered.loc[start_yr:end_yr]
                num_years = len(period_returns)
                
                if num_years == 1:
                    # Single year: return the annual return as-is
                    cagr = period_returns.loc[start_yr] * 100
                else:
                    # Multi-year: compound the returns
                    cumulative_return = (1 + period_returns).prod()
                    cagr = (cumulative_return ** (1/num_years) - 1) * 100
```

#### Step-by-Step Example:
**Scenario**: SPY returns from 2020-2022
- 2020: +18.4%
- 2021: +28.7% 
- 2022: -18.1%

**Calculation**:
1. Convert to decimals: [0.184, 0.287, -0.181]
2. Calculate cumulative return: (1.184) × (1.287) × (0.819) = 1.247
3. Apply CAGR formula: (1.247)^(1/3) - 1 = 0.076 = **7.6% CAGR**

### Annual Returns Calculation

Annual returns are calculated from daily price data using compound growth.

#### Implementation in `utils.py`:

```python
def load_etf_data():
    # Calculate daily returns from adjusted close prices
    spy_data['SPY'] = spy_data['SPY'].pct_change()  # (P_today - P_yesterday) / P_yesterday
    
    # Group by year and compound daily returns
    annual_returns = combined_data.groupby('Year')[['DIA', 'SPY', 'QQQ', 'VTI']].apply(
        lambda x: (1 + x).prod() - 1  # Compound daily returns: (1+r1)×(1+r2)×...×(1+rn) - 1
    )
```

#### Mathematical Formula:
```
Annual Return = ∏(1 + daily_return_i) - 1
```

#### Example Calculation:
**Daily returns for first 5 days of 2023**: [0.01, -0.005, 0.02, 0.008, -0.012]

**Annual return calculation**:
```
(1.01) × (0.995) × (1.02) × (1.008) × (0.988) - 1 = 0.0205 = 2.05%
```

## Performance Metrics Documentation

The application calculates comprehensive performance metrics in `performance_metrics.py`:

### 1. Sharpe Ratio

**Purpose**: Risk-adjusted return measure

**Formula**: 
```
Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
```

**Code Implementation**:
```python
def sharpe_ratio(self) -> float:
    excess_return = self.cagr() - self.risk_free_rate
    return excess_return / self.volatility() if self.volatility() > 0 else 0.0
```

**Example**: 
- CAGR: 12%
- Risk-free rate: 2% 
- Volatility: 15%
- **Sharpe Ratio = (12% - 2%) / 15% = 0.67**

### 2. Sortino Ratio

**Purpose**: Downside risk-adjusted return (only considers negative volatility)

**Formula**:
```
Sortino Ratio = (Portfolio Return - Risk-Free Rate) / Downside Deviation
```

**Code Implementation**:
```python
def sortino_ratio(self) -> float:
    excess_return = self.cagr() - self.risk_free_rate
    downside_returns = self.daily_returns[self.daily_returns < self.daily_rf_rate]
    downside_deviation = downside_returns.std() * np.sqrt(252)
    return excess_return / downside_deviation if downside_deviation > 0 else 0.0
```

### 3. Maximum Drawdown

**Purpose**: Largest peak-to-trough decline

**Formula**:
```
Drawdown = (Current Value / Peak Value) - 1
Maximum Drawdown = Minimum(All Drawdowns)
```

**Code Implementation**:
```python
def maximum_drawdown(self) -> Dict[str, float]:
    cumulative = (1 + self.daily_returns).cumprod()
    peak = cumulative.expanding().max()
    drawdown = (cumulative / peak) - 1
    max_dd = drawdown.min()
```

**Example**: Portfolio peaks at $100, drops to $75
- **Maximum Drawdown = (75/100) - 1 = -25%**

### 4. Pain Index

**Purpose**: Average drawdown over entire period

**Formula**:
```
Pain Index = Average(|All Drawdown Values|)
```

**Code Implementation**:
```python
def pain_index(self) -> float:
    cumulative = (1 + self.daily_returns).cumprod()
    peak = cumulative.expanding().max()
    drawdown = (cumulative / peak) - 1
    return abs(drawdown.mean())
```

### 5. Volatility (Standard Deviation)

**Purpose**: Measure of price variability

**Formula**:
```
Annualized Volatility = Daily Volatility × √252
```

**Code Implementation**:
```python
def volatility(self, annualized: bool = True) -> float:
    vol = self.daily_returns.std()
    return vol * np.sqrt(252) if annualized else vol
```

### 6. Beta (Market Sensitivity)

**Purpose**: Correlation with benchmark movement

**Formula**:
```
Beta = Covariance(Asset, Benchmark) / Variance(Benchmark)
```

**Code Implementation**:
```python
def beta(self) -> float:
    aligned = pd.DataFrame({
        'asset': self.daily_returns,
        'benchmark': self.benchmark_returns
    }).dropna()
    
    covariance = aligned['asset'].cov(aligned['benchmark'])
    benchmark_variance = aligned['benchmark'].var()
    return covariance / benchmark_variance if benchmark_variance > 0 else None
```

### 7. Value at Risk (VaR)

**Purpose**: Maximum expected loss at given confidence level

**Formula**:
```
VaR(5%) = 5th Percentile of Daily Returns
```

**Code Implementation**:
```python
def value_at_risk(self, confidence: float = 0.05) -> float:
    return np.percentile(self.daily_returns, confidence * 100)
```

**Example**: If VaR(5%) = -2.5%, there's a 5% chance of losing more than 2.5% in a single day.

### 8. Win Rate

**Purpose**: Percentage of profitable periods

**Code Implementation**:
```python
def win_rate(self) -> float:
    positive_returns = (self.annual_returns > 0).sum()
    total_periods = len(self.annual_returns)
    return positive_returns / total_periods if total_periods > 0 else 0.0
```

### 9. Recovery Days

**Purpose**: Time to recover from maximum drawdown

**Code Implementation**:
```python
# Find recovery point (first time we reach peak again after max DD)
recovery_mask = after_dd >= peak_value
if recovery_mask.any():
    recovery_point = after_dd[recovery_mask].index[0]
    recovery_days = (recovery_point - max_dd_start).days
```

## Data Processing Flow

### 1. Data Loading Process
```python
# Load CSV files with Date and Adj Close columns
data = pd.read_csv("ETF.csv")
data['Date'] = pd.to_datetime(data['Date'])

# Calculate daily returns
data['daily_return'] = data['Adj Close'].pct_change()
```

### 2. Annual Aggregation
```python
# Group by year and compound daily returns
annual_returns = data.groupby('Year')['daily_return'].apply(
    lambda x: (1 + x).prod() - 1
)
```

### 3. CAGR Matrix Generation
```python
# Create matrix where each cell represents CAGR from start_year to end_year
for start_yr in years:
    for end_yr in years:
        if end_yr >= start_yr:
            period_returns = returns.loc[start_yr:end_yr]
            cumulative = (1 + period_returns).prod()
            cagr = (cumulative ** (1/num_years) - 1) * 100
            matrix.loc[end_yr, start_yr] = cagr
```

## Testing and Validation

Use the included test scripts to validate calculations:

```bash
# Test CAGR matrix calculations
python test_api_endpoint.py

# Test FMP API integration  
python test_fmp_api.py

# Test performance metrics
python test_performance_overview.py
```