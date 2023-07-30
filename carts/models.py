from django.db import models
from store.models import Product, Variation, PriceTier
from accounts.models import Account


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

    def get_tier(self):
        try:
            return PriceTier.objects.get(product=self.product, min_quantity__lte=self.quantity)
        except PriceTier.DoesNotExist:
            return None
      
    @property
    def discounted_price(self):
        tier = self.get_tier()
        if tier:
            return self.product.price * (1 - tier.discount/100)
        else:
            return self.product.price


    def sub_total(self):
        return self.product.price * self.quantity

    def __unicode__(self):
        return self.product