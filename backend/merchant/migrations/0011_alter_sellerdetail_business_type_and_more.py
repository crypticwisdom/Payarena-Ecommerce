# Generated by Django 4.0.1 on 2022-11-08 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merchant', '0010_sellerdetail_company_tin_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sellerdetail',
            name='business_type',
            field=models.CharField(blank=True, choices=[('unregistered-individual-business', 'Unregistered Individual Business'), ('registered-individual-business', 'Registered Individual Business'), ('limited-liability-company', 'Limited Liability')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='sellerdetail',
            name='company_type',
            field=models.CharField(blank=True, choices=[('sole-proprietorship', 'Sole-Proprietorship'), ('partnership', 'Partnership / Joint Venture')], max_length=100, null=True),
        ),
    ]
