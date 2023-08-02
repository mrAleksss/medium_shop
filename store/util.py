import random
from djmoney.contrib.exchange.models import convert_money

from decimal import Decimal


size = 5
available_numbers = [x for x in range(10)]

def generate_product_number():
            new_number_list = [str(random.choice(available_numbers)) for _ in range(size)]
            new_number_str = "".join(new_number_list)
          
            return new_number_str


def calculate_discounted_price(money_obj):
        from .models import Product, PriceTier
        try:
            products = Product.objects.all()
            for product in products:
                price_tiers = PriceTier.objects.filter(product=product).order_by('-discount')
                for tier in price_tiers:
                  if tier:
                      discounted_price = money_obj * (1-tier.discount / Decimal(100))
                      discounted_price_in_uah = convert_money(discounted_price, 'UAH')
                      product.discounted_price_in_uah = discounted_price_in_uah
                  else:
                      product.price = convert_money(money_obj, 'UAH')
            return product.discounted_price_in_uah
      
        except AttributeError:
              return convert_money(money_obj, 'EUR')


