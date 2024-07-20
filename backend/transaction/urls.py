from django.urls import path
from . import views

app_name = "transaction"

urlpatterns = [
    path("", views.TransactionListAPIView.as_view(), name="transaction"),
    path("<id>/", views.TransactionDetailRetrieveAPIView.as_view(), name="transaction-detail"),

]

