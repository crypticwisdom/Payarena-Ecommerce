# Generated by Django 4.0.1 on 2022-09-26 13:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('location', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Seller',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.CharField(blank=True, max_length=100, null=True)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='seller-profile-picture')),
                ('status', models.CharField(blank=True, choices=[('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending')], default='pending', max_length=20, null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='location.city')),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='location.country')),
                ('state', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='location.state')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SellerVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_card', models.ImageField(blank=True, null=True, upload_to='seller-verification')),
                ('id_card_verified', models.BooleanField(default=False)),
                ('cac_number', models.CharField(blank=True, max_length=15, null=True)),
                ('cac_verified', models.BooleanField(default=False)),
                ('verified', models.BooleanField(default=False)),
                ('created_on', models.DateField(auto_now_add=True)),
                ('updated_on', models.DateField(auto_now=True)),
                ('seller', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='merchant.seller')),
            ],
        ),
        migrations.CreateModel(
            name='SellerFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='seller-files')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='merchant.seller')),
            ],
        ),
    ]