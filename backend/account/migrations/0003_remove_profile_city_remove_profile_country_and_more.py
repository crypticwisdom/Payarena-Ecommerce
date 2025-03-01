# Generated by Django 4.0.1 on 2022-10-11 10:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_alter_forgotpasswordotp_expire_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='city',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='country',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='home_address',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='state',
        ),
        migrations.RemoveField(
            model_name='usercard',
            name='email',
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('work', 'Work'), ('home', 'Home'), ('other', 'Other')], default='home', max_length=10)),
                ('name', models.CharField(max_length=500)),
                ('mobile_number', models.CharField(max_length=17)),
                ('num', models.CharField(max_length=500)),
                ('locality', models.CharField(blank=True, max_length=500, null=True)),
                ('landmark', models.CharField(blank=True, max_length=500, null=True)),
                ('country', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('town', models.CharField(blank=True, max_length=100, null=True)),
                ('postal_code', models.CharField(blank=True, default=0, max_length=50, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.profile')),
            ],
        ),
    ]
