from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear all cached data'

    def handle(self, *args, **options):
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Cache cleared successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error clearing cache: {e}'))