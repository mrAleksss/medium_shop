from django.dispatch import receiver
from django.db.models.signals import pre_save
from .models import Product, Rate_to_uah


@receiver(pre_save, sender=Product)
def update_price_in_uah(sender, instance, **kwargs):
    # Get the latest exchange rate USD to UAH
    try:
        rate = Rate_to_uah.objects.latest('id')
        usd_to_uah_rate = rate.usd_to_uah_rate
    except Rate_to_uah.DoesNotExist:
        # Default exchange rate if rate is not available
        usd_to_uah_rate = 40

    if instance.price:
        instance.price_in_uah = instance.price * usd_to_uah_rate
    else:
        instance.price_in_uah = None
