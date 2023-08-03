import random
from djmoney.contrib.exchange.models import convert_money

from decimal import Decimal
from django.db.models import Max


size = 5
available_numbers = [x for x in range(10)]

def generate_product_number():
            new_number_list = [str(random.choice(available_numbers)) for _ in range(size)]
            new_number_str = "".join(new_number_list)
          
            return new_number_str

    
    


