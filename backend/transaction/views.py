from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status

from .models import Transaction
from .serializers import TransactionSerializer
from home.pagination import CustomPagination


class TransactionListAPIView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return Transaction.objects.filter(order__customer__user=self.request.user)


class TransactionDetailRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Transaction.objects.filter(order__customer__user=self.request.user)





