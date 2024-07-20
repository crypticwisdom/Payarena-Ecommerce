from django.contrib import admin
from .models import Transaction, MerchantTransaction


class TransactionModelAdmin(admin.ModelAdmin):
    list_display = ["order", "payment_method", "status"]
    list_filter = ["payment_method", "status"]


admin.site.register(Transaction, TransactionModelAdmin)
admin.site.register(MerchantTransaction)


