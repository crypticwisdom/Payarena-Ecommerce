# Generated by Django 4.0.1 on 2022-11-17 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_remove_profile_wallet_id_profile_pay_auth'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='has_wallet',
            field=models.BooleanField(default=False),
        ),
    ]