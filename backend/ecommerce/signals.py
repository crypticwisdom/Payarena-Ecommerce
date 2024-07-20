import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from ecommerce.models import Promo


@receiver(signal=post_save, sender=Promo)
def property_post_save(sender, instance, **kwargs):
    property_obj = Promo.objects.filter(id=instance.id)
    if not instance.slug:
        slug = slugify(f"{instance.title}-{instance.id}{str(uuid.uuid4())[:5]}")
        property_obj.update(slug=slug)
