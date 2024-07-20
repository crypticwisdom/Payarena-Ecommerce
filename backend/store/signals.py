from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from ecommerce.models import Product, ProductCategory, ProductType
from uuid import uuid4


# post signal for generating slug field for the
from store.models import Store


@receiver(post_save, sender=Product)
def create_slug(sender, instance, created, **kwargs):
    if created:
        slug = f"{instance.name.replace(' ', '-')}-{str(uuid4()).replace('-', '')[:8]}{instance.id}"
        instance.slug = slug
        instance.save()


# Incase the name of the product was changed somehow,
# this signal would take care of renaming the Product's slug field.
@receiver(pre_save, sender=Product)
def update_slug(sender, instance, **kwargs):
    if not instance.slug:
        slug = f"{instance.name.replace(' ', '-')}-{str(uuid4()).replace('-', '')[:8]}{instance.id}"
        instance.slug = slug


@receiver(pre_save, sender=Store)
def update_slug(sender, instance, **kwargs):
    if not instance.slug:
        slug = f"{instance.name.replace(' ', '-')}-{str(uuid4()).replace('-', '')[:8]}{instance.id}"
        instance.slug = slug


@receiver(post_save, sender=Store)
def create_slug(sender, instance, created, **kwargs):
    if created:
        slug = f"{instance.name.replace(' ', '-')}-{str(uuid4()).replace('-', '')[:8]}{instance.id}"
        instance.slug = slug
        instance.save()


@receiver(pre_save, sender=Product)
def update_all_product_slug(sender, **kwargs):
    for product in Product.objects.all():
        if not product.slug:
            product.slug = f"{product.name.replace(' ', '-')}-{str(uuid4()).replace('-', '')[:8]}{product.id}"
            product.save()


@receiver(post_save, sender=ProductCategory)
def create_slug(sender, instance, created, **kwargs):
    if created:
        slug = f"{instance.name.replace(' ', '-')}-{str(uuid4()).replace('-', '')[:8]}{instance.id}"
        instance.slug = slug
        instance.save()


@receiver(post_save, sender=ProductType)
def create_slug(sender, instance, created, **kwargs):
    if created:
        slug = f"{instance.name.replace(' ', '-')}-{str(uuid4()).replace('-', '')[:8]}{instance.id}"
        instance.slug = slug
        instance.save()


