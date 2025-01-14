# Generated by Django 4.0.1 on 2023-01-18 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0029_remove_returnreason_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='promo',
            name='product_type',
            field=models.ManyToManyField(blank=True, to='ecommerce.ProductType'),
        ),
        migrations.AddField(
            model_name='promo',
            name='product_type_promo',
            field=models.BooleanField(default=False, help_text='Select product_type(s) if this is selected'),
        ),
    ]
