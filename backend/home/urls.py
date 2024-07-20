from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path('', views.HomeView.as_view(), name='homepage'),
    path('banks/', views.ListAllBanksAPIView.as_view(), name='banks'),

    # webhooks
    path('payment-verify', views.OrderPaymentVerifyAPIView.as_view(), name='payment-verify'),
    path('fund-wallet', views.FundWalletVerifyAPIView.as_view(), name='fund-wallet'),

]


