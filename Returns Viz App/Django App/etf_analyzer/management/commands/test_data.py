from django.core.management.base import BaseCommand
from etf_analyzer.utils import load_etf_data


class Command(BaseCommand):
    help = 'Test ETF data loading'

    def handle(self, *args, **options):
        try:
            self.stdout.write('Testing ETF data loading...')
            annual_returns, combined_data = load_etf_data()
            
            self.stdout.write(self.style.SUCCESS('Data loaded successfully!'))
            self.stdout.write(f'Available ETFs: {list(annual_returns.columns)}')
            self.stdout.write(f'Year range: {annual_returns.index.min()} - {annual_returns.index.max()}')
            self.stdout.write(f'Total years: {len(annual_returns)}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading data: {e}'))