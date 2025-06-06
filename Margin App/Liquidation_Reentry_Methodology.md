# 📊 Liquidation-Reentry Backtest Methodology

## Technical Documentation for Leveraged ETF Strategy Analysis

### Executive Summary

The Liquidation-Reentry Backtest is a sophisticated simulation engine that models the realistic dynamics of leveraged ETF trading with margin requirements. Unlike traditional backtests that ignore margin calls, this system simulates forced liquidations, capital constraints, and strategic re-entry timing to provide accurate risk assessment and performance analysis.

**Key Features:**
- Realistic margin call simulation with immediate forced liquidation
- Strategic 2-day cooling period before re-entry (risk management choice)
- Compound capital erosion modeling through multiple liquidation cycles
- Comprehensive interest cost and dividend reinvestment tracking
- Institutional-grade risk analytics and performance attribution

### Mathematical Foundation

#### Core Leverage Mathematics

**Position Sizing Formula:**
```
Total Position Size = Initial Cash × Leverage Multiplier
Margin Loan = Total Position Size - Initial Cash
Shares Purchased = Total Position Size ÷ Current ETF Price
```

**Example with 6.5x Leverage:**
```
Initial Cash: $15,384,615
Leverage: 6.5x
Total Position: $15,384,615 × 6.5 = $100,000,000
Margin Loan: $100,000,000 - $15,384,615 = $84,615,385
Shares (at $400): $100,000,000 ÷ $400 = 250,000 shares
```

#### Margin Call Trigger Calculation

**Maintenance Margin Requirement:**
```
For Portfolio Margin: 15% of portfolio value
For Reg-T Margin: 25% of portfolio value

Liquidation Trigger:
Current Equity < (Portfolio Value × Maintenance Margin %)

Where:
Current Equity = Portfolio Value - Margin Loan
Portfolio Value = Shares Held × Current ETF Price
```

**Critical Price Calculation:**
```
Liquidation Price = Margin Loan ÷ (Shares × (1 - Maintenance Margin %))

Example with Portfolio Margin (15%):
Liquidation Price = $84,615,385 ÷ (250,000 × 0.85) = $399.55
Price Drop to Liquidation = ($400.00 - $399.55) ÷ $400.00 = 0.11%
```

#### Daily Interest Accumulation

**Interest Rate Structure:**
```
Margin Rate = Federal Funds Rate + Broker Spread
Portfolio Margin Spread: Fed Funds + 2.0%
Reg-T Margin Spread: Fed Funds + 1.5%

Daily Interest Cost = Margin Loan × (Annual Rate ÷ 365)
```

### Liquidation-Reentry Process Flow

#### Phase 1: Initial Position Entry

**Capital Allocation:**
```python
def enter_position(current_equity, leverage, etf_price):
    position_value = current_equity * leverage
    shares_held = position_value / etf_price
    margin_loan = position_value - current_equity
    return shares_held, margin_loan, position_value
```

**Daily Monitoring:**
- Daily equity calculation: Portfolio Value - Margin Loan
- Daily interest accrual: Margin Loan × Daily Rate
- Dividend reinvestment: Additional Shares = Dividend ÷ ETF Price
- Maintenance margin check: Equity ≥ Portfolio Value × 15%

#### Phase 2: Liquidation Event

**Liquidation Trigger:**
```python
def check_margin_call(portfolio_value, margin_loan, maintenance_pct):
    current_equity = portfolio_value - margin_loan
    required_equity = portfolio_value * maintenance_pct
    return current_equity < required_equity
```

**Liquidation Execution:**
```python
def execute_liquidation(shares_held, current_price, margin_loan):
    gross_proceeds = shares_held * current_price
    net_equity = gross_proceeds - margin_loan
    return net_equity
```

#### Phase 3: Strategic Cooling Period

**2-Day Wait Implementation:**
```python
def cooling_period(liquidation_date):
    wait_days = 2  # Strategic choice for risk management
    earliest_reentry = liquidation_date + timedelta(days=wait_days)
    return earliest_reentry
```

