# ETF Margin Calculator - Django Edition

This is a Django-based version of the ETF Margin Calculator, recreated from the original Streamlit application. It provides tools for calculating and visualizing margin trading metrics for ETFs like SPY and VTI.

## Features

- **Margin Calculator**: Calculate leverage, margin requirements, and risk metrics
- **Market Overview**: View price charts for major ETFs
- **Price Analysis**: Analyze ETF price movements over custom time periods
- **Dividend Analysis**: Understand how dividend income affects margin positions
- **Kelly Criterion**: Determine optimal position sizes based on probabilities

## Requirements

- Python 3.8+
- Django 5.2
- pandas
- numpy
- plotly
- matplotlib
- seaborn

## Installation

1. Install required packages:
   ```
   pip install -r requirements.txt
   ```

2. Create the database:
   ```
   python manage.py migrate
   ```

3. Run the development server:
   ```
   python manage.py runserver
   ```

4. Access the application at http://127.0.0.1:8000/

## Data Files

The application looks for ETF price and dividend data files in the `Data` directory located in the parent folder. The following files are required:

- `SPY.csv` - Price data for SPY ETF
- `SPY_dividends.csv` - Dividend data for SPY ETF
- `VTI.csv` - Price data for VTI ETF
- `VTI_dividends.csv` - Dividend data for VTI ETF

## Usage

1. Navigate to the main page at http://127.0.0.1:8000/
2. Use the navigation tabs to access different features
3. Input your parameters in the Margin Calculator and click "Calculate"
4. Explore different market scenarios and dividend patterns

## Notes

This application is for educational purposes only and should not be used as the sole basis for investment decisions. Always consult with a financial advisor before engaging in margin trading.
