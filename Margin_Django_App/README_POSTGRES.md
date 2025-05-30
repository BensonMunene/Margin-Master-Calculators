# Migrating to PostgreSQL

This guide will help you migrate your Margin Calculator Django app from SQLite to PostgreSQL.

## Prerequisites

1. Install PostgreSQL on your system if not already installed:
   - Windows: Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
   - During installation, set a password for the postgres user (remember this password!)

2. Make sure you have installed the required Python packages:
   ```
   pip install -r requirements.txt
   ```

## Database Setup

1. Create a PostgreSQL database for the application:
   - Open pgAdmin (installed with PostgreSQL)
   - Right-click on "Databases" and select "Create" → "Database"
   - Name the database `margin_calculator` and save

2. Update the `.env` file with your PostgreSQL credentials:
   ```
   DB_NAME=margin_calculator
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   DB_HOST=localhost
   DB_PORT=5432
   ```

## Run Migrations

1. Run Django migrations to create the database tables:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

## Import Data

1. Import data from CSV files to the PostgreSQL database using the management command:
   ```
   python manage.py import_data --clear
   ```
   
   The `--clear` flag will delete any existing data before importing. Remove this flag if you want to keep existing data.

## Verify the Setup

1. Run the development server:
   ```
   python manage.py runserver
   ```

2. Visit `http://127.0.0.1:8000/` in your browser to ensure the application is working with PostgreSQL.

## Troubleshooting

- If you encounter connection issues, check that:
  - PostgreSQL service is running
  - Database credentials in the `.env` file are correct
  - Database exists and is accessible

- If data is not displaying correctly:
  - Check that the `import_data` command completed successfully
  - Verify that data exists in the database tables using pgAdmin

## Notes

- The application now uses environment variables for configuration, stored in the `.env` file
- The data is now loaded from the database models instead of directly from CSV files
- PostgreSQL provides better performance and scalability than SQLite for production use
