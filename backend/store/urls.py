from django.urls import path
from store.views import *

app_name = 'store'

urlpatterns = [
    path('brands/', BrandView.as_view(), name='brands'),
    path('brands/<int:brand_id>/', BrandView.as_view(), name='brands'),
    path('product-categories/', ProductCategoryView.as_view(), name='product_category'),
    path('product-categories/<int:cat_id>/', ProductCategoryView.as_view(), name='product_category'),
    path('store/', StoreView.as_view(), name='store'),
    path('store/<int:store_id>/', StoreView.as_view(), name='store-detail'),
    path('products/', ProductView.as_view(), name='products'),
    path('products/<str:slug>/', ProductView.as_view(), name='products-detail'),
    path('product-image/', ProductImageView.as_view(), name='product_image'),
    path('product-review/', ProductReviewView.as_view(), name='product_review'),
    path('product-wishlist/', ProductWishlistView.as_view(), name='product_wishlist'),
    path('shippers/', ShipperView.as_view(), name='shippers'),
]
