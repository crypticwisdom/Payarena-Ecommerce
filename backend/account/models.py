from django.contrib.auth.models import User
from django.db import models

from store.models import Store
from .choices import card_from_choices, address_type_choices


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    has_wallet = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile-pictures', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    verified = models.BooleanField(default=False)
    pay_auth = models.TextField(blank=True, null=True)
    pay_token = models.TextField(blank=True, null=True)
    wallet_pin = models.TextField(blank=True, null=True)
    verification_code = models.CharField(max_length=100, null=True, blank=True)
    following = models.ManyToManyField(Store, blank=True)
    code_expiration_date = models.DateTimeField(null=True, blank=True)
    recent_viewed_products = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.user)

    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def email(self):
        return self.user.email


class UserCard(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    bank = models.CharField(max_length=50, null=True)
    card_from = models.CharField(max_length=50, null=True, choices=card_from_choices, default='paystack')
    card_type = models.CharField(max_length=50, null=True)
    bin = models.CharField(max_length=300, null=True)
    last4 = models.CharField(max_length=50, null=True)
    exp_month = models.CharField(max_length=2, null=True)
    exp_year = models.CharField(max_length=4, null=True)
    signature = models.CharField(max_length=200, null=True)
    authorization_code = models.CharField(max_length=200, null=True)
    payload = models.TextField(null=True)
    default = models.BooleanField(default=False, null=True)

    def __str__(self):
        return f"{self.id}: {self.profile}"


class Address(models.Model):
    customer = models.ForeignKey(Profile, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=address_type_choices, default='home')
    name = models.CharField(max_length=500)
    mobile_number = models.CharField(max_length=17)
    locality = models.CharField(max_length=500, blank=True, null=True)
    landmark = models.CharField(max_length=500, blank=True, null=True)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    town = models.CharField(max_length=100, blank=True, null=True)
    town_id = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(default=0, blank=True, null=True, max_length=50)
    longitude = models.FloatField(null=True, blank=True, default=0.0)
    latitude = models.FloatField(null=True, blank=True, default=0.0)
    is_primary = models.BooleanField(default=False)
    updated_on = models.DateTimeField(auto_now=True)

    def get_full_address(self):
        addr = ""
        if self.locality:
            addr += f"{self.locality}, "
        if self.town:
            addr += f"{self.town}, "
        if self.city:
            addr += f"{self.city}, "
        if self.state:
            addr += f"{self.state}, "
        return addr.strip()

    def __str__(self):
        return "{} {} {}".format(self.type, self.name, self.locality)

    class Meta:
        verbose_name_plural = "Addresses"



