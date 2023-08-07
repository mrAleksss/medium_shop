from django import forms
from .models import Order, Payment


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'delivery_method', 'city', 'delivery_address', 'order_note']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['delivery_method'].widget.attrs.update({'class': 'form-control'})


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['payment_method'].widget.attrs.update({'class': 'form-control'})
