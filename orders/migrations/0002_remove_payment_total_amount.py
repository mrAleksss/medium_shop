# Generated by Django 4.2.4 on 2023-08-07 11:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='total_amount',
        ),
    ]
