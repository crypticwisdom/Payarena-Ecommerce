import json

import requests
import xmltodict
from django.conf import settings

from home.utils import log_request

payment_gw_url = settings.PAYMENT_GATEWAY_URL
payment_merchant_id = settings.PAYMENT_GATEWAY_MERCHANT_ID
payment_secret = settings.PAYMENT_GATEWAY_SECRET_KEY
get_banks_url = settings.BANK_URL
credit_wallet_url = settings.PAYMENT_CREDIT_WALLET_URL
u_map_url = settings.U_MAP_BASE_URL
u_map_user_id = settings.U_MAP_USER_ID
u_map_password = settings.U_MAP_PASSWORD


def get_bank_codes(token):
    """
        Call PayArena's API to fetch all bank codes.
    """
    try:
        # requests.exceptions.RequestException
        header = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url=get_banks_url, headers=header, verify=False)
        log_request(f"url: {response.url}, headers: {header}, response: {response.json()}")
        if response.status_code != 200:
            return False, "Request was not successful"
        response = response.json()
        if response['Success']:
            return True, response
        return False, "Request was not successful"
    except (Exception, ) as err:
        return False, str(err)


def call_name_enquiry(bank_code: str, account_number: str):
    try:
        # response = requests.get(url=f'{settings.NAME_ENQUIRY}/214/1774691015')
        response = requests.get(url=f'{settings.NAME_ENQUIRY}/{bank_code}/{account_number}', verify=False)
        if response.status_code != 200:
            return False, "Error while requesting for name enquiry"

        response_to_dict = xmltodict.parse(response.text)
        if response_to_dict['NameEnquiryResponse']['ResponseCode'] != '00':
            return False, response_to_dict['NameEnquiryResponse']['ErrorMessage']

        # response_to_dict = {
        #     'NameEnquiryResponse': {
        #         'ResponseCode': '200',
        #         'AccountNumber': '2114616054',
        #         'AccountName': 'Nwachukwu Wisdom',
        #         'PhoneNumber': '08057784796',
        #         'ErrorMessage': 'error'
        #     }
        # }

        return True, response_to_dict
    except (Exception, ) as err:
        return False, str(err)


def payment_for_wallet(**kwargs):
    link = payment_id = None
    url = f"{payment_gw_url}/{payment_merchant_id}"
    header = dict()
    header["Accept"] = header["Content-Type"] = "application/json"
    data = dict()
    data["amount"] = kwargs.get("amount")
    data["currency"] = 566
    data["description"] = kwargs.get("narration")
    data["returnUrl"] = kwargs.get("callback_url")
    data["secretKey"] = payment_secret
    data["fee"] = 0
    data["CustomerName"] = kwargs.get("name")
    data["Email"] = kwargs.get("email")

    payload = json.dumps(data)

    response = requests.request("POST", url, headers=header, data=payload, verify=False)
    log_request(f"url: {url}, payload: {payload}, response: {response}")
    if response.status_code == 200 and str(response.text).isnumeric():
        link = f"{payment_gw_url}/{response.text}"
        payment_id = str(response.text)

    return link, payment_id


def u_map_registration(**kwargs):
    url = f'{u_map_url}?BILLER_CODE={kwargs.get("biller_id")}&BILLER_DESCRIPTION={kwargs.get("description")}&' \
          f'MERCHANT_ID={kwargs.get("merchant_id")}&BILLER_ACCOUNT={kwargs.get("account_no")}&' \
          f'ACCOUNT_NAME={kwargs.get("account_name")}&BANK_CODE={kwargs.get("bank_code")}&' \
          f'FEP_TYPE={kwargs.get("fep_type")}&FEEL1={kwargs.get("feel")}&' \
          f'USER_ID={u_map_user_id}&PASSWORD={u_map_password}'

    response = requests.request("POST", url, headers={}, verify=False).json()
    log_request(f"Calling UMAP API ---->>> url: {url}, Response: {response}")
    return response






