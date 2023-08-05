from .models import ReviewRating
from django import forms


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ["subject", "review", "rating"]


class PriceRangeForm(forms.Form):
    PRICES = [
        ('', 'Any'),
        (50, '$50'),
        (100, '$100'),
        (150, '$150'),
        (200, '$200'),
        (500, '$500'),
        (1000, '$1000'),
        (2000, '$2000'),
        (5000, '$5000'),
    ]

    min_price = forms.ChoiceField(choices=PRICES, required=False)
    max_price = forms.ChoiceField(choices=PRICES, required=False)