# Generated by Django 4.0.1 on 2023-07-22 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0004_merchanttransaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='source',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
