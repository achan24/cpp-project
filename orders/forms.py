from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone',
                  'address_line1', 'address_line2', 'town_or_city', 
                  'county', 'eircode']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add placeholders and classes to form fields
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Last Name'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email Address'})
        self.fields['phone'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Phone Number'})
        self.fields['address_line1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Address Line 1'})
        self.fields['address_line2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Address Line 2 (Optional)'})
        self.fields['town_or_city'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Town or City'})
        self.fields['county'].widget.attrs.update({'class': 'form-control'})
        self.fields['eircode'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Eircode (Optional)'})
        self.fields['eircode'].required = False
