from django.db import models
from ecommerce.models import ProductCategory
from merchant.models import Seller


class Store(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='seller')
    slug = models.CharField(max_length=500, null=True, blank=True, editable=False)
    name = models.CharField(max_length=100, null=True, blank=True)
    logo = models.ImageField(upload_to='store-logo')
    description = models.TextField()
    categories = models.ManyToManyField(ProductCategory)
    is_active = models.BooleanField(default=False)
    on_sale = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.seller} - {self.name}"


