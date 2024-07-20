# Generated by Django 4.0.1 on 2022-12-23 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merchant', '0018_seller_approved_by_seller_checked_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seller',
            name='latitude',
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
        migrations.AlterField(
            model_name='seller',
            name='longitude',
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
    ]