**Strategic Rationale:**
- Volatility cooling: Allows market volatility to subside
- Emotional reset: Prevents impulsive immediate re-entry
- Technical analysis: Time to reassess market conditions
- Risk management: Avoids chasing momentum into further losses

#### Phase 4: Position Re-Entry

**Re-Entry Conditions:**
```python
def can_reenter(current_equity, min_threshold=1000):
    return current_equity >= min_threshold
```

### Chart Analysis Guide

#### Chart 1: Equity Evolution & Liquidation Events

**Primary Blue Line - Equity Trajectory:**
```
Daily_Equity(t) = Shares(t) × Price(t) - Margin_Loan(t)
```

**Visual Elements:**
- Red Triangles (▼): Liquidation events showing exact loss amounts
- Green Triangles (▲): Re-entry events with reduced capital
- Line Discontinuities: Represent forced exits and strategic re-entries

#### Chart 2: Position Status Timeline

**Color-Coded Status Indicators:**
```
Green Dots: Active leveraged position (at risk)
Red Dots: Liquidation day (loss realization)
Orange Dots: Cooling period (strategic wait)
Blue Dots: Re-entry day (new position establishment)
Gray Dots: Insufficient capital (strategy termination)
```

#### Chart 3: Drawdown Analysis

**Drawdown Calculation:**
```
Running_Max(t) = max(Equity(0) to Equity(t))
Drawdown(t) = (Equity(t) - Running_Max(t)) ÷ Running_Max(t) × 100
```

**Recovery Mathematics:**
```
To recover from 50% loss: need 100% gain
To recover from 60% loss: need 150% gain
To recover from 80% loss: need 400% gain
```

### Performance Metrics

#### Core Performance Indicators

**Total Return:**
```
Total Return = (Final Equity - Initial Cash) ÷ Initial Cash × 100
CAGR = ((Final ÷ Initial)^(1/Years) - 1) × 100
```

**Risk-Adjusted Returns:**
```
Sharpe Ratio = (Portfolio Return - Risk Free Rate) ÷ Portfolio Volatility
Sortino Ratio = (Portfolio Return - Risk Free Rate) ÷ Downside Volatility
```

### Results Interpretation

#### Success Indicators
```
✓ Total Return > 0%
✓ Liquidation Rate < 30%
✓ Average Survival > 180 days
✓ Sharpe Ratio > 0.5
✓ Max Drawdown < 50%
```

#### Warning Signals
```
⚠ Liquidation Rate 30-70%
⚠ Average Survival 30-180 days
⚠ Sharpe Ratio 0-0.5
⚠ Max Drawdown 50-80%
```

#### Critical Risk Levels
```
🚨 Liquidation Rate > 70%
🚨 Average Survival < 30 days
🚨 Sharpe Ratio < 0
🚨 Max Drawdown > 80%
🚨 Total Return < -50%
```

### User Guide for New Users

#### Step 1: Run Your First Backtest
1. Select ETF (SPY or VTI)
2. Choose modest leverage (2-3x for beginners)
3. Set reasonable start date (2010 or later)
4. Review initial position summary before running

#### Step 2: Interpret Main Equity Chart
- Blue line going up: Strategy is working
- Red triangles: You lost money and got liquidated
- Green triangles: You re-entered with less capital
- Flat periods: Cooling period (strategic wait)

#### Step 3: Check Key Metrics
- Total Return: Did you make or lose money overall?
- Total Liquidations: How many times did you get forced out?
- Max Drawdown: What's the worst loss you experienced?
- Time in Market: What percentage of time were you invested?

#### Step 4: Risk Assessment
- If liquidation rate > 50%, reduce leverage significantly
- If max drawdown > 60%, strategy may be too risky
- If negative total return, consider different approach

### Conclusion

This methodology provides a comprehensive framework for realistic leveraged trading simulation. By incorporating margin call mechanics, strategic cooling periods, and compound capital effects, the system delivers institutional-grade analysis for professional risk assessment and strategy development.

---

*Professional Documentation | Institutional Standards | Quantitative Risk Analysis* 