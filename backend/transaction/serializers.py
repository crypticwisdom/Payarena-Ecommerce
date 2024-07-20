from django.db.models import Sum
from rest_framework import serializers

from ecommerce.models import Order, OrderProduct
from store.models import Store
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    order_detail = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

    def get_amount(self, obj):
        merchant = self.context.get("merchant")
        if merchant:
            store = Store.objects.get(seller=merchant)
            order_product_total = OrderProduct.objects.filter(
                order=obj.order, product_detail__product__store=store).aggregate(Sum("total"))["total__sum"] or 0
            delivery_total = OrderProduct.objects.filter(
                order=obj.order, product_detail__product__store=store).aggregate(
                Sum("delivery_fee"))["delivery_fee__sum"] or 0
            amount = order_product_total + delivery_total
        else:
            amount = obj.amount
        return amount

    def get_order_detail(self, obj):
        data = dict()
        data["order_id"] = obj.order.id
        data["customer"] = obj.order.customer.get_full_name()
        products_in_order = list()
        merchant = self.context.get("merchant")
        if merchant:
            store = Store.objects.get(seller=merchant)
            order_products = OrderProduct.objects.filter(order=obj.order, product_detail__product__store=store)
        else:
            order_products = OrderProduct.objects.filter(order=obj.order)

        for order_product in order_products:
            detail = dict()
            detail["product_name"] = order_product.product_detail.product.name
            detail["category"] = order_product.product_detail.product.category.name
            detail["store_name"] = order_product.product_detail.product.store.name
            detail["waybill_no"] = order_product.waybill_no
            products_in_order.append(detail)

        data["products"] = products_in_order
        return data

    class Meta:
        model = Transaction
        exclude = ["order"]



