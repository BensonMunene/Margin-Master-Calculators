# PowerShell script to migrate from SQLite to PostgreSQL

Write-Host "Starting migration to PostgreSQL..." -ForegroundColor Green

# 1. Check for PostgreSQL
$pgCmd = Get-Command psql -ErrorAction SilentlyContinue
if (-not $pgCmd) {
    Write-Host "Error: PostgreSQL is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install PostgreSQL from https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit 1
}

# 2. Confirm that .env file exists
if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found" -ForegroundColor Red
    Write-Host "Please make sure you have created the .env file with database credentials" -ForegroundColor Yellow
    exit 1
}

# 3. Install required packages
Write-Host "Installing required packages..." -ForegroundColor Blue
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing requirements" -ForegroundColor Red
    exit 1
}

# 4. Run migrations
Write-Host "Running migrations..." -ForegroundColor Blue
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error creating migrations" -ForegroundColor Red
    exit 1
}

python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error applying migrations" -ForegroundColor Red
    exit 1
}

# 5. Import data
Write-Host "Importing data from CSV files into PostgreSQL..." -ForegroundColor Blue
$importChoice = Read-Host "Would you like to clear existing data before importing? (y/n)"
if ($importChoice -eq "y") {
    python manage.py import_data --clear
} else {
    python manage.py import_data
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error importing data" -ForegroundColor Red
    exit 1
}

Write-Host "Migration completed successfully!" -ForegroundColor Green
Write-Host "You can now run 'python manage.py runserver' to start the application with PostgreSQL" -ForegroundColor Green
