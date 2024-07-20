import csv
import datetime
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from threading import Thread
from account.serializers import *
from account.utils import validate_email, create_account
from ecommerce.serializers import *
from ecommerce.utils import top_monthly_categories
from home.pagination import CustomPagination
from home.utils import get_previous_date, get_month_start_and_end_datetime, get_year_start_and_end_datetime, \
    get_week_start_and_end_datetime, log_request
from merchant.merchant_email import merchant_account_approval_email, merchant_upload_guide_email
from merchant.models import BankAccount
from merchant.permissions import *
from merchant.serializers import SellerSerializer
from merchant.utils import create_product, update_product, create_seller, update_seller, get_sales_data, \
    get_best_selling_product
from module.apis import u_map_registration
from store.models import Store
from store.serializers import ProductCategorySerializer
from superadmin.exceptions import raise_serializer_error_msg
from superadmin.models import AdminUser, Role
from superadmin.serializers import AdminUserSerializer, CreateAdminUserSerializerIn, BannerSerializer, \
    RoleSerializerOut, AdminMerchantTransactionSerializer, BulkUploadMerchantSerializerIn
from superadmin.utils import create_or_update_category, check_permission, perform_banner_filter, \
    create_or_edit_banner_obj
from transaction.models import Transaction, MerchantTransaction
from transaction.serializers import TransactionSerializer
from superadmin.emails import admin_reset_password_mail
from module.shipping_service import ShippingService


class DashboardAPIView(APIView):
    permission_classes = []

    def get(self, request):
        # total_merchant, total_customer, total_product, sale_analysis, last_5_purchase_item, best_5_selling_product
        # best_selling_merchant_5, recent_payments
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        last_7_days = request.GET.get("last_7_days")
        this_month = request.GET.get("this_month")
        this_year = request.GET.get("this_year")
        this_week = request.GET.get("this_week")

        present_day = datetime.datetime.now()
        if last_7_days == "true":
            past_7_day = get_previous_date(date=present_day, delta=7)
            start_date = past_7_day
            end_date = present_day
        elif this_month == "true":
            month_start, month_end = get_month_start_and_end_datetime(present_day)
            start_date = month_start
            end_date = month_end
        elif this_year == "true":
            year_start, year_end = get_year_start_and_end_datetime(present_day)
            start_date = year_start
            end_date = year_end
        elif this_week == "true":
            week_start, week_end = get_week_start_and_end_datetime(present_day)
            start_date = week_start
            end_date = week_end
        else:
            start_date = date_from
            end_date = date_to

        data = dict()

        latest_purchased_products = OrderProduct.objects.all()[:5]
        most_viewed_products = Product.objects.all().order_by("-view_count")[:10]

        if date_from and date_to:
            latest_purchased_products = OrderProduct.objects.filter(packed_on__range=(start_date, end_date))[:5]
            most_viewed_products = Product.objects.filter(updated_on__range=(start_date, end_date)).order_by(
                "-view_count")[:10]

        last_purchased = list()
        for order_product in latest_purchased_products:
            order = dict()
            order["order_id"] = order_product.id
            order["product_name"] = order_product.product_detail.product.name
            order["image"] = request.build_absolute_uri(order_product.product_detail.product.image.image.url)
            order["amount"] = order_product.total
            order["remaining_stock"] = order_product.product_detail.stock
            last_purchased.append(order)

        most_viewed = list()
        for product in most_viewed_products:
            prod = dict()
            prod["product_id"] = product.id
            prod["product_name"] = product.name
            if product.image:
                prod["image"] = request.build_absolute_uri(product.image.image.url)
            else:
                prod["image"] = None
            prod["store_name"] = product.store.name
            prod["category_name"] = product.category.name
            prod["view_count"] = product.view_count
            most_viewed.append(prod)

        data["sales_data"] = get_sales_data()
        data["last_purchases"] = last_purchased
        data["best_selling_products"] = get_best_selling_product(request, seller=None, date_from=start_date, date_to=end_date)
        data["most_viewed_products"] = most_viewed
        data["top_categories_for_the_month"] = top_monthly_categories(request)
        data["total_merchant"] = Seller.objects.all().count()
        data["total_customer"] = Profile.objects.all().count()
        data["total_product"] = Product.objects.all().count()

        return Response(data)


