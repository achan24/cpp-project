from django.db import models
from django.contrib.auth.models import User
from products.models import Plant

# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    COUNTY_CHOICES = [
        ('antrim', 'Antrim'),
        ('armagh', 'Armagh'),
        ('carlow', 'Carlow'),
        ('cavan', 'Cavan'),
        ('clare', 'Clare'),
        ('cork', 'Cork'),
        ('derry', 'Derry'),
        ('donegal', 'Donegal'),
        ('down', 'Down'),
        ('dublin', 'Dublin'),
        ('fermanagh', 'Fermanagh'),
        ('galway', 'Galway'),
        ('kerry', 'Kerry'),
        ('kildare', 'Kildare'),
        ('kilkenny', 'Kilkenny'),
        ('laois', 'Laois'),
        ('leitrim', 'Leitrim'),
        ('limerick', 'Limerick'),
        ('longford', 'Longford'),
        ('louth', 'Louth'),
        ('mayo', 'Mayo'),
        ('meath', 'Meath'),
        ('monaghan', 'Monaghan'),
        ('offaly', 'Offaly'),
        ('roscommon', 'Roscommon'),
        ('sligo', 'Sligo'),
        ('tipperary', 'Tipperary'),
        ('tyrone', 'Tyrone'),
        ('waterford', 'Waterford'),
        ('westmeath', 'Westmeath'),
        ('wexford', 'Wexford'),
        ('wicklow', 'Wicklow'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    town_or_city = models.CharField(max_length=100)
    county = models.CharField(max_length=50, choices=COUNTY_CHOICES)
    eircode = models.CharField(max_length=8)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return f'Order {self.id} - {self.first_name} {self.last_name}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f'{self.quantity} x {self.plant.name} in Order {self.order.id}'
    
    def get_total_price(self):
        return self.price * self.quantity
