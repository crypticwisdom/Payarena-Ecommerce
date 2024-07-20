# Generated by Django 4.0.1 on 2022-12-01 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_profile_wallet_pin'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='billing_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='billing_verified',
            field=models.BooleanField(default=False),
        ),
    ]