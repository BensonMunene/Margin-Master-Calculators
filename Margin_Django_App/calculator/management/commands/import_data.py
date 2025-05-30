import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
from calculator.models import StockData, DividendData
from django.db import transaction

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATA_DIR = os.path.join(BASE_DIR, 'Data')

class Command(BaseCommand):
    help = 'Import stock and dividend data from CSV files into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data import...'))

        # Check if the Data directory exists
        if not os.path.exists(DATA_DIR):
            raise CommandError(f"Data directory not found: {DATA_DIR}")
            
        # Define file paths
        spy_path = os.path.join(DATA_DIR, 'SPY.csv')
        spy_dividends_path = os.path.join(DATA_DIR, 'SPY Dividends.csv')
        vti_path = os.path.join(DATA_DIR, 'VTI.csv')
        vti_dividends_path = os.path.join(DATA_DIR, 'VTI Dividends.csv')
        
        # Check if files exist
        files_to_check = {
            "SPY price data": spy_path,
            "SPY dividend data": spy_dividends_path,
            "VTI price data": vti_path, 
            "VTI dividend data": vti_dividends_path
        }
        
        for desc, path in files_to_check.items():
            if not os.path.exists(path):
                self.stdout.write(self.style.WARNING(f"{desc} file not found: {path}"))
                return
        
        # Clear existing data if requested
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            with transaction.atomic():
                StockData.objects.all().delete()
                DividendData.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))
        
        # Import SPY price data
        self.import_price_data(spy_path, 'SPY')
        
        # Import VTI price data
        self.import_price_data(vti_path, 'VTI')
        
        # Import SPY dividend data
        self.import_dividend_data(spy_dividends_path, 'SPY')
        
        # Import VTI dividend data
        self.import_dividend_data(vti_dividends_path, 'VTI')
        
        self.stdout.write(self.style.SUCCESS('Data import completed successfully!'))
    
    def import_price_data(self, file_path, symbol):
        self.stdout.write(f'Importing {symbol} price data...')
        try:
            # Read CSV file
            df = pd.read_csv(file_path, parse_dates=['Date'])
            
            # Create StockData objects in bulk
            with transaction.atomic():
                stock_data_objects = [
                    StockData(
                        symbol=symbol,
                        date=row['Date'],
                        open_price=row['Open'],
                        high=row['High'],
                        low=row['Low'],
                        close=row['Close'],
                        volume=row['Volume']
                    )
                    for _, row in df.iterrows()
                ]
                
                # Use bulk create for efficiency
                # Set ignore_conflicts=True to skip duplicates
                StockData.objects.bulk_create(stock_data_objects, batch_size=1000, ignore_conflicts=True)
                
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(df)} {symbol} price records'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing {symbol} price data: {e}'))
    
    def import_dividend_data(self, file_path, symbol):
        self.stdout.write(f'Importing {symbol} dividend data...')
        try:
            # Read CSV file
            df = pd.read_csv(file_path, parse_dates=['Date'])
            
            # Create DividendData objects in bulk
            with transaction.atomic():
                dividend_data_objects = [
                    DividendData(
                        symbol=symbol,
                        date=row['Date'],
                        amount=row['Dividends']
                    )
                    for _, row in df.iterrows()
                ]
                
                # Use bulk create for efficiency
                # Set ignore_conflicts=True to skip duplicates
                DividendData.objects.bulk_create(dividend_data_objects, batch_size=1000, ignore_conflicts=True)
                
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(df)} {symbol} dividend records'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing {symbol} dividend data: {e}'))
