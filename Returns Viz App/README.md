# Returns Visualization App

A professional Streamlit application for analyzing ETF performance with interactive CAGR (Compound Annual Growth Rate) heatmaps.

## Features

- Interactive CAGR heatmaps for SPY, QQQ, DIA, and VTI
- Professional financial dashboard design
- Customizable time period analysis
- ETF performance comparison
- Export functionality for analysis results

## Installation

1. Clone the repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install streamlit pandas numpy plotly
   ```

## Usage

1. Navigate to the `Visualization app` directory:
   ```bash
   cd "Returns Viz App/Visualization app"
   ```

2. Run the Streamlit app:
   ```bash
   streamlit run "Returns Viz App.py"
   ```

## File Structure

```
Returns Viz App/
├── Visualization app/
│   └── Returns Viz App.py  (main application)
├── Historical Data/
│   ├── DIA.csv
│   ├── SPY.csv
│   ├── QQQ.csv
│   └── VTI.csv
├── requirements.txt
└── README.md (this file)
```

## Data Requirements

The application expects CSV files with the following columns:
- `Date`: Date in a format pandas can parse
- `Adj Close`: Adjusted closing price

## About

Created by Pearson Creek Capital LLC for professional ETF performance analysis and investment research.

*This analysis is for informational purposes only and does not constitute investment advice.* 