from django.db import models
from django.db.models import Sum
from accounts.models import Account
from store.models import Product, Variation


class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    delivery_method = models.CharField(max_length=100, choices=[
        ('Самовивіз', 'Самовивіз'), 
        ('Нова Пошта', 'Нова Пошта'), 
        ('Адресна доставка', 'Адресна доставка')], default='Нова пошта')
    city = models.CharField(max_length=50)
    delivery_address = models.CharField(max_length=100)
    order_note = models.CharField(max_length=500, blank=True)
    order_total = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    remaining_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="New")
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Check if any payments have been made for this order
        if not self.payment_set.exists() and self.amount_paid == 0:
            self.remaining_balance = self.order_total
        super().save(*args, **kwargs)


    def update_remaining_balance(self):
        payments = self.payment_set.all()
        total_paid = sum(payment.amount_paid for payment in payments)
        self.remaining_balance = self.order_total - total_paid
        self.save(update_fields=['remaining_balance'])

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def full_address(self):
        return f"{self.city} - {self.delivery_method} - {self.delivery_address}"
    
    def __str__(self):
        return self.order_number
    

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=100, choices=[
        ('Оплата на карту', 'Оплата на карту'), 
        ('Наложенний платіж', 'Наложенний платіж'), 
        ('Готівкою при отриманні', 'Готівкою при отриманні'),], default='Готівкою при отриманні')
    payment_status = models.CharField(max_length=50, choices=[
        ('В очікуванні', 'В очікуванні'),
        ('Оплочено', 'Оплочено'),
        ('Часткова оплата', 'Часткова оплата')
    ], default='В очікуванні')

    def __str__(self):
        return f"{self.payment_date} - {self.amount_paid} - {self.payment_status}"
    
    def save(self, *args, **kwargs):
        super(Payment, self).save(*args, **kwargs)
        self.order.update_remaining_balance()
    

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=14, decimal_places=2)
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.product_name
    
    










