from django.db import models

from ecommerce.models import Order
from merchant.models import Seller

payment_status_choices = (
    ("pending", "Pending"), ("failed", "Failed"), ("success", "Success")
)
payment_method_choices = (
    ("-", "-------"), ("card", "Card"), ("wallet", "Wallet"), ("transfer", "Transfer"), ("pay_attitude", "Pay Attitude")
)


class Transaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=100, choices=payment_method_choices, default="-")
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
    # management_fee = models.DecimalField(decimal_places=2, max_digits=10, default=0.0)
    # total = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
    status = models.CharField(max_length=100, choices=payment_status_choices, default="pending")
    source = models.CharField(max_length=100, blank=True, null=True)
    transaction_reference = models.CharField(max_length=200, blank=True, null=True)
    transaction_detail = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order} - {self.status}"


class MerchantTransaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    merchant = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True)
    shipper = models.CharField(max_length=200)
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
    delivery_fee = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
    total = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ID: {self.id} - MerchantID: {self.merchant_id} - OrderID: {self.order_id}"


