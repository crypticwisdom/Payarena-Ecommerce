import requests
import json

from django.conf import settings

from home.utils import log_request


def send_email(content, email, subject):
    payload = json.dumps({"Message": content, "address": email, "Subject": subject})
    response = requests.request("POST", settings.EMAIL_URL, headers={'Content-Type': 'application/json'}, data=payload)
    # log_request(f"Email sent to: {email}")
    log_request(f"Sending email to: {email}, Response: {response.json()}")
    return response.text
