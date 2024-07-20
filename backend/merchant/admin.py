from django.contrib import admin
from .models import *


class SellerVerificationInline(admin.TabularInline):
    model = SellerDetail
    extra = 0


class SellerFileInline(admin.TabularInline):
    model = SellerFile
    extra = 0


class SellerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'status', 'created_on']
    list_filter = ['status', 'created_on']
    inlines = [SellerVerificationInline, SellerFileInline]


admin.site.register(Seller, SellerAdmin)
admin.site.register(SellerDetail)
admin.site.register(SellerFile)
admin.site.register(BankAccount)
admin.site.register(MerchantBanner)
admin.site.register(BulkUploadFile)


