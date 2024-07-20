from rest_framework import serializers

from ecommerce.models import Cart, OrderProduct, Product
from ecommerce.serializers import ProductSerializer
from merchant.models import Seller
from store.serializers import CartSerializer
from .models import Profile, Address
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField()

    def get_phone_number(self, obj):
        phone_no = None
        if Profile.objects.filter(user=obj).exists():
            phone_no = Profile.objects.get(user=obj).phone_number
        return phone_no

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'date_joined']


class CustomerAddressSerializer(serializers.ModelSerializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    is_primary = serializers.BooleanField()

    class Meta:
        model = Address
        exclude = []

    def update(self, instance, validated_data):
        is_primary = validated_data.get("is_primary")
        auth_user = validated_data.get("auth_user")

        address = super(CustomerAddressSerializer, self).update(instance, validated_data)
        if is_primary:
            address.is_primary = is_primary

        if is_primary is True:
            # Get all customer address and set their primary to false
            Address.objects.filter(customer__user=auth_user).exclude(id=instance.id).update(is_primary=False)
        address.save()
        return CustomerAddressSerializer(address, context=self.context).data


class CreateCustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = []


class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()
    user = UserSerializer()
    is_merchant = serializers.SerializerMethodField()
    cart = serializers.SerializerMethodField()
    total_purchase_count = serializers.SerializerMethodField()
    recently_viewed_products = serializers.SerializerMethodField()

    def get_recently_viewed_products(self, obj):
        recent_view = None
        if obj.recent_viewed_products:
            shopper_views = obj.recent_viewed_products.split(",")[1:]
            recent_view = ProductSerializer(Product.objects.filter(
                id__in=shopper_views, status="active", store__is_active=True).order_by("?")[:10], many=True,
                                            context={"request": self.context.get("request")}).data
        return recent_view

    def get_total_purchase_count(self, obj):
        return OrderProduct.objects.filter(order__customer=obj, order__payment_status="success").count()

    def get_cart(self, obj):
        request = self.context.get("request")
        if Cart.objects.filter(user=obj.user, status="open").exists():
            return CartSerializer(Cart.objects.filter(user=obj.user, status="open").last(), context={"request": request}).data
        return None

    def get_is_merchant(self, obj):
        if Seller.objects.filter(user=obj.user).exists():
            return True
        return False

    def get_profile_picture(self, obj):
        image = None
        if obj.profile_picture:
            image = obj.profile_picture.url
        return image

    def get_addresses(self, obj):
        address = None
        if Address.objects.filter(customer=obj).exists():
            address = CustomerAddressSerializer(Address.objects.filter(customer=obj), many=True).data
        return address

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'profile_picture', 'addresses', 'verified', 'has_wallet', 'is_merchant', 'cart',
            'total_purchase_count', 'recently_viewed_products', 'following'
        ]
