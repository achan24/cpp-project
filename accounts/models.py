from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address_line1 = models.CharField(max_length=250, blank=True)
    address_line2 = models.CharField(max_length=250, blank=True)
    town_or_city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=50, choices=COUNTY_CHOICES, blank=True)
    eircode = models.CharField(max_length=8, blank=True, help_text='Format: A65 F4E2')
    phone = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f'Profile for {self.user.username}'
