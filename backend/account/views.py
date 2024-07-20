import secrets, time
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from ecommerce.shopper_email import shopper_welcome_email
from home.utils import log_request
from superadmin.models import AdminUser
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from threading import Thread
from .serializers import ProfileSerializer, CustomerAddressSerializer, CreateCustomerAddressSerializer
from .utils import validate_email, merge_carts, create_account, send_shopper_verification_email, \
    register_payarena_user, login_payarena_user, change_payarena_user_password, get_wallet_info, \
    validate_phone_number_for_wallet_creation, create_user_wallet, make_payment_for_wallet, \
    confirm_or_create_billing_account, forget_password, reset_password


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            email = request.data.get('email', None)
            password, user = request.data.get('password', None), None
            cart_uid = request.data.get("cart_uid", None)

            if AdminUser.objects.filter(user__email=email).exists():
                return Response({"detail": "Invalid customer credential"}, status=status.HTTP_400_BAD_REQUEST)

            if email is None:
                return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            if password is None:
                return Response({"detail": "Password field is required"}, status=status.HTTP_400_BAD_REQUEST)

            if '@' in email:
                check = validate_email(email)

                if check is False:
                    return Response({"detail": "Email is not valid"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user is on UP USER ENGINE
            user = None
            if not User.objects.filter(email=email).exists():
                profile = login_payarena_user(profile=None, email=email, password=password)
                if profile is not None:
                    user = profile.user

            if not User.objects.filter(email=email).exists():
                return Response({"detail": "Customer with this credential not found"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email)
            log_request(f"user: {user}")

            # Check: if user is empty and password does not match.
            if not user.check_password(password):
                return Response({"detail": "Incorrect user login details"}, status=status.HTTP_400_BAD_REQUEST)

            if user:
                profile = Profile.objects.get(user=user)
                if profile.verified is False:
                    return Response({"detail": "User not verified, please request a verification link."},
                                    status=status.HTTP_400_BAD_REQUEST)

                has_merged, message = merge_carts(cart_uid=cart_uid, user=user)
                # Log 'message'

                # Login to PayArena Auth Engine
                Thread(target=login_payarena_user, args=[profile, email, password]).start()
                time.sleep(2)
                wallet_balance = get_wallet_info(profile)

                Thread(target=confirm_or_create_billing_account, args=[profile, email, password]).start()

                return Response({
                    "detail": "Login successful",
                    "token": f"{AccessToken.for_user(user)}",
                    "refresh_token": f"{RefreshToken.for_user(user)}",
                    "data": ProfileSerializer(Profile.objects.get(user=user), context={"request": request}).data,
                    "wallet_information": wallet_balance
                })

        except Exception as err:
            log_request(err)
            return Response({
                "detail": "Login error, please confirm email and password are correct", "error": str(err)
            }, status=status.HTTP_400_BAD_REQUEST)


class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            email = request.data.get("email", None)
            source = request.data.get("source", "payarena")
            f_name, l_name = request.data.get("first_name", None), request.data.get("last_name", None)
            phone_number, password = request.data.get("phone_number", None), request.data.get("password", None)
            password_confirm = request.data.get("password_confirm", None)

            if not all([email, phone_number, password, password_confirm, f_name, l_name]):
                return Response({
                    "detail": "first name, last name, email, phone number, password, and "
                              "confirm password are required fields",
                }, status=status.HTTP_400_BAD_REQUEST)

            # if "@" in username:
            #     return Response({"detail": 'Character "@" is not allowed in username field'},
            #                     status=status.HTTP_400_BAD_REQUEST)

            # Check username exist
            if User.objects.filter(email=email).exists():
                return Response({"detail": "A user with this email already exists"},
                                status=status.HTTP_400_BAD_REQUEST)

            if validate_email(email) is False:
                return Response({"detail": "Invalid Email Format"}, status=status.HTTP_400_BAD_REQUEST)

            phone_number = f"+234{phone_number[-10:]}"

            if password != password_confirm:
                return Response({"detail": "Passwords mismatch"}, status=status.HTTP_400_BAD_REQUEST)

            success, detail = register_payarena_user(email, phone_number, f_name, l_name, password)
            if success is False:
                return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

            success, profile_or_err_msg = create_account(email, phone_number, password, f_name, l_name)
            # if success:
            #     # Send Verification code.
            #     if send_shopper_verification_email(email=email, profile=profile_or_err_msg, source=source):
            #         return Response({"detail": "Account created and Verification link has been sent Successfully"})
            #     else:
            #         return Response({"detail": "An error occurred while sending the verification link"},
            #                         status=status.HTTP_400_BAD_REQUEST)

            return Response({"detail": profile_or_err_msg}, status=status.HTTP_400_BAD_REQUEST)

        except (Exception,) as err:
            log_request(f"Error: {err}")
            # Log
            return Response({"detail": "An error occurred while creating this user"},
                            status=status.HTTP_400_BAD_REQUEST)


# Pending the flow for Forgot Password.
class ForgotPasswordView(APIView):
    permission_classes = []

    def get(self, request):
        email = request.GET.get("email")

        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not validate_email(email):
            return Response({"detail": "Invalid Email Format"}, status=status.HTTP_400_BAD_REQUEST)

        # Call UP to send email with OTP to email
        Thread(target=forget_password, args=[email]).start()
        return Response({"detail": "An OTP has been sent to your email address"})

    def post(self, request):
        otp = request.data.get("otp")
        email = request.data.get("email")
        password = request.data.get("password")
        password_confirm = request.data.get("password_confirm")
        response_status = status.HTTP_400_BAD_REQUEST

        if not all([otp, email, password]):
            return Response({"detail": "otp, email, and password are required"}, status=response_status)

        if password != password_confirm:
            return Response({"detail": "Passwords mismatch"}, status=response_status)

        try:
            user = User.objects.get(email=email)
        except (Exception,) as err:
            log_request(f"Error: {err}")
            return Response({"detail": f"{err}"}, status=response_status)

        success, detail = reset_password(otp, password, email, user)
        if success is True:
            response_status = status.HTTP_200_OK
        return Response({"detail": f"{detail}"}, status=response_status)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            old_password, new_password = request.data.get("old_password", None), request.data.get("new_password", None)
            confirm_new_password = request.data.get("confirm_new_password", None)

            if not all([old_password, new_password, confirm_new_password]):
                return Response({"detail": "All password fields are required"}, status=status.HTTP_400_BAD_REQUEST)

            if new_password != confirm_new_password:
                return Response({"detail": "Password does not match"}, status=status.HTTP_400_BAD_REQUEST)

            if not check_password(old_password, request.user.password):
                return Response({"detail": "Old password does not match your current password"},
                                status=status.HTTP_400_BAD_REQUEST)
            user = request.user
            user_profile = Profile.objects.get(user=user)
            # Change Password on PayArena Auth Engine
            success, message = change_payarena_user_password(user_profile, old_password, new_password)
            if success is False:
                return Response({"detail": "An error occurred while changing password, please try again later",
                                 "error": str(message)}, status=status.HTTP_400_BAD_REQUEST)
            user.password = make_password(confirm_new_password)
            user.save()

        except (Exception,) as err:
            log_request(f"Error: {err}")
            # Log
            return Response({"detail": f"Error: {err}"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"detail": "Password has been changed"}, status=status.HTTP_201_CREATED)


class ResendVerificationLinkView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            email = request.data.get("email", None)
            source = request.data.get("source", "payarena")
            if not email:
                return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            profile = Profile.objects.get(user__email=email)

            if profile is not None:
                if send_shopper_verification_email(email=email, profile=profile, source=source):
                    return Response({"detail": "Verification link has been sent to the specified Email"},
                                    status=status.HTTP_200_OK)
                else:
                    return Response({"detail": "An error occurred while send verification link"},
                                    status=status.HTTP_400_BAD_REQUEST)

            return Response({"detail": "No Profile is linked to the Provided email"}, status=status.HTTP_400_BAD_REQUEST)
        except (Exception, ) as err:
            return Response({"detail": f"{err}"}, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationLinkView(APIView):
    permission_classes = []

    def post(self, request, token=None):
        source = request.data.get("source", "payarena")
        if not Profile.objects.filter(verification_code=token).exists():
            return Response({"detail": "Invalid Verification code"}, status=status.HTTP_400_BAD_REQUEST)

        user_profile = Profile.objects.get(verification_code=token)
        if timezone.now() > user_profile.code_expiration_date:
            return Response({"detail": "Verification code has expired"}, status=status.HTTP_400_BAD_REQUEST)

        user_profile.verified = True
        user_profile.verification_code = ""
        user_profile.save()

        # Send Email to user
        email = user_profile.user.email
        Thread(target=shopper_welcome_email, args=[email, source]).start()
        return Response({"detail": "Your Email has been verified successfully"}, status=status.HTTP_200_OK)


class CustomerAddressView(generics.ListCreateAPIView):
    # serializer_class = CustomerAddressSerializer
    serializer_class = CreateCustomerAddressSerializer

    def get_queryset(self):
        return Address.objects.filter(customer__user=self.request.user)


class CustomerAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerAddressSerializer
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        address_id = self.kwargs.get("id")
        address = get_object_or_404(Address, customer__user=request.user, id=address_id)
        serializer = CustomerAddressSerializer(instance=address, data=request.data, context=self.get_serializer_context())
        if serializer.is_valid():
            serializer.save()
            data = CustomerAddressSerializer(address).data
            return Response(data)
        else:
            return Response({"detail": "An error has occurred", "error": str(serializer.errors)})

    def get_queryset(self):
        return Address.objects.filter(customer__user=self.request.user)


class CreateCustomerWalletAPIView(APIView):

    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.has_wallet is True:
                return Response({"detail": "This account already has a wallet"}, status=status.HTTP_400_BAD_REQUEST)
            response = validate_phone_number_for_wallet_creation(profile)
            return Response({"detail": str(response)})
        except Exception as err:
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            wallet_pin = request.data.get("wallet_pin")
            otp = request.data.get("otp")

            profile = Profile.objects.get(user=request.user)
            success, response = create_user_wallet(profile, wallet_pin, otp)
            if success is False:
                return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": response})
        except Exception as ex:
            return Response({"detail": "An error has occurred", "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class FundWalletAPIView(APIView):

    def post(self, request):
        amount = request.data.get("amount")
        pin = request.data.get("pin")
        if not all([amount, pin]):
            return Response({"detail": "Amount and PIN are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payment_link, payment_id = make_payment_for_wallet(request, amount, pin)
            if payment_link is None:
                return Response({"detail": "Error occurred while generating payment link"})
            return Response({"detail": payment_link})
        except Exception as ex:
            return Response(
                {"detail": "Error occurred while generating payment link", "error": str(ex)},
                status=status.HTTP_400_BAD_REQUEST
            )




