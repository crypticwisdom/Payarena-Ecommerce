import json
import re
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from account.models import Profile
from ecommerce.models import Product, ProductDetail, Cart, CartProduct
import uuid
from django.utils import timezone
from threading import Thread
from ecommerce.shopper_email import shopper_signup_verification_email
from ecommerce.utils import encrypt_text, decrypt_text, encrypt_payarena_data
from home.utils import log_request
from module.apis import payment_for_wallet
import requests
from module.payarena_service import PayArenaServices
from module.billing_service import BillingService
from django.conf import settings


def send_shopper_verification_email(email, profile, source):
    try:
        # Send Verification code
        profile.verification_code = uuid.uuid1()
        profile.code_expiration_date = timezone.now() + timezone.timedelta(minutes=15)
        profile.save()

        Thread(target=shopper_signup_verification_email,
               kwargs={"email": email, "profile": profile, "source": source}).start()
        return True
    except (Exception,) as err:
        log_request(f"Error {err}")
        # LOG ERROR
        return False


def create_account(email, phone_number, password, first_name, last_name):
    try:
        user_instance = User.objects.create(
            username=email, email=email, password=make_password(password), first_name=first_name, last_name=last_name
        )
        if user_instance:
            profile = Profile.objects.create(user=user_instance, phone_number=phone_number, verified=True)
            if not profile:
                return False, "An error occurred while creating a profile for this user"
            return True, profile
        else:
            return False, "User not created"
    except (Exception,) as err:
        # Log error
        log_request(f"Error: {err}")
        return False, "An error occurred during user creation"


def validate_email(email):
    try:
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.fullmatch(regex, email):
            return True
        return False
    except (TypeError, Exception) as err:
        # Log error
        return False


def merge_carts(cart_uid, user):
    try:
        """
            Synopsis:
            - If cart A (Unauthenticated cart instance) is empty delete it.
            - If cart B (Authenticated cart instance) is empty delete it.
            
            - Merge Functionality:
                - Sum the 2 query sets to get 1.
                - create a 'basket' / 'container' to holder values during merging.
                - 'basket' should hold the item's Product ID as key and Item (CartProduct) as value.
                - go through the merged queryset to check if item's ID is found in basket.
                - if found, then merge item's 'price' and 'quantity'
                - else add item's Product ID as key and item as value.
        """
        if Cart.objects.filter(cart_uid=cart_uid, status="open").exists():
            unauthenticated_cart_instance = Cart.objects.get(cart_uid=cart_uid, status="open")

            # Filter CartProduct where 'unauthenticated_cart_instance' is found/connected to.
            unauthenticated_cart_instance_products = CartProduct.objects.filter(cart=unauthenticated_cart_instance)

            # Delete cart instance (Cart created by unauthenticated user) if it has not cart-product.
            if len(unauthenticated_cart_instance_products) < 1:
                unauthenticated_cart_instance.delete()
                # Return 'True' after deleting newly created empty cart because it is empty and we can't merge an empty
                # can't perform the merge operation with an empty cart.
                return True, 'cart instance is empty and has been deleted'

            # Get "open" cart that belongs to the user logged-in
            if Cart.objects.filter(user=user, status="open").exists():
                # Since cart with this user is found, then perform merge with both new and authenticated_carts.

                # - Get cart and cart products relating to the user.
                authenticated_cart_instance = Cart.objects.get(user=user, status="open")

                authenticated_cart_instance_products = CartProduct.objects.filter(cart=authenticated_cart_instance)

                if len(authenticated_cart_instance_products) < 1:
                    # if 'authenticated_cart_instance' is empty, delete and assign the user's instance to the new
                    # 'unauthenticated_cart_instance'.
                    authenticated_cart_instance.delete()

                    unauthenticated_cart_instance.user = user
                    unauthenticated_cart_instance.cart_uid = ""
                    unauthenticated_cart_instance.save()
                    return True, 'old instance is empty and has been deleted and has been assigned to user'

                # Merge the 2 carts together to get 1.
                sum_carts = authenticated_cart_instance_products | unauthenticated_cart_instance_products

                basket = {}
                # Main merge functionality using 'basket: dict'
                for item in sum_carts:
                    if item.product_detail.product.id in basket:
                        basket[item.product_detail.product.id].price += item.price
                        basket[item.product_detail.product.id].quantity += item.quantity
                        basket[item.product_detail.product.id].save()
                    else:
                        basket[item.product_detail.product.id] = item
                else:
                    # Delete the previous carts to have a new 'cart' instance.
                    unauthenticated_cart_instance.delete()
                    authenticated_cart_instance.delete()

                    cart = Cart.objects.create(user=user)
                    for key, value in basket.items():
                        value.cart = cart
                        value.save()

        return True, "Success"
    except (Exception,) as err:
        return False, f"{err}"


def register_payarena_user(email, phone_number, f_name, l_name, password):
    # Check if user is available on Payarena Portal
    phone_no = f"0{phone_number[-10:]}"
    response = PayArenaServices.register(
        email=email, phone_no=phone_no, first_name=f_name, last_name=l_name, password=password
    )
    if "Success" in response:
        if response["Success"] is False:
            if response["Message"] == f"User name '{email}' is already taken.":
                pass
            else:
                return False, str(response["Message"])

    return True, "Account Created"


