import ast
import csv
from io import StringIO
from threading import Thread

from django.contrib.auth.models import User
from django.db.models import Avg
from rest_framework import serializers

from ecommerce.models import Promo, ProductCategory
from merchant.models import BulkUploadFile
from store.models import Store
from superadmin.models import Role, AdminUser
from superadmin.exceptions import InvalidRequestException
from transaction.models import MerchantTransaction


class RoleSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Role
        exclude = []


class AdminUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.CharField(source="user.email")
    role = RoleSerializerOut()

    class Meta:
        model = AdminUser
        exclude = ["user"]


class CreateAdminUserSerializerIn(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    role = serializers.CharField(required=True)

    def create(self, validated_data):
        f_name = validated_data.get("first_name")
        l_name = validated_data.get("last_name")
        email = validated_data.get("email")
        password = validated_data.get("password")
        role_id = validated_data.get("role")

        if not Role.objects.filter(id=role_id).exists():
            raise InvalidRequestException({"detail": "Invalid role selected"})

        if User.objects.filter(email=email).exists():
            raise InvalidRequestException({"detail": "User with this email already exist"})

        role = Role.objects.get(id=role_id)

        # Create user
        user, _ = User.objects.get_or_create(username=email)
        user.first_name = f_name
        user.last_name = l_name
        user.email = email
        user.is_staff = True
        user.set_password(password)
        user.save()

        # Create AdminUser
        admin_user, created = AdminUser.objects.get_or_create(user=user)
        admin_user.role = role
        admin_user.save()

        data = AdminUserSerializer(admin_user).data
        return data


class BulkUploadMerchantSerializerIn(serializers.Serializer):
    file = serializers.FileField()

    def create(self, validated_data):
        from merchant.utils import bulk_upload_merchant_thread
        request = self.context.get("request", None)
        file = validated_data.get("file")
        upload = BulkUploadFile.objects.create(file=file)
        Thread(target=bulk_upload_merchant_thread, args=[upload, request]).start()
        return BulkProductUploadSerializerOut(upload, context={"request": request}).data


class BannerSerializer(serializers.ModelSerializer):
    merchant = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()
    product_type = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    def get_product(self, obj):
        request = self.context.get("request")
        prod = list()
        for product in obj.product.all():
            price = product.productdetail_set.last().price
            discount = product.productdetail_set.last().discount
            p_discount = discount / price
            data = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'category': product.category.name,
                'store_name': product.store.name,
                'seller_email': product.store.seller.user.email,
                'product_detail_id': product.productdetail_set.last().id,
                'price': price,
                'discount': discount,
                'percentage_discount': f"-{p_discount:.1%}",
                'rating': product.productreview_set.all().aggregate(Avg('rating'))['rating__avg'] or 0,
                'image': request.build_absolute_uri(product.image.image.url),
            }
            prod.append(data)
        return prod

    def get_merchant(self, obj):
        if obj.merchant:
            merchants = list()
            for merchant in obj.merchant.all():
                store_id = store_name = None
                if Store.objects.filter(seller=merchant).exists():
                    store = Store.objects.filter(seller=merchant).last()
                    store_id = store.id
                    store_name = store.name

                merchants.append({
                    "id": merchant.id,
                    "name": merchant.user.get_full_name(),
                    "store_id": store_id,
                    "store_name": store_name,
                    "email": merchant.user.email,
                })
            return merchants

    def get_category(self, obj):
        if obj.category:
            return [
                {
                    "id": category.id,
                    "name": category.name,
                    "sub_categories": [
                        {'id': cat.id, 'name': cat.name, 'slug': cat.slug}
                        for cat in ProductCategory.objects.filter(parent=category)]
                }
                for category in obj.category.all()
            ] or []

    def get_sub_category(self, obj):
        if obj.sub_category:
            return [
                {
                    "id": sub_cat.id,
                    "name": sub_cat.name,
                    "slug": sub_cat.slug
                }
                for sub_cat in obj.sub_category.all()
            ] or []

    def get_product_type(self, obj):
        if obj.product_type:
            return [
                {
                    "id": prod_type.id,
                    "name": prod_type.name,
                    "slug": prod_type.slug
                }
                for prod_type in obj.product_type.all()
            ] or []

    class Meta:
        model = Promo
        exclude = []


class AdminMerchantTransactionSerializer(serializers.ModelSerializer):
    # order_id, customer_id, merchant_id, transaction_id ref, biller_code
    customer = serializers.SerializerMethodField()
    merchant = serializers.SerializerMethodField()
    transaction_ref = serializers.CharField(source="transaction.transaction_reference")

    def get_customer(self, obj):
        data = dict()
        data["id"] = obj.order.customer_id
        data["first_name"] = obj.order.customer.user.first_name
        data["last_name"] = obj.order.customer.user.last_name
        data["email"] = obj.order.customer.user.email
        return data

    def get_merchant(self, obj):
        data = dict()
        data["id"] = obj.merchant_id
        data["biller_code"] = obj.merchant.biller_code
        return data

    class Meta:
        model = MerchantTransaction
        exclude = ["transaction"]


class BulkProductUploadSerializerOut(serializers.ModelSerializer):
    errors = serializers.SerializerMethodField()

    def get_errors(self, obj):
        if obj.errors:
            return ast.literal_eval(str(obj.errors))
        return obj.errors

    class Meta:
        model = BulkUploadFile
        exclude = ["file"]


class BulkProductUploadSerializerIn(serializers.Serializer):
    current_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    file = serializers.FileField()

    def create(self, validated_data):
        from merchant.utils import bulk_upload_thread
        user = validated_data.get('current_user')
        file = validated_data.get("file")
        upload = BulkUploadFile.objects.create(file=file)
        # Thread(target=bulk_upload_thread, args=[user, upload]).start()
        bulk_upload_thread(user, upload)
        return BulkProductUploadSerializerOut(upload, context={"request": self.context.get("request")}).data
