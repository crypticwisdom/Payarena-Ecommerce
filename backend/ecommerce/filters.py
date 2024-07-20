from django_filters import rest_framework as filters
from .models import Product


class ProductFilter(filters.FilterSet):
    price = filters.RangeFilter(field_name="productdetail__price")
    discount = filters.RangeFilter(field_name="productdetail__discount")
    color = filters.CharFilter(field_name="productdetail__color",)
    size = filters.CharFilter(field_name="productdetail__size",)
    category = filters.CharFilter(field_name="category__name",)
    store = filters.CharFilter(field_name="store__name",)
    brand = filters.CharFilter(field_name="productdetail__brand__name", lookup_expr='iexact')
    rating = filters.NumberFilter(field_name='productreview__rating', lookup_expr='iexact')
    is_featured = filters.BooleanFilter(field_name='is_featured')

    class Meta:
        model = Product
        fields = ('store', 'category', 'brand', 'rating', 'price', 'discount', 'is_featured', 'size', 'color')
