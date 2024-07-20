# Generated by Django 4.0.1 on 2023-01-27 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0032_dailydeal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='status',
            field=models.CharField(choices=[('cancelled', 'Cancelled'), ('processed', 'Processed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('returned', 'Returned'), ('paid', 'Paid'), ('refunded', 'Refunded'), ('pending', 'Pending')], default='paid', max_length=50),
        ),
    ]