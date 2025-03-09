from django.db import models
from django.contrib.auth.models import User
from products.models import Plant
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
        # Ensure a user can only review a plant once
        unique_together = ('user', 'plant')
    
    def __str__(self):
        return f'{self.user.username} - {self.plant.name} - {self.rating} stars'
