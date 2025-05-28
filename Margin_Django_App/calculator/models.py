from django.db import models
import datetime

class StockData(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    open_price = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()
    
    class Meta:
        unique_together = ('symbol', 'date')
        indexes = [
            models.Index(fields=['symbol', 'date']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.date}"

class DividendData(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    amount = models.FloatField()
    
    class Meta:
        unique_together = ('symbol', 'date')
        indexes = [
            models.Index(fields=['symbol', 'date']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.date} - ${self.amount}"

