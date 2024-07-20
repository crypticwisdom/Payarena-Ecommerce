from django.urls import path
from . import views

urlpatterns = [
    path('', views.MerchantView.as_view(), name='seller'),
    path('create-merchant/', views.BecomeAMerchantView.as_view(), name="create-merchant"),
    path('add-banner/', views.MerchantAddBannerView.as_view(), name="add-banner"),
    path('dashboard/', views.MerchantDashboardView.as_view(), name="merchant-dashboard"),
    path('products/', views.ProductAPIView.as_view(), name="product"),
    path('stock-values/', views.MerchantLowAndOutOfStockView.as_view(), name="low-and-out-off-stock"),

    path('returns/', views.MerchantReturnsAndRejectView.as_view(), name="returns-and-reject"),
    path('transactions/', views.MerchantTransactionView.as_view(), name="merchant-transaction"),
    path('products/<int:pk>/', views.ProductAPIView.as_view(), name="product"),

    path('product/reviews/', views.MerchantProductReviewsView.as_view(), name="product-review"),
    path('product/reviews/<int:pk>/', views.MerchantProductReviewsView.as_view(), name="product-review-detail"),

    # Orders
    path('orders/', views.MerchantOrderProductsView.as_view(), name="merchant-orders"),
    path('download-report', views.DownloadOrderReport.as_view(), name="download-report"),

    # Transactions
    path('transaction', views.MerchantTransactionAPIView.as_view(), name="transaction"),
    path('transaction/<int:pk>/', views.MerchantTransactionAPIView.as_view(), name="transaction-detail"),

    # Merchant Banner
    path('banner/', views.MerchantBannerCreateAPIView.as_view(), name="banner"),
    path('get-banner/', views.ListMerchantBannerAPIView.as_view(), name="get-banner"),
    path('banner/<int:id>/', views.MerchantBannerRetrieveUpdateAPIView.as_view(), name="banner-detail"),

    # image
    path('product/image/', views.ProductImageView.as_view(), name="product-image"),
    path('product/image/<int:pk>/', views.ProductImageView.as_view(), name="edit-delete-product-image"),

    # Bulk Upload
    path('product-bulk-upload/', views.BulkProductUpload.as_view(), name="product-bulk-upload"),

]

