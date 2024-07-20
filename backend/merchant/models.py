from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
# from location.models import City, State, Country
from .choices import *


# token = Token.objects.create(user=User.objects.get(pk=1))
# print(token.key)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


COMPANY_TYPE = (
    ('sole-proprietorship', 'Sole-Proprietorship'),
    # Frontend should only send 'partnership' for 'partnership / Joint Venture'
    ('partnership', 'Partnership / Joint Venture'),
)

BUSINESS_TYPES = (
    ('unregistered-individual-business', 'Unregistered Individual Business'),
    ('registered-individual-business', 'Registered Individual Business'),
    ('limited-liability-company', 'Limited Liability'),
)

# BANNER_SIZE_CHOICES = (
#     ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')
# ) # Used by MerchantBanner model.

FEP_TYPE_CHOICES = (
    ('flat', "Flat"), ('rate', 'Rate')
)


class Seller(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    merchant_id = models.CharField(max_length=100, null=True, blank=True)
    biller_code = models.CharField(max_length=200, null=True, blank=True)
    fep_type = models.CharField(max_length=50, choices=FEP_TYPE_CHOICES, default="flat")
    feel = models.CharField(max_length=200, null=True, blank=True)
    town = models.CharField(max_length=100, null=True, blank=True)
    town_id = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True, default=0.0)
    latitude = models.FloatField(null=True, blank=True, default=0.0)
    profile_picture = models.ImageField(null=True, blank=True, upload_to='seller-profile-picture')
    status = models.CharField(max_length=20, choices=seller_status_choices, default='pending', null=True, blank=True)
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="checked_by")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="approved_by")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user}-{self.phone_number}: {self.status}'

    def get_full_address(self):
        addr = ""
        if self.address:
            addr += f"{self.address}, "
        if self.town:
            addr += f"{self.town}, "
        if self.city:
            addr += f"{self.city}, "
        if self.state:
            addr += f"{self.state}, "
        return addr.strip()


class Director(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.phone_number}"


class SellerDetail(models.Model):
    seller = models.OneToOneField(Seller, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    business_address = models.CharField(max_length=100, null=True, blank=True)
    business_state = models.CharField(max_length=100, null=True, blank=True)
    business_city = models.CharField(max_length=100, null=True, blank=True)
    business_drop_off_address = models.CharField(max_length=100, null=True, blank=True)
    company_type = models.CharField(max_length=100, null=True, blank=True, choices=COMPANY_TYPE)
    business_type = models.CharField(max_length=100, null=True, blank=True, choices=BUSINESS_TYPES)
    market_size = models.PositiveIntegerField(null=True, blank=True)
    number_of_outlets = models.PositiveIntegerField(null=True, blank=True)
    maximum_price_range = models.DecimalField(default=0.0, decimal_places=2, max_digits=10, null=True, blank=True)
    director = models.ForeignKey(Director, on_delete=models.SET_NULL, null=True, blank=True)
    id_card = models.ImageField(null=True, blank=True, upload_to='seller-verification')
    id_card_verified = models.BooleanField(default=False)
    cac_number = models.CharField(null=True, blank=True, max_length=15)
    cac_verified = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    company_tin_number = models.CharField(null=True, blank=True, max_length=50)
    tin_verified = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)

    def __str__(self):
        return f'{self.seller}: {self.verified}'


class SellerFile(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    file = models.FileField(upload_to='seller-files')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.seller}: {self.file}'


class BankAccount(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=True, blank=True)
    bank_code = models.CharField(max_length=100, null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.seller.user.first_name} - {self.bank_name} - {self.account_name}"


class MerchantBanner(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    banner_image = models.ImageField(upload_to='promo-banners')
    # banner_size = models.CharField(max_length=50, choices=BANNER_SIZE_CHOICES, default='small') # Commented 'size' out
    is_active = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Merchant: {self.seller} - ID: {self.id}"


class BulkUploadFile(models.Model):
    file = models.FileField(upload_to="bulk-upload")
    used = models.BooleanField(default=False)
    errors = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.file} - USED: {self.used}"


