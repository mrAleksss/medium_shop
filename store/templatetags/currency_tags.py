from django import template
from djmoney.contrib.exchange.models import convert_money
from store.util import calculate_discounted_price


register = template.Library()


@register.filter
def convert_to_uah(price_in_usd):
    return convert_money(price_in_usd, 'UAH')


@register.filter
def discounted_tag(money_obj):
    return calculate_discounted_price(money_obj)
# def calculate_discounted_price(money_obj):
#     products = Product.objects.all()
    
#     for product in products:
#         price_tiers = PriceTier.objects.filter(product=product).order_by('-discount').first()
#         for tier in price_tiers:
#             if tier:
#                 discounted_price = money_obj * (1-tier.discount / Decimal(100))
#                 discounted_price_in_uah = convert_money(discounted_price, 'UAH')
#                 product.discounted_price_in_uah = discounted_price_in_uah
     
            
            
        
#         return product.discounted_price_in_uah