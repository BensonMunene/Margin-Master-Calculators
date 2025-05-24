# Margin Master App

## Overview
Margin Master App is a comprehensive, interactive tool for financial traders and investors to calculate, visualize, and analyze margin requirements for leveraged trading. The application provides real-time calculations, interactive visualizations, and stress testing capabilities to help users make informed decisions about margin trading.

## Features
- **Interactive Margin Calculator**: Calculate required margin, buying power, and interest accrual based on investment amount, leverage, and interest rates
- **Dual Margin Comparison**: Visualize both Reg-T and Portfolio margin requirements side-by-side
- **Risk Visualization**: Dynamic gauge showing safety zones for your current margin settings
- **Stress Testing**: Pre-built and custom scenarios to test your positions against historical market conditions
- **Customizable Settings**: Adjust themes, data sources, and notification preferences
- **Export Functionality**: Save and export your calculations and scenarios

## Installation

### Prerequisites
- Python 3.8+
- Pip package manager

### Setup
1. Clone this repository
2. Navigate to the project directory
3. Install required dependencies:
```
pip install -r requirements.txt
```

## Usage
Run the application with:
```
streamlit run "Margin Master App.py"
```

### Sections
1. **Header**: Global controls and app banner
2. **Margin Calculator**: Input your investment details and view real-time calculations
3. **Visualization**: Interactive charts showing margin call scenarios
4. **Stress Testing**: Test your positions against historical scenarios
5. **Settings**: Customize app appearance and behavior

## Project Structure
- `Margin Master App.py`: Main application entry point
- `ui.py`: UI components and styling functions
- `calculations.py`: Core margin calculation logic
- `charts.py`: Plotly-based visualization components
- `utils.py`: Utility functions and helpers

## Data Sources
The app uses historical market data for stress testing scenarios and real-time calculations. You can toggle between local CSV data and external API sources in the settings section.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details. 