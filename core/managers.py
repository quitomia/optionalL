from django.db import models

class AvailableItemManager(models.Manager):
    def available(self):
        return self.filter(stock__gt=0)
    
    def in_stock(self):
        return self.filter(stock__gt=0).order_by('-created_at')
    
    def with_low_stock(self, threshold=5):
        return self.filter(stock__lte=threshold, stock__gt=0)