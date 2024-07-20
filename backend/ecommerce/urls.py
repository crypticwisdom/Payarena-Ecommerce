from django.urls import path
from ecommerce import views

app_name = "ecommerce"

urlpatterns = [
    path("", views.MallLandPageView.as_view(), name="mall-land-page"),
    path("product-types/", views.ProductTypeListAPIView.as_view(), name="product-types"),
    path("banner-promo/", views.BannerPromoListAPIView.as_view(), name="banner-promo"),
    path("banner-promo/<str:slug>/", views.BannerPromoDetailAPIView.as_view(), name="banner-promo-detail"),
    path("categories/", views.CategoriesView.as_view(), name="categories"),
    path("categories/<str:slug>/", views.CategoriesView.as_view(), name="categories-detail"),
    path("top-selling/", views.TopSellingProductsView.as_view(), name="top-selling"),
    path("recommended-products/", views.RecommendedProductView.as_view(), name="recommended-products"),
    path("filtered-search/", views.FilteredSearchView.as_view(), name="filter-search"),
    path("product-filter/", views.ProductFilterAPIView.as_view(), name="product-filter"),

    path("category-filter/", views.CategoryFilterAPIView.as_view(), name="category-filter"),

    # CART
    path("cart/", views.CartProductOperationsView.as_view(), name="add-to-cart"),
    path("cart/<str:id>/", views.CartProductOperationsView.as_view(), name="cart-products"),


    # Wishlist
    path("wishlist/", views.ProductWishlistView.as_view(), name="wishlist"),    # GET, POST
    path("wishlist/<int:id>/", views.RetrieveDeleteWishlistView.as_view(), name="wishlist-detail"),

    # Products
    path("product/", views.ProductView.as_view(), name="product"),
    path("product/<str:slug>/", views.ProductView.as_view(), name="product-detail"),

    # Order
    path("checkout/", views.ProductCheckoutView.as_view(), name="checkout"),
    path("track-order", views.TrackOrderAPIView.as_view(), name="track-order"),
    path("order/", views.OrderAPIView.as_view(), name="orders"),
    path("order/<int:pk>/", views.OrderAPIView.as_view(), name="order-detail"),
    path("order/return/<int:pk>/", views.OrderReturnView.as_view(), name="return-order-detail"),
    path("order/return/", views.OrderReturnView.as_view(), name="return-all"),

    # Return Reasons
    path('return-reason/', views.ReturnReasonListAPIView.as_view(), name='return-reason'),
    path('return-reason/<int:id>/', views.ReturnReasonRetrieveAPIView.as_view(), name='return-reason-detail'),

    # Customer Dashboard
    path("dashboard/", views.CustomerDashboardView.as_view(), name="customer-dashboard"),

    # Product Review
    path("review/", views.ProductReviewAPIView.as_view(), name="review"),

    # Name Enquiry
    path("name-enquiry/", views.NameEnquiryAPIView.as_view(), name="name-enquiry"),

    # Mobile APP
    path("mobile/category/", views.MobileCategoryListAPIView.as_view(), name="mobile-category"),
    path("mobile/category/<str:slug>/", views.MobileCategoryDetailRetrieveAPIView.as_view(), name="mobile-category-detail"),
    path("mobile/store", views.MobileStoreListAPIView.as_view(), name="mobile-store"),
    path("mobile/store/<str:slug>/", views.MobileStoreDetailRetrieveAPIView.as_view(), name="mobile-store-detail"),
    path("mobile/store/<str:store_slug>/product", views.MiniStoreAPIView.as_view(), name="mobile-store-detail"),

    # Followers
    path('mobile/follow/', views.StoreFollowerAPIView.as_view(), name='follower'),

    # Cron
    path('cron/delete-cart/', views.RemoveRedundantCartCronView.as_view(), name='cart-cron'),
    path('cron/retry-pickup/', views.RetryOrderBookingCronView.as_view(), name='retry-pickup'),

]
