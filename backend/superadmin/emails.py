from django.contrib.auth.models import User
from django.shortcuts import render
from module.email_service import send_email
from django.conf import settings


def admin_reset_password_mail(user):
    first_name =user.first_name
    frontend_link = settings.FRONTEND_URL

    if not first_name:
        first_name = "Payarena Admin"

    message = f'<p class="letter-heading">Hello There, <span>!</span> <br><br><br><br></p>' \
              f'<div class="letter-body"><p>You have successfully reset you password.<br>' \
              f'<br>' \
              f'<div class="order-btn"><a href="{frontend_link}">Get Started </a></div>'

    subject = "Password Reset"
    contents = render(None, 'payarena.html', context={'message': message}).content.decode('utf-8')

    send_email(contents, user.email, subject)
    return True
