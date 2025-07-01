# Returns Calculation Guide 📊

This document explains the mathematical formulas used to convert ETF close prices into daily returns and then into Compound Annual Growth Rates (CAGR).

## 🔢 Step 1: Close Prices to Daily Returns

### Formula

For each trading day, we calculate the **daily return** as:

```
Daily Return = (Price_today / Price_yesterday) - 1
```

**Alternative form:**

```
Daily Return = (Price_today - Price_yesterday) / Price_yesterday
```

### Example

- **Day 1**: SPY closes at $100
- **Day 2**: SPY closes at $102
- **Daily Return** = (102 / 100) - 1 = 0.02 = **2.0%**

### Python Implementation

```python
# Convert prices to returns
spy_data['SPY'] = spy_data['SPY'].pct_change()
```

The `pct_change()` function calculates: `(current / previous) - 1`

---

## 📅 Step 2: Daily Returns to Annual Returns

### Formula

To get the **annual return** for a given year, we compound all daily returns:

```
Annual Return = (1 + r₁) × (1 + r₂) × ... × (1 + rₙ) - 1
```

Where:

- `r₁, r₂, ..., rₙ` are daily returns for all trading days in that year
- `n` = number of trading days in the year (~252 days)

### Example

If daily returns for a year are: [0.01, -0.005, 0.02, ...]

```
Annual Return = (1 + 0.01) × (1 - 0.005) × (1 + 0.02) × ... - 1
Annual Return = 1.01 × 0.995 × 1.02 × ... - 1
```

### Python Implementation

```python
# Group by year and compound daily returns
annual_returns = combined_data.groupby('Year')[['DIA', 'SPY', 'QQQ', 'VTI']].apply(
    lambda x: (1 + x).prod() - 1
)
```

---

## 🎯 Step 3: Annual Returns to CAGR

### Formula

The **Compound Annual Growth Rate (CAGR)** between any two years is:

```
CAGR = ((1 + r₁) × (1 + r₂) × ... × (1 + rₙ))^(1/n) - 1
```

Where:

- `r₁, r₂, ..., rₙ` are annual returns for each year in the period
- `n` = number of years in the period

### Alternative Formula (using final/initial values)

```
CAGR = (Final Value / Initial Value)^(1/n) - 1
```

### Example: 3-Year CAGR

**Annual returns:** 2015: 10%, 2016: -5%, 2017: 15%

```
CAGR = ((1 + 0.10) × (1 - 0.05) × (1 + 0.15))^(1/3) - 1
CAGR = (1.10 × 0.95 × 1.15)^(1/3) - 1
CAGR = (1.202)^(0.333) - 1
CAGR = 1.0635 - 1 = 6.35%
```

### Python Implementation

```python
def create_cagr_matrix(annual_returns_series, start_year, end_year):
    period_returns = annual_returns_series.loc[start_year:end_year]
    num_years = len(period_returns)
  
    if num_years == 1:
        # Single year return
        cagr = period_returns.loc[start_year]
    else:
        # Multi-year CAGR
        cumulative_return = (1 + period_returns / 100).prod()
        cagr = (cumulative_return ** (1/num_years) - 1) * 100
  
    return cagr
```

---

## 🧮 Complete Calculation Flow

### Example: SPY from $100 to $200 over 5 years

1. **Daily Returns**: Calculate for each trading day

   ```
   Day 1: (101/100) - 1 = 1.0%
   Day 2: (99/101) - 1 = -1.98%
   ... (continue for ~1,260 trading days)
   ```
2. **Annual Returns**: Compound daily returns for each year

   ```
   2020: 18.33%
   2021: 28.73%
   2022: -18.18%
   2023: 26.18%
   2024: 24.89%
   ```
3. **5-Year CAGR**: Compound the annual returns

   ```
   CAGR = ((1.1833 × 1.2873 × 0.8182 × 1.2618 × 1.2489)^(1/5)) - 1
   CAGR = (2.0)^(0.2) - 1 = 14.87%
   ```

---

## 🔍 Key Points

### Why We Use Daily Returns

- **Precision**: Captures all market movements, not just month-end or year-end prices
- **Compounding**: Properly accounts for reinvestment of gains
- **Market Reality**: Reflects actual trading experience

### Why CAGR is Important

- **Standardization**: Allows comparison across different time periods
- **Smoothing**: Reduces the impact of volatility in individual years
- **Real Returns**: Shows the equivalent constant annual growth rate

### Data Handling

- **Missing Data**: Handled automatically by pandas (NaN values excluded from calculations)
- **Chronological Order**: Critical for proper compounding (data sorted by date)
- **Percentage Conversion**: Results converted to percentages for readability

---

## 📈 Matrix Interpretation

In our CAGR matrix:

- **Rows**: End year of investment period
- **Columns**: Start year of investment period
- **Values**: CAGR for that specific period
- **Diagonal**: Single-year returns (annual returns)
- **Lower Triangle**: Multi-year CAGRs

**Example Reading:**

- Matrix[2024, 2019] = 17.09% means investing in SPY from start of 2019 to end of 2024 gave a 17.09% CAGR