# Product Start
class ProductAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            return Response(ProductSerializer(Product.objects.get(id=pk), context={"request": request}).data)
        except Exception as err:
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        merchant_id = request.data.get("seller_id")
        try:
            seller = Seller.objects.get(id=merchant_id)
            success, detail, product = create_product(request, seller)
            if success is False:
                return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"detail": detail, "product": ProductSerializer(product, context={"request": request}).data})
        except Exception as err:
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            product = Product.objects.get(id=pk)
            success, query = update_product(request, product)
            if success is False:
                return Response({"detail": query}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "Product updated successfully",
                             "product": ProductSerializer(query, context={"request": request}).data})
        except Exception as ess:
            return Response({"detail": "An error has occurred", "error": str(ess)}, status=status.HTTP_400_BAD_REQUEST)


class ProductListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['store__name', 'name']

    def get_queryset(self):
        prod_status = self.request.GET.get("status")
        queryset = Product.objects.all().order_by("-id")
        if prod_status:
            queryset = Product.objects.filter(status=prod_status).order_by("-id")
        return queryset


# Product End

# Product_Type Start
class ProductTypeAPIView(APIView, CustomPagination):
    permission_classes = [IsAdminUser]

    def post(self, request):
        name = request.data.get("name")
        cat = request.data.get("category_id")

        if not ProductCategory.objects.filter(id=cat, parent__isnull=False).exists():
            return Response({"detail": "Invalid sub category selected"}, status=status.HTTP_400_BAD_REQUEST)

        category = ProductCategory.objects.get(id=cat, parent__isnull=False)
        product_type = ProductType.objects.create(name=name, category=category)
        serializer = ProductTypeSerializer(product_type).data
        return Response({"detail": "Product Type added successfully", "data": serializer})

    def get(self, request, pk=None):
        if pk:
            prod_type = get_object_or_404(ProductType, id=pk)
            response = ProductTypeSerializer(prod_type).data
            return response

        prod_type = ProductType.objects.all()
        queryset = self.paginate_queryset(prod_type, request)
        serializer = ProductTypeSerializer(queryset, many=True).data
        response = self.get_paginated_response(serializer).data
        return response

    def delete(self, pk):
        prod_type = get_object_or_404(ProductType, id=pk)
        prod_type.delete()
        return Response({"detail": "Product Type deleted"})


# Profile Start
class ProfileListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["user__first_name", "user__last_name", "user__email", "phone_number"]

    def get_queryset(self):
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        queryset = Profile.objects.all().order_by("-id")
        if date_from and date_to:
            queryset = Profile.objects.filter(created_on__range=[date_from, date_to]).order_by("-id")
        return queryset

    def list(self, request, *args, **kwargs):
        response = super(ProfileListAPIView, self).list(request, args, kwargs)
        response.data['total_customer'] = Profile.objects.all().count()
        response.data['total_active_customer'] = Profile.objects.filter(user__is_active=True).count()
        date = get_previous_date(date=datetime.datetime.now(), delta=7)
        response.data['recent_customer'] = Profile.objects.filter(created_on__gte=date).count()
        return response


class ProfileDetailRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    lookup_field = "id"


# Profile End

# Brand Start
class BrandListAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = BrandSerializer
    queryset = Brand.objects.all().order_by("-id")
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = request.data.getlist('image')[0]
        name = request.data.get("name")
        if Brand.objects.filter(name=name).exists():
            return Response({'detail': f'Brand: {name}, already exist'}, status=status.HTTP_400_BAD_REQUEST)

        # success, msg = utils.image_processor(9, image)
        #
        # if not success:
        #     return Response({"detail": f"{msg}"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response(serializer.data)


class BrandDetailRetrieveAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    lookup_field = "id"


# Brand End


# ProductCategory Start
class ProductCategoryListAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all().order_by('-id')
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    def create(self, request, *args, **kwargs):
        try:
            data = dict()
            permission = check_permission(request)

            if permission is False:
                return Response(
                    {"detail": "You do not have permission to perform this action."}, status=status.HTTP_401_UNAUTHORIZED
                )

            # Image processor implementation
            image = request.data.getlist('image')[0]
            # success, msg = utils.image_processor(2, image)
            # if not success:
            #     return Response({"detail": f"{msg}"}, status=status.HTTP_400_BAD_REQUEST)
            # Implementation ends here

            # serializer = ProductCategorySerializer(data=request.data)
            # if not serializer.is_valid():
            #     data['detail'] = 'Error in data sent'
            #     for key, value in serializer.errors.items():
            #         for text in value:
            #             data['detail'] = f"Error in '{key}' sent: {text}"
            #     return Response(data, status=status.HTTP_400_BAD_REQUEST)

            category = create_or_update_category(data=request.data, image=image)
            return Response(ProductCategorySerializer(category, context={"request": request}).data)
        except (Exception, ) as err:
            return Response({"detail": f"{err}"}, status=status.HTTP_400_BAD_REQUEST)


class ProductCategoryDetailRetrieveAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        permission = check_permission(request)
        if permission is False:
            return Response(
                {"detail": "You do not have permission to perform this action."}, status=status.HTTP_401_UNAUTHORIZED
            )

        cat_id = self.kwargs.get("id")
        # Image processor implementation
        image = request.data.getlist('image')[0]
        # success, msg = utils.image_processor(2, image)
        # if not success:
        #     return Response({"detail": f"{msg}"}, status=status.HTTP_400_BAD_REQUEST)
        # Implementation ends here

        # serializer = ProductCategorySerializer(data=request.data)
        # if not serializer.is_valid():
        #     data['detail'] = 'Error in data sent'
        #     for key, value in serializer.errors.items():
        #         for text in value:
        #             data['detail'] = f"Error in '{key}' sent: {text}"
        #     return Response(data, status=status.HTTP_400_BAD_REQUEST)

        category = create_or_update_category(data=request.data, image=image, cat_id=cat_id)
        return Response(ProductCategorySerializer(category, context={"request": request}).data)


# ProductCategory End


# Merchant
class AdminSellerAPIView(APIView, CustomPagination):
    permission_classes = [IsAdminUser]

    def get(self, request, seller_id=None):
        if seller_id:
            serializer = SellerSerializer(Seller.objects.get(id=seller_id), context={"request": request})
        else:
            status = request.GET.get("status")
            search = request.GET.get("search")
            param = request.GET.get("param")
            query = Q()
            if status:
                query &= Q(status=status)
            if search:
                query &= Q(sellerdetail__company_name__icontains=search) | Q(user__last_name__icontains=search) | \
                         Q(user__first_name__icontains=search)

            result = Seller.objects.filter(query).order_by("-id")
            if param == "no-paginate":
                data = SellerSerializer(result, many=True, context={"request": request}).data
                return Response(data)
            queryset = self.paginate_queryset(result, request)
            data = SellerSerializer(queryset, many=True, context={"request": request}).data
            serializer = self.get_paginated_response(data)
        return Response(serializer.data)

    def put(self, request, seller_id):
        try:
            success, response = update_seller(request, seller_id)
            if success is False:
                return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
            serializer = SellerSerializer(Seller.objects.get(id=seller_id), context={"request": request}).data
            return Response({"detail": "Merchant account updated", "data": serializer})

        except Exception as ex:
            return Response({"detail": "An error occurred while creating merchant", "error": str(ex)},
                            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        f_name = request.data.get("first_name")
        l_name = request.data.get("last_name")
        email = request.data.get("email")
        phone_number = request.data.get("phone_number")

        try:
            # create user and profile
            if not all([email, phone_number, f_name, l_name]):
                return Response({
                    "detail": "first name, last name, email, and phone number are required fields",
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check username exist
            if User.objects.filter(email=email).exists():
                return Response({"detail": "A user with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            if validate_email(email) is False:
                return Response({"detail": "Invalid Email Format"}, status=status.HTTP_400_BAD_REQUEST)

            phone_number = f"+234{phone_number[-10:]}"

            # Create account on payarena Auth Engine
            password = User.objects.make_random_password()
            """
                User instance will be created on PayArena Auth Engine only when the account is approved 
            """
            # success, detail = register_payarena_user(email, phone_number, f_name, l_name, password)
            # if success is False:
            #     return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

            success, response = create_account(email, phone_number, password, f_name, l_name)
            if success is False:
                return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
            user = response.user

            success, msg = create_seller(request, user, email, phone_number)
            if success is False:
                return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "Merchant account created"})
        except Exception as err:
            return Response({"detail": "An error occurred while creating merchant", "error": str(err)},
                            status=status.HTTP_400_BAD_REQUEST)


class BulkUploadMerchantAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = BulkUploadMerchantSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "File uploaded successfully", "data": response})


class UpdateMerchantStatusAPIView(APIView):
    permission_classes = [IsAdminUser & (IsAuthorizer | IsAdmin | IsSuperAdmin)]

    def put(self, request):
        seller_id = request.data.get("seller_id")
        seller_status = request.data.get("status")

        biller_code = request.data.get("biller_code")
        merchant_id = settings.PAYARENA_MERCHANT_ID
        feel = request.data.get("FEEL")
        fep_type = request.data.get("FEP_TYPE")

        try:
            seller = Seller.objects.get(id=seller_id)
            seller.status = seller_status

            if seller_status == "approve":
                if not all([biller_code, feel, fep_type]):
                    return Response({"detail": "Biller Code, FEEL1 and FEP_TYPE are required to onboard "
                                               "merchant"}, status=status.HTTP_400_BAD_REQUEST)

                if not (fep_type == "flat" or fep_type == "rate"):
                    return Response({"detail": "FEP TYPE can either be 'rate' or 'flat'"},
                                    status=status.HTTP_400_BAD_REQUEST)

                seller.biller_code = biller_code
                seller.feel = feel
                seller.fep_type = fep_type
                seller.merchant_id = merchant_id
                seller.status = "active"
                seller.approved_by = request.user

                store_name = Store.objects.filter(seller=seller).last().name
                bank_account = BankAccount.objects.filter(seller=seller).last()

                if not bank_account:
                    return Response({"detail": "Merchant has no bank account"}, status=status.HTTP_400_BAD_REQUEST)

                # Update seller on UMAP
                response = u_map_registration(
                    biller_id=biller_code, description=str(store_name).upper(), merchant_id=merchant_id,
                    account_no=bank_account.account_number, account_name=bank_account.account_name,
                    bank_code=bank_account.bank_code, fep_type=str(fep_type).upper()[0], feel=feel
                )
                if response["RESPONSE_CODE"] != "00":
                    reason = response["RESPONSE_DESCRIPTION"]
                    seller.status = "inactive"
                    seller.save()
                    return Response(
                        {
                            "detail": f"An error has occurred while registering merchant on UMAP. {reason}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Send Approval Email to seller
                Thread(target=merchant_account_approval_email, args=[seller.user.email]).start()
                Thread(target=merchant_upload_guide_email, args=[seller.user.email]).start()

            seller.save()

            if seller_status == "active" and seller.biller_code == "":
                return Response(
                    {"detail": "Kinly approve merchant first, as biller code, is not registered"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if seller_status == "active" or seller_status == "approve":
                Store.objects.filter(seller=seller).update(is_active=True)
            if seller_status == "inactive" or seller_status == "pending":
                Store.objects.filter(seller=seller).update(is_active=False)
            return Response({"detail": "Merchant status updated successfully"})
        except Exception as ex:
            log_request(f"Exception Error: {ex}")
            return Response({"detail": "An error has occurred", "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


# Admin User
class AdminUserListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = AdminUserSerializer
    pagination_class = CustomPagination
    queryset = AdminUser.objects.all().order_by("-id")
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['user__first_name', 'user__last_name']

    def post(self, request, *args, **kwargs):
        serializer = CreateAdminUserSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        data = serializer.save()
        return Response(data)


class AdminUserRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer
    lookup_field = "id"

    def update(self, request, *args, **kwargs):
        seller_id = self.kwargs.get("id")
        admin_user = get_object_or_404(AdminUser, id=seller_id)
        if not request.data:
            return Response({"detail": "Nothing was updated"})

        if request.data.get('first_name'):
            admin_user.user.first_name = request.data.get('first_name')
        if request.data.get('last_name'):
            admin_user.user.last_name = request.data.get('last_name')
        if request.data.get('password'):
            admin_user.user.set_password(request.data.get('password'))
        admin_user.user.save()

        if request.data.get('role'):
            admin_user.role_id = request.data.get('role')
            admin_user.save()

        data = dict()
        data['detail'] = "Admin user updated successfully"
        data['data'] = AdminUserSerializer(admin_user).data
        return Response(data)


class AdminBannerView(APIView, CustomPagination):
    permission_classes = [IsAdminUser]

    def get(self, request, pk=None):
        if pk:
            banner = get_object_or_404(Promo, id=pk)
            return Response(BannerSerializer(banner, context={"request": request}).data)
        queryset = self.paginate_queryset(Promo.objects.all().order_by("-id"), request)
        serializer = BannerSerializer(queryset, many=True, context={"request": request}).data
        result = self.get_paginated_response(serializer).data
        return Response(result)

    def post(self, request):
        name = request.data.get('title')
        image = request.data.getlist('banner_image')

        if Promo.objects.filter(title=name).exists():
            return Response({
                "detail": "Promo, Deal or Banner with this name already exist"}, status=status.HTTP_400_BAD_REQUEST)

        if not image:
            return Response({"detail": "Image is required."}, status=status.HTTP_400_BAD_REQUEST)
        success, response = create_or_edit_banner_obj(request.data)
        if success is False:
            return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
        data = BannerSerializer(response, context={"request": request}).data
        return Response(data)

    def put(self, request, pk):
        banner = get_object_or_404(Promo, id=pk)
        success, response = create_or_edit_banner_obj(request.data, banner)
        if success is False:
            return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
        data = BannerSerializer(response, context={"request": request}).data
        return Response(data)

    def delete(self, request, pk):
        banner = get_object_or_404(Promo, id=pk)
        # Remove all discount
        for prod in banner.product.all():
            prod.productdetail_set.all().update(discount=0)

        banner.delete()
        return Response({'detail': 'Banner deleted successfully'}, status=status.HTTP_200_OK)


class AdminTransactionListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TransactionSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        "order__orderproduct__product_detail__product__name",
        "order__orderproduct__product_detail__product__category__name",
        "order__orderproduct__product_detail__product__store__name", "order__orderproduct__waybill_no",
        "order__customer__user__first_name", "order__customer__user__last_name"
    ]

    def get_queryset(self):
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        queryset = Transaction.objects.all().order_by("-id")
        if date_from and date_to:
            queryset = Transaction.objects.filter(created_on__range=[date_from, date_to])
        return queryset


class DownloadTransactionReport(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        end_date = request.GET.get("date_to")
        start_date = request.GET.get("date_from")

        if not all([start_date, end_date]):
            return Response({"detail": "Expected: start date and end date for filter"}, status=status.HTTP_400_BAD_REQUEST)

        query_set = Transaction.objects.filter(created_on__range=[start_date, end_date]).order_by("-id")

        if not query_set:
            return Response({"detail": "Cannot download empty report"}, status=status.HTTP_400_BAD_REQUEST)
        file_name = f"transaction_report_{start_date}_to_{end_date}.csv"
        response = HttpResponse(content_type="text/csv", headers={"Content-Disposition": f'attachment; filename={file_name}'})
        fields = [
            'S/N', 'PAYMENT_SOURCE', 'ORDER_ID', 'TRANSACTION_ID', 'CUSTOMER_NAME', 'ADDRESS', 'DATE', 'STATUS',
            'AMOUNT', 'PAYMENT_REFERENCE', 'DETAILS'
        ]
        writer = csv.DictWriter(response, fieldnames=fields)
        writer.writeheader()

        num = 0
        for item in query_set:
            num += 1
            data = dict()
            data["S/N"] = num
            data["PAYMENT_SOURCE"] = item.payment_method
            data["ORDER_ID"] = item.order_id
            data["TRANSACTION_ID"] = item.id
            data["CUSTOMER_NAME"] = item.order.customer.get_full_name()
            data["ADDRESS"] = item.order.address.get_full_address()
            data["DATE"] = item.created_on
            data["STATUS"] = item.status
            data["AMOUNT"] = item.amount
            data["PAYMENT_REFERENCE"] = item.transaction_reference
            data["DETAILS"] = item.transaction_detail
            writer.writerow(data)

        return response


class AdminTransactionRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    lookup_field = "id"


class AdminSignInAPIView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not all([email, password]):
            return Response({"detail": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)
        if not user:
            return Response({"detail": "Invalid login details"}, status=status.HTTP_400_BAD_REQUEST)

        if not AdminUser.objects.filter(user=user).exists():
            return Response({"detail": "You are not permitted to perform this action"},
                            status=status.HTTP_401_UNAUTHORIZED)

        data = AdminUserSerializer(AdminUser.objects.get(user=user)).data
        return Response({"detail": "Login successful",
                         "token": f"{AccessToken.for_user(user)}",
                         "refresh_token": f"{RefreshToken.for_user(user)}",
                         "data": data})


class OrdersView(generics.ListAPIView):
    pagination_class = CustomPagination

    def get_serializer_class(self):
        param = self.kwargs.get('param', '')
        request = self.request
        if param == 'first-level' or 'filter':
            if request.GET.get("order_id"):
                return OrderProductSerializer
            return OrderSerializer
        else:
            return OrderProductSerializer

    def get_serializer_context(self):
        data = {
            'merchant_id': self.request.data.get('merchant_id'),
            'request': self.request
        }
        return data

    def get_queryset(self):
        param = self.kwargs.get('param')
        request = self.request

        if param == 'all':
            return Order.objects.filter(payment_status="success").order_by('-created_on').distinct()

        elif param == 'first-level':
            if request.GET.get("order_id"):
                order_id = request.GET.get("order_id")
                if not Order.objects.filter(id=order_id, payment_status="success").exists():
                    return OrderProduct.objects.filter(payment_status="success").order_by('-created_on')
                order = get_object_or_404(Order, id=order_id)
                return OrderProduct.objects.filter(order=order, order__payment_status="success").order_by(
                    '-created_on').distinct()

            return Order.objects.filter(payment_status="success").order_by('-created_on').distinct()

        elif param == 'filter':
            if not self.request.GET.get('date_from') or not self.request.GET.get('date_to'):
                return Order.objects.filter(payment_status="success").order_by('-created_on').distinct()

            date_from = self.request.GET.get('date_from', '')
            date_to = self.request.GET.get('date_to', '')
            return Order.objects.filter(created_on__range=[date_from, date_to], payment_status="success").order_by(
                '-created_on').distinct()

        else:
            return Order.objects.filter(orderproduct__status=param).order_by('-created_on').distinct()


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser & (IsSuperAdmin | IsAdmin)]
    serializer_class = OrderProductSerializer
    queryset = OrderProduct.objects.all()

    def get_object(self):
        return OrderProduct.objects.get(pk=self.kwargs['order_product_id'])

    def put(self, request, order_product_id):
        order_product = get_object_or_404(OrderProduct, pk=order_product_id)

        order_status = request.data.get('status')
        order_product.status = order_status
        order_product.save()

        # Send email to shopper
        # Send email to seller

        return Response({"detail": "Order updated successfully"})


class AdminRoleListAPIView(generics.ListAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = Role.objects.all().order_by("-created_on")
    serializer_class = RoleSerializerOut


class AdminMerchantTransactionListAPIView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = MerchantTransaction.objects.all().order_by("-id")
    serializer_class = AdminMerchantTransactionSerializer
    pagination_class = CustomPagination


class AdminMerchantTransactionRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]
    queryset = MerchantTransaction.objects.all()
    serializer_class = AdminMerchantTransactionSerializer
    pagination_class = CustomPagination
    lookup_field = "id"


class AdminPasswordResetView(APIView):
    permission_classes = [IsAdminUser]

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
            user_profile = get_object_or_404(Profile, pk=user.id)

            user.password = make_password(confirm_new_password)
            user.save()
            Thread(target=admin_reset_password_mail, args=[user]).start()
            return Response({"detail": "Admin Password has been changed"}, status=status.HTTP_201_CREATED)

        except (Exception,) as err:
            log_request(f"Error: {err}")
            # Log
            return Response({"detail": f"Error: {err}"}, status=status.HTTP_400_BAD_REQUEST)


class ShippersAPIVIew(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            shippers = ShippingService.get_all_shippers()
            data = [{
                "id": shipper["shipperId"], "name": shipper["name"], "biller_code": shipper["billerCode"]
            } for shipper in shippers]
            return Response({"detail": "Data retrieved", "data": data})
        except Exception as err:
            return Response(
                {"detail": "An error occurred while fetching shippers, please try again later", "error": str(err)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request, pk):
        biller_code = request.data.get("biller_code")
        email = request.data.get("email")
        username = request.data.get("username")
        password = request.data.get("password")

        try:
            response = ShippingService.update_shipper(
                pk, billerCode=biller_code, email=email, username=username, password=password
            )
            name = response["name"]
        except Exception as err:
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": f"Shipper: {name}, update successfully"})


