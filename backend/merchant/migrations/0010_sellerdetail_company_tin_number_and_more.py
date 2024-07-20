# Generated by Django 4.0.1 on 2022-10-31 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merchant', '0009_sellerdetail_company_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='sellerdetail',
            name='company_tin_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='sellerdetail',
            name='tin_verified',
            field=models.BooleanField(default=False),
        ),
    ]