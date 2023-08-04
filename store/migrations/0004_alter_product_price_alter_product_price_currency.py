# Generated by Django 4.2.3 on 2023-08-04 09:28

from django.db import migrations
import djmoney.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_alter_product_price_alter_product_price_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=djmoney.models.fields.MoneyField(decimal_places=2, max_digits=14),
        ),
        migrations.AlterField(
            model_name='product',
            name='price_currency',
            field=djmoney.models.fields.CurrencyField(choices=[('UAH', 'UAH'), ('USD', 'USD $')], default='USD', editable=False, max_length=3),
        ),
    ]