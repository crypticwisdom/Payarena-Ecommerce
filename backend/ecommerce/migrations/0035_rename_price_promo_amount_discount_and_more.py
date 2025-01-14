# Generated by Django 4.0.1 on 2023-02-15 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0034_alter_promo_position'),
    ]

    operations = [
        migrations.RenameField(
            model_name='promo',
            old_name='price',
            new_name='amount_discount',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='category_promo',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='discount',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='merchant_promo',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='price_promo',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='product_promo',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='product_type_promo',
        ),
        migrations.RemoveField(
            model_name='promo',
            name='sub_category_promo',
        ),
        migrations.AddField(
            model_name='promo',
            name='fixed_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=50, null=True),
        ),
        migrations.AddField(
            model_name='promo',
            name='percentage_discount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=50, null=True),
        ),
        migrations.AlterField(
            model_name='promo',
            name='discount_type',
            field=models.CharField(choices=[('fixed', 'Fixed Amount'), ('percentage', 'Percentage'), ('amount_off', 'Amount Off')], default='fixed', max_length=50),
        ),
    ]
