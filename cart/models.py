from django.db import models
from products.models import Plant
from django.contrib.auth.models import User

# For a simple cart implementation, we'll use a database model
# This is a straightforward approach for a student project
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    session_id = models.CharField(max_length=255, null=True, blank=True)  # For anonymous users
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.quantity} x {self.plant.name}'
    
    def total_price(self):
        return self.quantity * self.plant.price
