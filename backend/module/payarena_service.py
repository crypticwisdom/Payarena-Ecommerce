import json
import requests
from django.conf import settings

from ecommerce.utils import decrypt_text
from home.utils import log_request

base_url = settings.PAYARENA_ACCOUNT_BASE_URL
pgw_url = settings.PAYMENT_GATEWAY_URL


class PayArenaServices:
    @classmethod
    def get_auth_header(cls, profile):
        token = decrypt_text(profile.pay_auth)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        return headers

    @classmethod
    def register(cls, **kwargs):
        url = f"{base_url}/account/register"

        payload = dict()
        payload["Email"] = kwargs.get("email")
        payload["PhoneNumber"] = kwargs.get("phone_no")
        payload["FirstName"] = kwargs.get("first_name")
        payload["LastName"] = kwargs.get("last_name")
        payload["Password"] = kwargs.get("password")

        payload = json.dumps(payload)
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload, verify=False).json()
        log_request(f"url: {url}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def login(cls, email, password):
        url = f"{base_url}/account/login"
        payload = f'Username={email}&Password={password}'
        res = requests.request("POST", url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=payload, verify=False)
        log_request(f"url: {url}", f"payload: {payload}", f"response: {res.text}")
        return res.json()

    @classmethod
    def forget_password(cls, email):
        url = f"{base_url}/account/forgetpassword"
        data = {
            "EmailAddress": email
        }
        payload = json.dumps(data)
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload, verify=False).json()
        log_request(f"url: {url}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def reset_password(cls, email, pin, password):
        url = f"{base_url}/account/resetpassword"
        payload = json.dumps({
            "EmailAddress": email,
            "OTP": pin,
            "Password": password
        })
        response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload, verify=False).json()
        log_request(f"url: {url}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def change_password(cls, profile, old_password, new_password):
        url = f"{base_url}/account/changepassword"
        header = cls.get_auth_header(profile)
        payload = json.dumps({
            "OldPassword": f"{old_password}",
            "NewPassword": f"{new_password}"
        })
        response = requests.request("POST", url, headers=header, data=payload, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def get_wallet_info(cls, profile):
        header = cls.get_auth_header(profile)
        url = f"{base_url}/mobile/balance"
        response = requests.request("GET", url, headers=header, verify=False)
        log_request(f"url: {url}", f"headers: {header}", f"response: {response.text}")
        return response.json()

    @classmethod
    def validate_number(cls, profile):
        header = cls.get_auth_header(profile)
        url = f"{base_url}/mobile/validate-phone-number"
        response = requests.request("GET", url, headers=header, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"response: {response}")
        return response

    @classmethod
    def create_wallet(cls, profile, wallet_pin, otp, ott):
        header = cls.get_auth_header(profile)
        url = f"{base_url}/mobile/create-wallet"
        payload = json.dumps({
            "Pin": wallet_pin,
            "AuthCode": otp,
            "Token": ott
        })
        response = requests.request("POST", url, headers=header, data=payload, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def fund_wallet(cls, profile, amount, payment_info):
        header = cls.get_auth_header(profile)
        url = f"{base_url}/mobile/mall-credit-wallet"
        payload = json.dumps({"Amount": amount, "Fee": 100, "PaymentInformation": payment_info})
        response = requests.request("POST", url, headers=header, data=payload, verify=False).json()
        log_request(f"url: {url}", f"headers: {header}", f"payload: {payload}", f"response: {response}")
        return response

    @classmethod
    def get_payment_status(cls, reference):
        url = f"{pgw_url}/status/{reference}"
        response = requests.request("GET", url, verify=False)
        log_request(f"url: {url}", f"response: {response}")
        return response.json()
