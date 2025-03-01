# Generated by Django 4.0.1 on 2022-11-09 13:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ecommerce', '0013_returnreason_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnedProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('success', 'Success'), ('failed', 'Failed'), ('rejected', 'Rejected')], default='pending', max_length=50, null=True)),
                ('payment_status', models.CharField(blank=True, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('success', 'Success'), ('failed', 'Failed'), ('rejected', 'Rejected')], default='pending', max_length=50, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ecommerce.orderproduct')),
                ('reason', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='ecommerce.returnreason')),
                ('returned_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updated_by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReturnProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_primary', models.BooleanField(default=False)),
                ('return_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ecommerce.returnedproduct')),
            ],
        ),
        migrations.AddIndex(
            model_name='returnedproduct',
            index=models.Index(fields=['status', 'payment_status', 'created_on', 'updated_on'], name='ecommerce_r_status_ca3888_idx'),
        ),
    ]
