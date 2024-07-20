# Generated by Django 4.0.1 on 2022-10-17 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merchant', '0002_remove_seller_city_remove_seller_country_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='seller',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='seller',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='seller',
            name='town',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]