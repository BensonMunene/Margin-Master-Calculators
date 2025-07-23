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