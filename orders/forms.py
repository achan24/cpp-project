from django import forms
from .models import Order
from eircode_pkg import EircodeValidator

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
        
    def clean_eircode(self):
        """
        Validate the Eircode using the eircode-validator-24203203 package.
        """
        eircode = self.cleaned_data.get('eircode')
        validator = EircodeValidator(allow_empty=True)
        is_valid, error_message = validator.validate(eircode)
        
        if not is_valid:
            raise forms.ValidationError(error_message)
            
        # Format the Eircode properly if it's valid
        if eircode:
            eircode = validator.format(eircode)
            
        return eircode