def login_payarena_user(profile, email, password):
    response = PayArenaServices.login(email, password)
    user_token = password
    user_profile = profile
    if "Success" in response:
        if response["Success"] is True and response['Data']:
            user_token = response['Data']["access_token"]
            if user_profile is None:
                # Create User
                user_email = response["Data"]["userProfile"]["Email"]
                first_name = response["Data"]["userProfile"]["FirstName"]
                last_name = response["Data"]["userProfile"]["Surname"]
                phone_no = response["Data"]["userProfile"]["PhoneNumber"]
                user = User.objects.create(username=user_email, first_name=first_name, last_name=last_name, password=make_password(password), email=user_email)
                user_profile = Profile.objects.create(user=user)
                user_profile.verified = True
                user_profile.phone_number = phone_no
                user_profile.save()

        # Encrypt token
        token = None
        if user_token:
            token = encrypt_text(user_token)
        if user_profile:
            user_profile.pay_auth = token
            user_profile.save()

        return user_profile


def change_payarena_user_password(profile, old_password, new_password):
    response = PayArenaServices.change_password(profile, old_password, new_password)
    if "Success" in response:
        if response["Success"] is False:
            log_request(f"Error logging request on User Engine.", f"error_message: {response['Message']}")
            return False, f"{response['Message']}"
        else:
            log_request(f"Password changed on User Engine.", f"message: {response['Message']}")
            return True, f"{response['Message']}"
    return True, ""


def get_wallet_info(profile):
    response = PayArenaServices.get_wallet_info(profile)
    balance = dict()
    if "Success" in response:
        if response["Success"] is False:
            balance["detail"] = response["Message"]
        if response["Success"] is True:
            profile.has_wallet = True
            profile.save()
            balance["detail"] = response["Message"]
            balance["wallet"] = response["Data"]
    return balance


def validate_phone_number_for_wallet_creation(profile):
    response = PayArenaServices.validate_number(profile)
    message = ""
    if "Success" in response:
        if response["Success"] is False:
            message = response["Message"]
        if response["Success"] is True:
            token = response["Data"]["Token"]
            profile.pay_token = encrypt_text(token)
            profile.save()
            message = "A verification OTP has been sent to your mobile number"
    return message


def create_user_wallet(profile, pin, otp):
    one_time_token = decrypt_text(profile.pay_token)
    response = PayArenaServices.create_wallet(profile, wallet_pin=pin, otp=otp, ott=one_time_token)
    success = False
    message = "Error creating wallet, please try again later"
    if "Success" in response:
        if response["Success"] is False:
            message = response["Message"]
        if response["Success"] is True:
            success = True
            message = response["Message"]
            profile.has_wallet = True
            profile.save()

    return success, message


def make_payment_for_wallet(request, amount, pin):
    profile = Profile.objects.get(user=request.user)
    description = "TopUp wallet balance from PayArena Mall"
    callback = f"https://{request.get_host()}/fund-wallet"
    full_name = profile.get_full_name()
    email = profile.email()

    payment_link, payment_id = payment_for_wallet(
        amount=amount, narration=description, callback_url=callback, name=full_name, email=email
    )
    profile.wallet_pin = encrypt_text(pin)
    profile.save()
    return payment_link, payment_id


def fund_customer_wallet(reference):
    # Check payment status
    email = ""
    response = PayArenaServices.get_payment_status(reference)
    status = "pending"
    amount = 0
    if "Status" in response:
        status = str(response["Status"]).lower()
        amount = response["Amount"]
        email = response["CustomerEmail"]
    if status == "approved":
        # Credit customer wallet
        profile = Profile.objects.get(user__email=email)
        # Decrypt wallet pin
        decryted_pin = decrypt_text(profile.wallet_pin)
        # Encrypt payment information
        data = json.dumps({"Scheme": "wallet", "PIN": decryted_pin})
        encrypted_payment_info = encrypt_payarena_data(data)
        response = PayArenaServices.fund_wallet(profile, amount, encrypted_payment_info)

        if "Success" in response:
            if response["Success"] is True and response["Data"]["Status"]:
                return response["Data"]["Status"]

    return status


def confirm_or_create_billing_account(profile, email, password):

    # Validate customer
    response = BillingService.validate_customer(email)
    if "error" in response:
        # Register Customer on billing service
        f_name = profile.user.first_name
        l_name = profile.user.last_name
        phone = profile.phone_number

        result = BillingService.register_customer(
            first_name=f_name, last_name=l_name, email=email, phone_no=phone, password=password
        )
        log_request(f"Billing account created for {f_name} {l_name}", f"response: {result}")
        return True
    return True


def forget_password(email):
    if not email:
        return False, "Email address is required"

    PayArenaServices.forget_password(email)

    return True, "Password recovery email has been successfully sent to the email address provided"


def reset_password(pin, password, email, user):
    response = PayArenaServices.reset_password(email, pin, password)
    if "Success" in response:
        if response["Success"] is True:
            # Change mall user password
            password = make_password(password=password)
            user.password = password
            user.save()
            return True, "Password reset was successful, please proceed to login"
        else:
            return False, "An error has occurred, please try again later"
    if "Error" in response:
        return False, response["Error"]

    return True, ""
