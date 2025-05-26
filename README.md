# Financial Analysis and Margin Trading Toolkit

Welcome to the Financial Analysis and Margin Trading Toolkit! This repository hosts a collection of tools and resources designed to assist with financial data analysis, with a particular focus on ETF performance and margin trading strategies.

## Key Components:

*   **Margin Master App**: A comprehensive Streamlit application for detailed margin calculations, risk visualization, and stress testing.
*   **Margin App**: A Streamlit application for visualizing ETF data (SPY, VTI) including price charts and dividend history, along with a basic margin calculator.
*   **Data Preparation Scripts**: Jupyter notebooks for processing and preparing financial data.
*   **Excel Workbooks**: Pre-built Excel calculators for various financial scenarios.
*   **Data**: A collection of CSV and Excel files containing market data for ETFs, Federal Funds rates, etc.

---

## Margin App

The **Margin App** is a Streamlit application designed for analyzing and visualizing Exchange Traded Fund (ETF) data, specifically for SPY (S&P 500 ETF) and VTI (Total Stock Market ETF). It also includes a basic margin calculator.

### Key Features:

*   Visualization of ETF data with candlestick charts.
*   Dividend distribution bar charts.
*   Date range selection for analysis.
*   A margin calculator for investment analysis.
*   Ability to toggle between local and repository data sources.

### Installation:

Ensure you have Python installed. All required Python packages are listed in the main `requirements.txt` file at the root of this repository.

1.  Clone this repository:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Usage:

To run the Margin App:

```bash
streamlit run "Margin App/Margin_App.py"
```

For more detailed information, please see the [Margin App README](./Margin%20App/README.md).

---

## Margin Master App

The **Margin Master App** is a comprehensive, interactive Streamlit application for financial traders and investors to calculate, visualize, and analyze margin requirements for leveraged trading.

### Key Features:

*   **Interactive Margin Calculator**: Calculate required margin, buying power, and interest accrual.
*   **Dual Margin Comparison**: Visualize Reg-T and Portfolio margin requirements side-by-side.
*   **Risk Visualization**: Dynamic gauge showing safety zones for margin settings.
*   **Stress Testing**: Test positions against historical market conditions and custom scenarios.
*   **Customizable Settings**: Adjust themes, data sources, and notification preferences.
*   **Export Functionality**: Save and export calculations and scenarios.

### Installation:

Ensure you have Python installed. All required Python packages are listed in the main `requirements.txt` file at the root of this repository.

1.  Clone this repository:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `Margin Master App` also contains an identical `requirements.txt` specific to it, but the root file covers all common dependencies.)*

### Usage:

To run the Margin Master App:

```bash
streamlit run "Margin Master App/Margin_Master_App.py"
```

For more detailed information, including project structure and specific data source notes, please see the [Margin Master App README](./Margin%20Master%20App/README.md).

---

## Other Components

Beyond the primary Streamlit applications, this repository contains several other useful resources:

*   **`Codes/Data Preparation.ipynb`**: A Jupyter Notebook that likely contains Python scripts for cleaning, transforming, or preparing the financial data used in the applications or analyses.
*   **`Data/`**: This directory stores the raw and processed data files, including:
    *   ETF historical data (SPY, VTI) in CSV format.
    *   Dividend history for these ETFs.
    *   Federal Funds interest rate data.
    *   Various Excel files (`.xlsx`) related to specific datasets.
*   **`Excel workbooks/`**: Contains Microsoft Excel files, such as `WSP-Margin-Call-Price-Calculator_vF.xlsx` and `spy_long.xlsx`, which are likely pre-built calculators or analysis spreadsheets.
*   **`Ben Insights/`**: This folder holds images that might be used in reports, presentations, or as visual aids supporting the analyses conducted within this repository.
*   **`RoadMap.docx` and `margin notes.docx`**: Word documents that appear to contain planning notes, feature roadmaps, or specific details related to the margin tools.

---

## General Project Setup/Installation

To set up the project and run the applications, follow these steps:

1.  **Prerequisites**:
    *   Python 3.8 or higher is recommended.
    *   `pip` (Python package installer).
    *   Git for cloning the repository.

2.  **Clone the Repository**:
    ```bash
    git clone <your_repository_url_here>
    cd <repository_name_here>
    ```
    *(Replace `<your_repository_url_here>` with the actual URL of this repository and `<repository_name_here>` with the directory name if it's different.)*

3.  **Install Dependencies**:
    The main dependencies for the Python-based tools (especially the Streamlit applications) are listed in `requirements.txt` at the root of the repository.
    ```bash
    pip install -r requirements.txt
    ```
    This command will install Streamlit, Pandas, NumPy, Matplotlib, Seaborn, and Plotly, which are used by one or both of the `Margin App` and `Margin Master App`.

4.  **Running the Applications**:
    Refer to the specific "Usage" instructions under the "Margin App" and "Margin Master App" sections above to run each application.

---

## Directory Structure

Here's an overview of the main directories and their purpose within this repository:

```
.
├── Ben Insights/           # Images and visual aids for analyses
├── Codes/                  # Jupyter notebooks (e.g., Data Preparation.ipynb)
├── Data/                   # CSV, Excel, and other data files
├── Excel workbooks/        # Standalone Excel-based calculators and tools
├── Margin App/             # Source code and README for the Margin App
│   ├── Margin_App.py       # Main script for the Margin App
│   ├── README.md           # Detailed README for Margin App
│   └── ...                 # Other supporting files (UI components, visualizations)
├── Margin Master App/      # Source code and README for the Margin Master App
│   ├── Margin_Master_App.py # Main script for the Margin Master App
│   ├── README.md           # Detailed README for Margin Master App
│   └── ...                 # Other supporting files (calculations, UI, charts)
├── README.md               # This main README file
├── requirements.txt        # Root Python dependencies for the Streamlit apps
├── RoadMap.docx            # Project roadmap and planning document
└── margin notes.docx       # Notes related to margin calculations or features
```
*(Note: ... indicates other files and subdirectories within the respective app folders.)*

---

## Contributing

Contributions to this toolkit are welcome. If you have suggestions for improvements, new features, or find any issues, please feel free to:

1.  Open an issue on the repository's issue tracker.
2.  Fork the repository, make your changes, and submit a pull request.

Please ensure that any new code is well-documented and, where applicable, includes relevant tests.

---

## License

This project is licensed under the MIT License. You can find a copy of the license in the `LICENSE`file in this repository. If the `LICENSE` file is not present, the terms of the MIT License still apply.

The MIT License is a permissive free software license originating at the Massachusetts Institute of Technology (MIT). It puts only very limited restrictions on reuse and has, therefore, high license compatibility.
