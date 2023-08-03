from django import template
from djmoney.contrib.exchange.models import convert_money
from store.util import calculate_discounted_price


register = template.Library()


@register.filter
def convert_to_uah(price_in_usd):
    return convert_money(price_in_usd, 'UAH')



