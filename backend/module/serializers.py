from rest_framework import serializers

from merchant.models import BankAccount, SellerDetail, SellerFile, Seller
from merchant.serializers import SellerDetailSerializer, SellerFileSerializer
from store.models import Store


class SellerSerializer(serializers.ModelSerializer):
    first_name = serializers.StringRelatedField(source='user.first_name')
    last_name = serializers.StringRelatedField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    phone_number = serializers.CharField()
    detail = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    store = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    checked_by = serializers.SerializerMethodField()
    approved_by = serializers.SerializerMethodField()

    def get_checked_by(self, obj):
        if obj.checked_by:
            return obj.checked_by.email
        return None

    def get_approved_by(self, obj):
        if obj.approved_by:
            return obj.approved_by.email
        return None

    def get_bank_details(self, obj):
        bank_detail = None
        if BankAccount.objects.filter(seller=obj).exists():
            bank = BankAccount.objects.filter(seller=obj).last()
            bank_detail = dict()
            bank_detail["code"] = bank.bank_code
            bank_detail["bank_name"] = bank.bank_name
            bank_detail["account_name"] = bank.account_name
            bank_detail["account_no"] = bank.account_number
        return bank_detail

    def get_detail(self, obj):
        data = None
        if SellerDetail.objects.filter(seller=obj):
            data = SellerDetailSerializer(SellerDetail.objects.filter(seller=obj).last(), context=self.context).data
        return data

    def get_file(self, obj):
        file = None
        if SellerFile.objects.filter(seller=obj).exists():
            file = SellerFileSerializer(SellerFile.objects.filter(seller=obj), many=True, context=self.context).data
        return file

    def get_store(self, obj):
        if Store.objects.filter(seller=obj).exists():
            request = self.context.get("request")
            store = [{
                "name": store.name,
                "description": store.description,
                # "categories": store.categories,
                "active": store.is_active
            } for store in Store.objects.filter(seller=obj)]
            return store
        return None

    class Meta:
        model = Seller
        exclude = ["user"]
