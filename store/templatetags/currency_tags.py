from django import template
from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money
from ..models import Product, PriceTier
from decimal import Decimal


register = template.Library()


@register.filter
def convert_to_uah(price_in_usd):
    return convert_money(price_in_usd, 'UAH')


@register.filter
def calculate_discounted_price(product):
    try:
        price_tiers = PriceTier.objects.filter(product=product).order_by('-discount')
        discounted_price = product.price
        for tier in price_tiers:
            if quantity >= tier.min_quantity:
                discounted_price = product.price * (1-tier.discount / Decimal(100))
        return discounted_price
    except AttributeError:
        return product.price
    