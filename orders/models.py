from django.db import models
from django.db.models import Sum
from accounts.models import Account
from store.models import Product, Variation



class Payment(models.Model):
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Partial', 'Partial')
    ], default='Pending')

    def __str__(self):
        return f"{self.order} - {self.amount_paid} - {self.payment_status}"
    
    def update_amount_paid(self):
        payments_total = Payment.objects.filter(order=self.order).exclude(payment_status='Pending').aggregate(total=Sum('amount_paid'))
        total_paid = payments_total['total'] or 0
        self.order.amount_paid = total_paid
        self.order.save()
        self.order.update_remaining_balance()

    def save(self, *args, **kwargs):
        if not self.id:
            self.order.amount_paid += self.amount_paid
            self.order.save()
            self.update_amount_paid()
        super().save(*args, **kwargs)

    

class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )


    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ManyToManyField(Payment)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    order_note = models.CharField(max_length=500, blank=True)
    order_total = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    remaining_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="New")
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_remaining_balance(self):
        self.remaining_balance = self.order_total - self.amount_paid
        self.save()

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2}"
    
    def __str__(self):
        return self.user.first_name
    

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
    
    










