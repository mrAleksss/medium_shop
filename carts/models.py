from django.db import models
from django.db.models import Max
from store.models import Product, Variation, PriceTier
from accounts.models import Account

from decimal import Decimal, ROUND_UP, ROUND_DOWN


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id


class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def get_tiers(self):
        return self.product.tier.filter(min_quantity__lte=self.quantity)
    
    @property
    def discounted_price(self):
        tiers = self.get_tiers()
        if tiers:
            max_discount = tiers.aggregate(Max('discount'))['discount__max']
            if max_discount is not None:
                max_discount_tier = tiers.get(discount=max_discount)
                if self.quantity >= max_discount_tier.min_quantity:
                    discounted_price = self.product.price_in_uah.amount * (1 - max_discount / 100)
                    return discounted_price.quantize(Decimal('0.00'), rounding=ROUND_UP)
        return self.product.price_in_uah.amount.quantize(Decimal('0.00'), rounding=ROUND_UP)
    
    @property
    def discounted_total(self):
        return self.discounted_price * self.quantity


    def __unicode__(self):
        return self.product