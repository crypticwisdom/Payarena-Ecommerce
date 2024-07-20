import json

import requests
from django.conf import settings
from home.utils import log_request


base_url = settings.BILLING_BASE_URL
email = settings.BILLING_EMAIL
password = settings.BILLING_PASSWORD
uid = settings.BILLING_USER_ID


class BillingService:
    @classmethod
    def login(cls):
        payload = json.dumps({"email": email, "password": password})
        url = f"{base_url}/login"
        response = requests.request("POST", url, data=payload, headers={"Content-Type": "application/json"}, verify=False).json()
        log_request(f"url: {url}", f"payload: {payload}", f"response: {response}")
        return response["token"]

    @classmethod
    def get_header(cls):
        token = settings.SHIPPING_TOKEN
        header = dict()
        header["Authorization"] = f"Bearer {token}"
        header["Content-Type"] = "application/json"
        return header

    @classmethod
    def validate_customer(cls, user_email):
        url = f"{base_url}/validate-customer"
        payload = json.dumps({
            "companyId": uid,
            "customerEmail": user_email
        })
        header = cls.get_header()
        response = requests.request("POST", url, headers=header, data=payload, verify=False).json()
        log_request(f"url: {url}, payload: {payload}, response: {response}")
        return response

    @classmethod
    def register_customer(cls, **kwargs):
        header = cls.get_header()
        url = f"{base_url}/{uid}/register-customer"

        data = list()
        params = dict()
        params["firstName"] = kwargs.get("first_name")
        params["lastName"] = kwargs.get("last_name")
        params["email"] = kwargs.get("email")
        params["phone"] = kwargs.get("phone_no")
        params["password"] = kwargs.get("password")

        data.append(params)
        payload = json.dumps(data)
        response = requests.request("POST", url, headers=header, data=payload, verify=False).json()
        log_request(f"url: {url}, payload: {payload}, response: {response}")
        return response

    @classmethod
    def charge_customer(cls, **kwargs):
        url = f"{base_url}/operations/charge"
        header = cls.get_header()

        payment_type = kwargs.get("payment_type")

        if payment_type == "pay_attitude":
            payment_type = "payattitude"

        data = dict()
        data["paymentProvider"] = "Unified Payment"
        data["paymentType"] = payment_type
        data["customerId"] = kwargs.get("customer_id")  # Customer email
        data["currency"] = 566
        data["description"] = kwargs.get("narration")
        data["amount"] = kwargs.get("amount")
        data["returnUrl"] = kwargs.get("callback_url")
        data["pin"] = kwargs.get("pin")
        data["fee"] = 0

        payload = json.dumps(data)

        response = requests.request("POST", url, headers=header, data=payload, verify=False).json()
        log_request(f"url: {url}, payload: {payload}, response: {response}")
        return response

    @classmethod
    def verify_payment(cls, **kwargs):

        header = cls.get_header()

        customer_id = kwargs.get('customer_id')
        provider = kwargs.get('provider')
        trans_id = kwargs.get('trans_id')
        status = str(kwargs.get('status')).upper()
        approval = kwargs.get('approved')

        url = f"{base_url}/operations/verify-payment/{customer_id}/{provider}?trxId={trans_id}&status=" \
              f"{status}&approved={approval}"

        response = requests.request("POST", url, headers=header, verify=False).json()
        log_request(f"url: {url}, response: {response}")
        return response




