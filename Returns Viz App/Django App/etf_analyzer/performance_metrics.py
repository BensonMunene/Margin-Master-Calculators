import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PerformanceMetrics:
    """Comprehensive performance metrics calculator for financial assets"""
    
    def __init__(self, daily_returns: pd.Series, benchmark_returns: Optional[pd.Series] = None, risk_free_rate: float = 0.02):
        """
        Initialize with daily returns data
        
        Args:
            daily_returns: Series of daily returns (as decimals, not percentages)
            benchmark_returns: Series of daily benchmark returns (optional, for relative metrics)
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.daily_returns = daily_returns.dropna()
        self.benchmark_returns = benchmark_returns.dropna() if benchmark_returns is not None else None
        self.risk_free_rate = risk_free_rate
        self.daily_rf_rate = (1 + risk_free_rate) ** (1/252) - 1  # Convert to daily
        
        # Calculate basic statistics
        self.total_return = (1 + self.daily_returns).prod() - 1
        self.num_years = len(self.daily_returns) / 252
        self.annual_returns = self._calculate_annual_returns()
        
    def _calculate_annual_returns(self) -> pd.Series:
        """Calculate annual returns from daily returns"""
        df = pd.DataFrame({'returns': self.daily_returns})
        df['year'] = df.index.year
        annual_returns = df.groupby('year')['returns'].apply(lambda x: (1 + x).prod() - 1)
        return annual_returns
    
    def cagr(self) -> float:
        """Compound Annual Growth Rate"""
        if self.num_years <= 0:
            return 0.0
        return (1 + self.total_return) ** (1 / self.num_years) - 1
    
    def simple_annualized_return(self) -> float:
        """Simple Annualized Return (Total Return ÷ Number of Years)"""
        if self.num_years <= 0:
            return 0.0
        return self.total_return / self.num_years
    
    def volatility(self, annualized: bool = True) -> float:
        """Volatility (standard deviation of returns)"""
        vol = self.daily_returns.std()
        return vol * np.sqrt(252) if annualized else vol
    
    def sharpe_ratio(self) -> float:
        """Sharpe Ratio (risk-adjusted return)"""
        excess_return = self.cagr() - self.risk_free_rate
        return excess_return / self.volatility() if self.volatility() > 0 else 0.0
    
    def sortino_ratio(self) -> float:
        """Sortino Ratio (downside deviation adjusted return)"""
        excess_return = self.cagr() - self.risk_free_rate
        downside_returns = self.daily_returns[self.daily_returns < self.daily_rf_rate]
        if len(downside_returns) == 0:
            return float('inf')
        downside_deviation = downside_returns.std() * np.sqrt(252)
        return excess_return / downside_deviation if downside_deviation > 0 else 0.0
    
    def maximum_drawdown(self) -> Dict[str, float]:
        """Maximum Drawdown and related metrics"""
        cumulative = (1 + self.daily_returns).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative / peak) - 1
        
        max_dd = drawdown.min()
        max_dd_start = drawdown.idxmin()
        
        # Find the peak before the maximum drawdown
        peak_before_dd = peak.loc[:max_dd_start].idxmax()
        
        # Find recovery point (first time we reach peak again after max DD)
        recovery_point = None
        peak_value = peak.loc[max_dd_start]
        after_dd = cumulative.loc[max_dd_start:]
        recovery_mask = after_dd >= peak_value
        if recovery_mask.any():
            recovery_point = after_dd[recovery_mask].index[0]
            recovery_days = (recovery_point - max_dd_start).days
        else:
            recovery_days = None  # Still in drawdown
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_start': peak_before_dd,
            'max_drawdown_end': max_dd_start,
            'recovery_point': recovery_point,
            'recovery_days': recovery_days
        }
    
    def calmar_ratio(self) -> float:
        """Calmar Ratio (CAGR / Max Drawdown)"""
        max_dd = abs(self.maximum_drawdown()['max_drawdown'])
        return self.cagr() / max_dd if max_dd > 0 else 0.0
    
    def value_at_risk(self, confidence: float = 0.05) -> float:
        """Value at Risk (VaR) at given confidence level"""
        return np.percentile(self.daily_returns, confidence * 100)
    
    def conditional_var(self, confidence: float = 0.05) -> float:
        """Conditional Value at Risk (Expected Shortfall)"""
        var = self.value_at_risk(confidence)
        return self.daily_returns[self.daily_returns <= var].mean()
    
    def skewness(self) -> float:
        """Skewness of returns"""
        return stats.skew(self.daily_returns)
    
    def kurtosis(self) -> float:
        """Kurtosis of returns"""
        return stats.kurtosis(self.daily_returns)
    
    def win_rate(self) -> float:
        """Percentage of positive return periods"""
        positive_returns = (self.annual_returns > 0).sum()
        total_periods = len(self.annual_returns)
        return positive_returns / total_periods if total_periods > 0 else 0.0
    
    def best_year(self) -> Dict[str, float]:
        """Best performing year"""
        if len(self.annual_returns) == 0:
            return {'year': None, 'return': 0.0}
        best_idx = self.annual_returns.idxmax()
        return {'year': best_idx, 'return': self.annual_returns.loc[best_idx]}
    
    def worst_year(self) -> Dict[str, float]:
        """Worst performing year"""
        if len(self.annual_returns) == 0:
            return {'year': None, 'return': 0.0}
        worst_idx = self.annual_returns.idxmin()
        return {'year': worst_idx, 'return': self.annual_returns.loc[worst_idx]}
    
    def average_up_year(self) -> float:
        """Average return in positive years"""
        positive_years = self.annual_returns[self.annual_returns > 0]
        return positive_years.mean() if len(positive_years) > 0 else 0.0
    
    def average_down_year(self) -> float:
        """Average return in negative years"""
        negative_years = self.annual_returns[self.annual_returns < 0]
        return negative_years.mean() if len(negative_years) > 0 else 0.0
    
    def pain_index(self) -> float:
        """Pain Index (average drawdown)"""
        cumulative = (1 + self.daily_returns).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative / peak) - 1
        return abs(drawdown.mean())
    
    def ulcer_index(self) -> float:
        """Ulcer Index (RMS of drawdowns)"""
        cumulative = (1 + self.daily_returns).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative / peak) - 1
        return np.sqrt((drawdown ** 2).mean())
    
    def beta(self) -> float:
        """Beta relative to benchmark"""
        if self.benchmark_returns is None or len(self.benchmark_returns) == 0:
            return None
        
        # Align the two series
        aligned = pd.DataFrame({
            'asset': self.daily_returns,
            'benchmark': self.benchmark_returns
        }).dropna()
        
        if len(aligned) < 2:
            return None
            
        covariance = aligned['asset'].cov(aligned['benchmark'])
        benchmark_variance = aligned['benchmark'].var()
        
        return covariance / benchmark_variance if benchmark_variance > 0 else None
    
    def alpha(self) -> float:
        """Jensen's Alpha relative to benchmark"""
        beta_val = self.beta()
        if beta_val is None or self.benchmark_returns is None:
            return None
        
        benchmark_cagr = (1 + self.benchmark_returns).prod() ** (252 / len(self.benchmark_returns)) - 1
        expected_return = self.risk_free_rate + beta_val * (benchmark_cagr - self.risk_free_rate)
        
        return self.cagr() - expected_return
    
    def r_squared(self) -> float:
        """R-squared relative to benchmark"""
        if self.benchmark_returns is None:
            return None
        
        # Align the two series
        aligned = pd.DataFrame({
            'asset': self.daily_returns,
            'benchmark': self.benchmark_returns
        }).dropna()
        
        if len(aligned) < 2:
            return None
        
        correlation = aligned['asset'].corr(aligned['benchmark'])
        return correlation ** 2 if not pd.isna(correlation) else None
    
    def treynor_ratio(self) -> float:
        """Treynor Ratio (excess return per unit of systematic risk)"""
        beta_val = self.beta()
        if beta_val is None or beta_val == 0:
            return None
        
        excess_return = self.cagr() - self.risk_free_rate
        return excess_return / beta_val
    
    def information_ratio(self) -> float:
        """Information Ratio (tracking error adjusted excess return)"""
        if self.benchmark_returns is None:
            return None
        
        # Align the two series
        aligned = pd.DataFrame({
            'asset': self.daily_returns,
            'benchmark': self.benchmark_returns
        }).dropna()
        
        if len(aligned) < 2:
            return None
        
        excess_returns = aligned['asset'] - aligned['benchmark']
        tracking_error = excess_returns.std() * np.sqrt(252)
        
        if tracking_error == 0:
            return None
        
        excess_return = self.cagr() - ((1 + self.benchmark_returns).prod() ** (252 / len(self.benchmark_returns)) - 1)
        return excess_return / tracking_error
    
    def get_all_metrics(self) -> Dict[str, any]:
        """Get all performance metrics as a dictionary"""
        dd_metrics = self.maximum_drawdown()
        best = self.best_year()
        worst = self.worst_year()
        
        metrics = {
            # Return Metrics
            'cagr': self.cagr(),
            'total_return': self.total_return,
            'simple_annualized': self.simple_annualized_return(),
            'annualized_return': self.cagr(),
            
            # Risk Metrics
            'volatility': self.volatility(),
            'maximum_drawdown': dd_metrics['max_drawdown'],
            'recovery_days': dd_metrics['recovery_days'],
            'pain_index': self.pain_index(),
            'ulcer_index': self.ulcer_index(),
            'var_5': self.value_at_risk(0.05),
            'cvar_5': self.conditional_var(0.05),
            
            # Risk-Adjusted Returns
            'sharpe_ratio': self.sharpe_ratio(),
            'sortino_ratio': self.sortino_ratio(),
            'calmar_ratio': self.calmar_ratio(),
            
            # Distribution Metrics
            'skewness': self.skewness(),
            'kurtosis': self.kurtosis(),
            
            # Period Analysis
            'win_rate': self.win_rate(),
            'best_year': best['return'],
            'best_year_date': best['year'],
            'worst_year': worst['return'],
            'worst_year_date': worst['year'],
            'average_up_year': self.average_up_year(),
            'average_down_year': self.average_down_year(),
            
            # Relative Metrics (vs benchmark)
            'beta': self.beta(),
            'alpha': self.alpha(),
            'r_squared': self.r_squared(),
            'treynor_ratio': self.treynor_ratio(),
            'information_ratio': self.information_ratio(),
            
            # Additional Info
            'num_years': self.num_years,
            'num_observations': len(self.daily_returns)
        }
        
        return metrics


def calculate_performance_metrics(daily_returns: pd.Series, benchmark_returns: Optional[pd.Series] = None) -> Dict[str, any]:
    """
    Convenience function to calculate all performance metrics
    
    Args:
        daily_returns: Series of daily returns (as decimals)
        benchmark_returns: Optional benchmark returns for relative metrics
        
    Returns:
        Dictionary of all performance metrics
    """
    calculator = PerformanceMetrics(daily_returns, benchmark_returns)
    return calculator.get_all_metrics()