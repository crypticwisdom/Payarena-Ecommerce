# Generated by Django 4.0.1 on 2023-02-20 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0035_rename_price_promo_amount_discount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.CharField(blank=True, editable=False, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='slug',
            field=models.CharField(blank=True, editable=False, max_length=500, null=True),
        ),
    ]
