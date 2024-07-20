from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = "account"

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='user-login'),   # POST
    path('refresh-token/', TokenRefreshView.as_view(), name='refresh-token'),
    path('sign-up/', views.SignupView.as_view(), name="sign-up"),   # POST
    path('forgot-password/', views.ForgotPasswordView.as_view(), name="forgot-password"),   # GET and POST
    path('change-password/', views.ChangePasswordView.as_view(), name="change-password"),   # PUT
    path('resend-verification/', views.ResendVerificationLinkView.as_view(), name="resend-verification-link"),
    path('link-verification/<str:token>/', views.EmailVerificationLinkView.as_view(), name="link-verification"),

    # Customer Address
    path('address/', views.CustomerAddressView.as_view(), name='customer-address'),
    path('address/<int:id>/', views.CustomerAddressDetailView.as_view(), name='customer-address-detail'),

    # Wallet
    path('wallet/', views.CreateCustomerWalletAPIView.as_view(), name='create-wallet'),
    path('fund-wallet/', views.FundWalletAPIView.as_view(), name='fund-wallet'),

]

