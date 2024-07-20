from threading import Thread

from django.http import HttpResponseRedirect
from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from account.models import Profile
from account.utils import fund_customer_wallet
from ecommerce.utils import update_purchase
from home.utils import log_request
from merchant.utils import get_all_banks

from django.conf import settings

from transaction.models import Transaction

frontend_base_url = settings.FRONTEND_URL


class HomeView(APIView):
    permission_classes = []

    def get(self, request):
        return HttpResponse('Welcome to PAYARENA MALL')


class ListAllBanksAPIView(APIView):

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        success, detail = get_all_banks(profile)
        if success is False:
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response(detail)


class OrderPaymentVerifyAPIView(APIView):
    permission_classes = []

    def post(self, request):
        log_request(request.data)
        trans_ref = request.GET.get("transactionId")
        trans_status = request.GET.get("status")

        try:
            # Check if status is APPROVED, to update transaction, and order
            trans = Transaction.objects.filter(transaction_reference=trans_ref).last()
            if trans_status == "APPROVED":
                # Get transaction
                trans.status = "success"
                trans.order.payment_status = "success"
                order = trans.order
                payment_method = trans.payment_method
                source = trans.source
                # Order Placement
                # update_purchase(order, payment_method)
                Thread(target=update_purchase, args=[order, payment_method, source]).start()

            if trans_status == "DECLINED":
                trans.status = "failed"
                trans.order.payment_status = "failed"

            trans.order.save()
            trans.save()
        except Exception as err:
            log_request(f"Error occurred: {err}")

        return HttpResponseRedirect(redirect_to=f"{frontend_base_url}/verify-checkout?status={trans_status}")


class FundWalletVerifyAPIView(APIView):
    permission_classes = []

    def post(self, request):
        reference = request.data.get("trxId")
        trans_status = fund_customer_wallet(reference)
        # Redirect to frontend endpoint
        return HttpResponseRedirect(redirect_to=f"{frontend_base_url}/verify-wallet?status={str(trans_status)}")


