# Generated by Django 4.0.1 on 2022-12-05 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0025_remove_order_receiver_town_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='decline_reason',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending'), ('declined', 'Declined'), ('checked', 'Checked')], default='pending', max_length=10),
        ),
    ]
