from django_filters import rest_framework as filters
from ecommerce.models import ProductDetail, Product, ProductCategory, OrderProduct, Order


class MerchantOrderProductFilter(filters.FilterSet):
    """
        Read: https://www.geeksforgeeks.org/filter-data-in-django-rest-framework/
    """
    status = filters.CharFilter(field_name="status", lookup_expr="iexact")
    category_name = filters.CharFilter(field_name="product_detail__product__category__name", lookup_expr="icontains")
    cancelled_on = filters.DateFromToRangeFilter(field_name="cancelled_on")

    class Meta:
        model = OrderProduct
        fields = ['status', 'category_name', 'cancelled_on']


class MerchantProductSearch(filters.FilterSet):
    product_name = filters.CharFilter(field_name="product__name", lookup_expr="icontains")
    category = filters.CharFilter(field_name="product__category", lookup_expr="icontains")

    class Meta:
        model = ProductDetail
        fields = ['product_name', "category"]
