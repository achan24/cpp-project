from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    """
    Form for users to create or edit a review for a product they've purchased.
    """
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(
                attrs={'class': 'star-rating-input'},
                choices=[(5, '5'), (4, '4'), (3, '3'), (2, '2'), (1, '1')]
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Share your thoughts about this plant...'
                }
            ),
        }
        labels = {
            'rating': 'Your Rating',
            'comment': 'Your Review',
        }
