# Generated by Django 4.0.1 on 2022-11-25 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0020_alter_product_status_alter_productcategory_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productcategory',
            name='image',
            field=models.ImageField(blank=True, upload_to='category-images'),
        ),
    ]
