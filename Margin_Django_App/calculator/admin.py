from django.contrib import admin
from .models import StockData, DividendData

# Register your models here.
admin.site.register(StockData)
admin.site.register(DividendData)
