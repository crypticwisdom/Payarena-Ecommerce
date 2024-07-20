import uuid
import datetime

from django.conf import settings
from django.db.models import Q, Sum
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from django.utils import timezone
from account.models import Profile, Address
from account.serializers import ProfileSerializer
from account.utils import get_wallet_info
from home.utils import get_previous_date, log_request
from module.apis import call_name_enquiry
from store.models import Store
from store.serializers import CartSerializer, StoreSerializer, StoreProductSerializer
from superadmin.exceptions import raise_serializer_error_msg
from superadmin.serializers import BannerSerializer
from superadmin.utils import perform_banner_filter
from transaction.models import Transaction
from .cron import remove_redundant_cart_cron, retry_order_booking
from .filters import ProductFilter
from .serializers import ProductSerializer, CategoriesSerializer, MallDealSerializer, ProductWishlistSerializer, \
    CartProductSerializer, OrderSerializer, ReturnedProductSerializer, OrderProductSerializer, \
    ProductReviewSerializerOut, ProductReviewSerializerIn, MobileCategorySerializer, ReturnReasonSerializer, \
    DailyDealSerializer, ProductTypeSerializer

from .models import ProductCategory, Product, ProductDetail, Cart, CartProduct, Promo, ProductWishlist, Order, \
    OrderProduct, ReturnReason, ReturnedProduct, ReturnProductImage, ProductReview, DailyDeal, ProductType
from home.pagination import CustomPagination

from .utils import check_cart, perform_operation, top_weekly_products, top_monthly_categories, \
    validate_product_in_cart, get_shipping_rate, order_payment, add_order_product, perform_order_cancellation, \
    perform_order_pickup, perform_order_tracking, create_or_update_cart_product

# Create your views here.
from .utils import sorted_queryset

cache_timeout = settings.CACHE_TIMEOUT


class MallLandPageView(APIView):
    permission_classes = []

    def get(self, request):
        report_type = request.GET.get("request_type")
        try:
            response, response_container, start_date = list(), dict(), timezone.datetime.today()

            if report_type == "deals":
                today_deal_key = "deals_of_the_day"
                # Deals of the Day
                deals_of_the_day = cache.get(today_deal_key)
                if deals_of_the_day is None:
                    # response_container["deals_of_the_day"] = DailyDealSerializer(
                    deals_of_the_day = DailyDealSerializer(
                        DailyDeal.objects.all().order_by("-id")[:10], many=True, context={"request": request}).data
                    cache.set(key=today_deal_key, value=deals_of_the_day, timeout=cache_timeout)
                response_container["deals_of_the_day"] = deals_of_the_day

                # Small Deal
                small_deal_key = "small_deal"
                small_deals = cache.get(small_deal_key)
                if small_deals is None:
                    small_deals = MallDealSerializer(
                        Promo.objects.filter(promo_type="deal", status="active", position="small_deal").order_by("-id")[
                        :10], many=True, context={"request": request}).data
                    cache.set(key=small_deal_key, value=small_deals, timeout=cache_timeout)
                response_container["small_deal"] = small_deals

                # Medium Deal
                medium_deal_key = "medium_deal"
                medium_deals = cache.get(medium_deal_key)
                if medium_deals is None:
                    medium_deals = MallDealSerializer(
                        Promo.objects.filter(promo_type="deal", status="active", position="medium_deal").order_by(
                            "-id")[:10], many=True, context={"request": request}).data
                    cache.set(key=medium_deal_key, value=medium_deals, timeout=cache_timeout)
                response_container["medium_deal"] = medium_deals

                # Big Deal
                big_deal_key = "big_deal"
                big_deals = cache.get(big_deal_key)
                if big_deals is None:
                    big_deals = MallDealSerializer(
                        Promo.objects.filter(promo_type="deal", status="active", position="big_deal").order_by("-id")[
                        :10], many=True, context={"request": request}).data
                    cache.set(key=big_deal_key, value=big_deals, timeout=cache_timeout)
                response_container["big_deal"] = big_deals

            elif report_type == "banner":
                # Small Banners
                small_banner_key = "small_banner"
                small_banner = cache.get(small_banner_key)
                if small_banner is None:
                    small_banner = MallDealSerializer(
                        Promo.objects.filter(promo_type="banner", status="active", position="small_banner").order_by(
                            "-id")[:10], many=True, context={"request": request}).data
                    cache.set(key=small_banner_key, value=small_banner, timeout=cache_timeout)
                response_container["small_banner"] = small_banner

                # Medium Banners
                medium_banner_key = "medium_banner"
                medium_banner = cache.get(medium_banner_key)
                if medium_banner is None:
                    medium_banner = MallDealSerializer(
                        Promo.objects.filter(promo_type="banner", status="active", position="medium_banner").order_by(
                            "-id")[:10], many=True, context={"request": request}).data
                    cache.set(key=medium_banner_key, value=small_banner, timeout=cache_timeout)
                response_container["medium_banner"] = medium_banner

                # Big Banners
                big_banner_key = "big_banner_key"
                big_banner = cache.get(big_banner_key)
                if big_banner is None:
                    big_banner = MallDealSerializer(
                        Promo.objects.filter(promo_type="banner", status="active", position="big_banner").order_by(
                            "-id")[:10], many=True, context={"request": request}).data
                    cache.set(key=big_banner_key, value=big_banner, timeout=cache_timeout)
                response_container["big_banner"] = big_banner

                # Header Banner
                header_banner_key = "head_banner_key"
                header_banner = cache.get(header_banner_key)
                if header_banner is None:
                    header_banner = MallDealSerializer(
                        Promo.objects.filter(promo_type="banner", status="active", position="header_banner")[:10],
                        many=True, context={"request": request}).data
                    cache.set(key=header_banner_key, value=header_banner, timeout=cache_timeout)
                response_container["header_banner"] = header_banner

                # Footer Banner
                footer_banner_key = "footer_banner_key"
                footer_banner = cache.get(footer_banner_key)
                if footer_banner is None:
                    footer_banner = MallDealSerializer(
                        Promo.objects.filter(promo_type="banner", status="active", position="footer_banner")[:10],
                        many=True, context={"request": request}).data
                    cache.set(key=footer_banner_key, value=footer_banner, timeout=cache_timeout)
                response_container["footer_banner"] = footer_banner

            elif report_type == "new_arrivals":
                # (2) Hot New Arrivals in last 3 days ( now changed to most recent 15 products)
                new_arrivals_key = "new_arrivals_key"
                arrival_serializer = cache.get(new_arrivals_key)
                if arrival_serializer is None:
                    new_arrivals = Product.objects.filter(status="active", store__is_active=True).order_by("-id")[:15]
                    arrival_list = [product.id for product in new_arrivals]
                    hot_new_arrivals = Product.objects.filter(id__in=arrival_list).order_by("?")
                    arrival_serializer = ProductSerializer(hot_new_arrivals, many=True, context={"request": request}).data
                    cache.set(key=new_arrivals_key, value=arrival_serializer, timeout=cache_timeout)
                response_container["hot_new_arrivals"] = arrival_serializer

            elif report_type == "top_selling":
                # (3) Top weekly selling products
                top_selling_key = "top_selling_key"
                top_products = cache.get(top_selling_key)
                if top_products is None:
                    top_products = top_weekly_products(request)
                    cache.set(key=top_selling_key, value=top_products, timeout=cache_timeout)
                response_container["top_selling"] = top_products

            elif report_type == "top_category":
                # (4) Top categories of the month
                top_monthly_key = "top_monthly_key"
                top_monthly_cat = cache.get(top_monthly_key)
                if top_monthly_cat is None:
                    top_monthly_cat = top_monthly_categories(request)
                    cache.set(key=top_monthly_key, value=top_monthly_cat, timeout=cache_timeout)
                response_container["top_monthly_categories"] = top_monthly_cat

            elif report_type == "recommended":
                # (5) Recommended Products
                recommended_prod_key = "recommended_prod_key"
                recommended = cache.get(recommended_prod_key)
                if recommended is None:
                    recommended = ProductSerializer(
                        Product.objects.filter(is_featured=True, status="active", store__is_active=True)[:10],
                        many=True, context={"request": request}).data
                    cache.set(key=recommended_prod_key, value=recommended, timeout=cache_timeout)
                response_container["recommended_products"] = recommended

            elif report_type == "most_viewed":
                most_viewed_key = "most_viewed_key"
                most_viewed = cache.get(most_viewed_key)
                if most_viewed is None:
                    most_viewed = ProductSerializer(
                        Product.objects.filter(status="active", store__is_active=True).order_by("-view_count")[:10],
                        many=True, context={"request": request}).data
                    cache.set(key=most_viewed_key, value=most_viewed, timeout=cache_timeout)
                response_container["most_viewed_products"] = most_viewed

            elif report_type == "categories":
                # (6) All categories - to include sub categories and product types
                categories_key = "categories_key"
                categories = cache.get(categories_key)
                if categories is None:
                    categories = CategoriesSerializer(
                        ProductCategory.objects.filter(parent=None), many=True, context={"request": request}).data
                    cache.set(key=categories_key, value=categories, timeout=cache_timeout)
                response_container["categories"] = categories

            elif report_type == "recent_views":
                # recently viewed products:
                # these are products that were recently viewed by the shopper, or last viewed products
                recent_view_key = "recent_view_key"
                recent_view = cache.get(recent_view_key)
                if recent_view is None:
                    recent_view = ProductSerializer(Product.objects.filter(
                        status="active", store__is_active=True).order_by("-last_viewed_date")[:10], many=True,
                                                    context={"request": request}).data
                    if request.user.is_authenticated:
                        shopper = Profile.objects.get(user=request.user)
                        if shopper.recent_viewed_products:
                            shopper_views = shopper.recent_viewed_products.split(",")[1:]
                            recent_view = ProductSerializer(Product.objects.filter(
                                id__in=shopper_views, status="active", store__is_active=True).order_by("?")[:10],
                                                            many=True, context={"request": request}).data
                    cache.set(key=recent_view_key, value=recent_view, timeout=cache_timeout)
                response_container["recently_viewed"] = recent_view

            else:
                return Response({"detail": "Invalid request type selected"}, status=status.HTTP_400_BAD_REQUEST)

            response.append(response_container)
            return Response({"detail": response})
        except (Exception,) as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)


class CategoriesView(APIView, CustomPagination):
    permission_classes = []

    def get(self, request, slug=None):
        param = request.GET.get("param")
        search = request.GET.get("search")
        sub_cat = request.GET.get("sub-category")
        try:
            if slug:
                data = CategoriesSerializer(ProductCategory.objects.get(slug=slug), context={"request": request}).data
                return Response({"detail": data})
            else:
                query = Q()
                if sub_cat == "yes":
                    query &= Q(parent__isnull=False)
                if not sub_cat or sub_cat != "yes":
                    query &= Q(parent__isnull=True)
                if search:
                    query &= Q(name__icontains=search)
                if param == "no-paginate":
                    data = [{"id": cat.id, "name": cat.name, "slug": cat.slug} for cat in
                            ProductCategory.objects.filter(query).order_by("name")]
                    return Response(data)
                query_set = ProductCategory.objects.filter(query).order_by("name")
                paginate_queryset = self.paginate_queryset(query_set, request)
                serialized_data = CategoriesSerializer(paginate_queryset, many=True, context={"request": request}).data
                data = self.get_paginated_response(serialized_data).data
                return Response(data)

        except (Exception,) as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)


class ProductTypeListAPIView(generics.ListAPIView):
    permission_classes = []
    queryset = ProductType.objects.all().order_by("-id")
    serializer_class = ProductTypeSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]


class BannerPromoListAPIView(generics.ListAPIView):
    permission_classes = []
    queryset = Promo.objects.all().order_by("-id")
    serializer_class = BannerSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["title"]


class BannerPromoDetailAPIView(generics.RetrieveAPIView):
    permission_classes = []
    queryset = Promo.objects.all().order_by("-id")
    serializer_class = BannerSerializer
    lookup_field = "slug"


class TopSellingProductsView(APIView, CustomPagination):
    permission_classes = []

    def get(self, request):
        try:
            start_date = timezone.datetime.today()
            end_date2 = timezone.timedelta(weeks=1)

            top_selling_prod_key = "top_selling_prod_ep_key"
            queryset = cache.get(top_selling_prod_key)
            if queryset is None:
                queryset = Product.objects.filter(sale_count=0, created_on__date__gte=start_date - end_date2).order_by(
                    "-id")
                cache.set(key=top_selling_prod_key, value=queryset, timeout=cache_timeout)

            paginated_query = self.paginate_queryset(queryset, request)
            data = self.get_paginated_response(
                ProductSerializer(paginated_query, many=True, context={"request": request}).data).data

            return Response({"detail": data})
        except (Exception,) as err:
            log_request(f"Error: {err}")
            # LOG ERROR
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)


class RecommendedProductView(APIView, CustomPagination):
    permission_classes = []

    def get(self, request):
        try:
            query_set = Product.objects.filter(is_featured=True).order_by("-id")
            data = ProductSerializer(query_set, many=True, context={"request": request}).data

            paginated_query = self.paginate_queryset(query_set, request)
            data = self.get_paginated_response(data=data).data
            return Response({"detail": data})
        except (Exception,) as err:
            log_request(f"Error: {err}")
            # LOG ERROR
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)


class CartProductOperationsView(APIView):
    permission_classes = []

    def post(self, request):
        try:
            variant = request.data.get("variant", [])
            cart_uid = request.data.get("cart_uid")

            if not variant:
                return Response(
                    {"detail": "Product variant is required"}, status=status.HTTP_400_BAD_REQUEST
                )

            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user, status="open")
            else:
                if cart_uid:
                    cart = get_object_or_404(Cart, cart_uid=cart_uid)
                else:
                    cart = Cart.objects.create(cart_uid=uuid.uuid4())

            success, response = create_or_update_cart_product(variant, cart=cart)
            if success is False:
                return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
            # Delete cart if no item is in it
            if not CartProduct.objects.filter(cart=cart).exists():
                cart.delete()
                return Response({"detail": "Cart is empty"})

            serializer = CartSerializer(cart, context={"request": request}).data
            return Response({"detail": "Cart updated", "data": serializer})
        except Exception as err:
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, id=None):
        # try:
        cart = None
        if request.user.is_authenticated:
            if Cart.objects.filter(status="open", user=request.user).exists():
                cart = Cart.objects.filter(status="open", user=request.user).last()
                remaining_open_carts = Cart.objects.filter(status="open", user=request.user).exclude(id=cart.id)

                # Close other open carts
                if remaining_open_carts:
                    remaining_open_carts.update(status="discard")
        else:
            if Cart.objects.filter(status="open", cart_uid=id).exists():
                cart = Cart.objects.get(status="open", cart_uid=id)

        if not cart:
            return Response({"detail": "Cart empty"})

        serializer = CartSerializer(cart, context={"request": request}).data

        return Response({"detail": serializer}, status=status.HTTP_200_OK)
        # except (Exception,) as err:
        #     return Response({"detail": f"{err}"}, status=status.HTTP_400_BAD_REQUEST)


class FilteredSearchView(generics.ListAPIView):
    permission_classes = []
    pagination_class = CustomPagination
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = ProductFilter

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        order_by = self.request.GET.get('sort_by', '')

        query = Q(status='active', store__is_active=True)

        if search:
            query &= Q(name__icontains=search)

        if order_by:
            queryset = sorted_queryset(order_by, query)
            return queryset

        queryset = Product.objects.filter(query).order_by('-updated_on').distinct()
        return queryset


class ProductWishlistView(APIView, CustomPagination):

    def get(self, request):
        try:
            product_wishlist = ProductWishlist.objects.filter(user=request.user).order_by("-id")
            paginated_queryset = self.paginate_queryset(product_wishlist, request)
            serialized_queryset = ProductWishlistSerializer(paginated_queryset, many=True,
                                                            context={"request": request}).data
            serializer = self.get_paginated_response(serialized_queryset).data
            return Response({"detail": serializer})
        except (Exception,) as err:
            return Response({"detail": f"{err}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        product_id = request.data.get('product_id', '')
        if not product_id:
            return Response({"detail": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(pk=product_id)
            product_wishlist, created = ProductWishlist.objects.get_or_create(user=request.user, product=product)
            data = ProductWishlistSerializer(product_wishlist, context={"request": request}).data

            return Response({"detail": "Added to wishlist", "data": data})
        except Exception as ex:
            return Response({"detail": "An error occurred. Please try again", "error": str(ex)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RetrieveDeleteWishlistView(generics.RetrieveDestroyAPIView):
    pagination_class = [CustomPagination]
    serializer_class = ProductWishlistSerializer
    lookup_field = "id"

    def get_queryset(self):
        queryset = ProductWishlist.objects.filter(user=self.request.user)
        return queryset


class ProductView(APIView, CustomPagination):
    permission_classes = []

    def get(self, request, slug=None):
        try:
            if slug:
                product = Product.objects.get(slug=slug, status="active", store__is_active=True)
                product.view_count += 1
                product.last_viewed_date = datetime.datetime.now()
                if request.user.is_authenticated:
                    shopper = Profile.objects.get(user=request.user)
                    viewed_products = str(shopper.recent_viewed_products).split(',')
                    if str(product.id) not in viewed_products:
                        shopper.recent_viewed_products = str("{},{}").format(shopper.recent_viewed_products, product.id)
                        shopper.save()
                product.save()
                serializer = ProductSerializer(product, context={"request": request}).data
            else:
                search = request.GET.get("search")
                query = Q(status="active", store__is_active=True)
                if search:
                    query &= Q(name=search)
                prod = self.paginate_queryset(Product.objects.filter(query).order_by("-id"), request)
                queryset = ProductSerializer(prod, many=True, context={"request": request}).data
                serializer = self.get_paginated_response(queryset).data
            return Response(serializer)
        except Exception as err:
            return Response({"detail": "Error occurred while fetching product", "error": str(err)},
                            status=status.HTTP_400_BAD_REQUEST)


class ProductCheckoutView(APIView):

    def get(self, request):
        address_id = request.GET.get("address_id")
        try:
            # Get customer profile
            customer, created = Profile.objects.get_or_create(user=request.user)
            # Validate product in cart
            validate = validate_product_in_cart(customer)
            if validate:
                return Response({"detail": validate}, status=status.HTTP_400_BAD_REQUEST)
            # Call shipping API to get rate
            shipping_rate = get_shipping_rate(customer, address_id)
            return Response(shipping_rate)
        except Exception as err:
            log_request(f"Error: {err}")
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):

        payment_method = request.data.get("payment_method")
        pin = request.data.get("pin")
        source = request.data.get("source", "payarena")
        address_id = request.data.get("address_id")
        shipping_information = request.data.get("shipping_information")

        # Expected shipping_information payload
        # shipping_information = [
        #     {
        #         "cart_product_id": [2, 23],
        #         "company_id": "234",
        #         "shipper": "GIGLOGISTICS",
        #     }
        # ]

        if not all([shipping_information, address_id]):
            return Response({"detail": "Shipper information and address are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            customer, created = Profile.objects.get_or_create(user=request.user)
            address = Address.objects.get(customer=customer, id=address_id)
            cart = Cart.objects.get(user=request.user, status="open")

            delivery_fee = []
            for product in shipping_information:
                # Get Cart Products
                cart_products = CartProduct.objects.filter(id__in=product["cart_product_id"], cart=cart)

                for cart_product in cart_products:
                    if str(product["company_id"]).isnumeric():
                        cart_product.company_id = product["company_id"]
                    cart_product.shipper_name = str(product["shipper"]).upper()
                    cart_product.delivery_fee = product["shipping_fee"]
                    cart_product.save()

                first_cart_product = cart_products.first()
                delivery_fee.append(first_cart_product.delivery_fee)

            validate = validate_product_in_cart(customer)
            if validate:
                return Response({"detail": validate}, status=status.HTTP_400_BAD_REQUEST)

            # Create Order
            order, created = Order.objects.get_or_create(customer=customer, cart=cart, address=address)

            # PROCESS PAYMENT
            delivery_amount = sum(delivery_fee)
            success, detail = order_payment(request, payment_method, delivery_amount, order, source, pin)
            if success is False:
                return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": detail})

        except Exception as ex:
            return Response({"detail": "An error has occurred", "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class OrderAPIView(APIView, CustomPagination):

    def get(self, request, pk=None):
        context = {"request": request}
        try:
            if pk:
                data = OrderSerializer(Order.objects.get(id=pk, customer__user=request.user), context=context).data
            else:
                order_status = request.GET.get("status", None)
                if order_status:
                    order = Order.objects.filter(orderproduct__status=order_status,
                                                 customer__user=request.user).distinct()
                else:
                    order = Order.objects.filter(customer__user=request.user, payment_status="success").order_by("-id")
                queryset = self.paginate_queryset(order, request)
                serializer = OrderSerializer(queryset, many=True, context=context).data
                data = self.get_paginated_response(serializer).data
            return Response(data)
        except (Exception,) as err:
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            order = Order.objects.get(id=pk, customer__user=request.user)
            success, detail = perform_order_cancellation(order, request.user)
            if success is False:
                return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": detail})
        except Exception as ex:
            return Response({"detail": "An error has occurred", "error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class OrderReturnView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
            To fetch all returned order by the current logged user.
        """
        try:
            returned_products = ReturnedProduct.objects.filter(returned_by=request.user).order_by("-id")
            paginated_response = self.paginate_queryset(returned_products, request)
            serialized_returned_product = ReturnedProductSerializer(instance=paginated_response, many=True,
                                                                    context={"request": request}).data
            final_serialized_response = self.get_paginated_response(serialized_returned_product).data
            return Response({"detail": final_serialized_response})
        except (Exception,) as err:
            return Response({"detail": f"{err}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, pk=None):
        try:
            reason_id = request.data.get('reason_id', None)
            comment = request.data.get('comment', None)
            images = request.data.getlist('images', [])

            # I don't need the image processor here !

            if pk is None:
                return Response({"detail": f"Order Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            if reason_id is None:
                return Response({"detail": f"Order Product ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            if comment is None:
                return Response({"detail": f"Your comment is needed."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if images was passed into 'images' list.
            if all(images) is False:
                return Response({"detail": f"Please provide an Image"}, status=status.HTTP_400_BAD_REQUEST)

            order_product = OrderProduct.objects.filter(id=pk, status="delivered")

            if not order_product.exists():
                return Response({"detail": f"Order product does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            order_product = order_product.last()

            reason = get_object_or_404(ReturnReason, pk=reason_id)

            return_product_instance, success = ReturnedProduct.objects.get_or_create(
                returned_by=request.user, product=order_product)
            return_product_instance.reason = reason
            return_product_instance.comment = comment
            return_product_instance.save()

            for image in images:
                # Pending... waiting for image processing (waiting on the image processing method to use)
                return_product_image = ReturnProductImage(return_product=return_product_instance, image=image)
                return_product_image.save()

            # Pending... Notify admin
            return Response({"detail": f"Your report has been submitted"})
        except (Exception,) as err:
            return Response({"detail": f"{err}"}, status=status.HTTP_400_BAD_REQUEST)


class CustomerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            response = dict()

            # Wallet Information
            profile = Profile.objects.get(user=request.user)
            wallet_bal = get_wallet_info(profile)

            # Recent Orders
            recent_orders = OrderProduct.objects.filter(order__customer=profile).order_by("-id")[:10]
            response['profile_detail'] = ProfileSerializer(profile, context={"request": request}).data
            response['recent_orders'] = OrderProductSerializer(recent_orders, context={"request": request},
                                                               many=True).data
            response['wallet_information'] = wallet_bal
            response['total_amount_spent'] = Transaction.objects.filter(
                order__customer__user=request.user, status="success"
            ).aggregate(Sum("amount"))["amount__sum"] or 0
            # ----------------------

            # Recent Payment
            # -------------------------------

            return Response(response)

        except (Exception,) as err:
            return Response({"detail": f"{err}"}, status=status.HTTP_400_BAD_REQUEST)


class TrackOrderAPIView(APIView):

    def get(self, request):
        order_prod_id = request.GET.get("order_product_id")

        try:
            order_product = OrderProduct.objects.get(id=order_prod_id, order__customer__user=request.user)
            if order_product.tracking_id:
                # Track Order
                success, detail = perform_order_tracking(order_product)
                if success is False:
                    return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
                return Response(detail)
            else:
                return Response({"detail": "Tracking ID not found for selected order"})
        except Exception as er:
            return Response({"detail": f"{er}"}, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewAPIView(APIView, CustomPagination):
    permission_classes = []

    def get(self, request):
        product_id = self.request.GET.get("product_id")

        reviews = self.paginate_queryset(ProductReview.objects.filter(product_id=product_id), request)
        serializer = ProductReviewSerializerOut(reviews, many=True).data
        data = self.get_paginated_response(serializer).data
        return Response(data)

    def post(self, request):
        serializer = ProductReviewSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        result = serializer.save()
        return Response({"detail": "Review added successfully", "data": result})


class NameEnquiryAPIView(APIView):
    permission_classes = []

    def get(self, request):
        bank_code = request.GET.get("bank_code")
        account_no = request.GET.get("account_no")
        success, response = call_name_enquiry(bank_code, account_no)
        return Response({"success": success, "data": response})


# Mobile APP
class MobileCategoryListAPIView(generics.ListAPIView):
    permission_classes = []
    pagination_class = CustomPagination
    queryset = ProductCategory.objects.filter(parent__isnull=True).order_by("-id")
    serializer_class = MobileCategorySerializer


class MobileCategoryDetailRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = []
    serializer_class = MobileCategorySerializer
    queryset = ProductCategory.objects.filter(parent__isnull=True).order_by("-id")
    lookup_field = "slug"


class MobileStoreListAPIView(generics.ListAPIView):
    permission_classes = []
    pagination_class = CustomPagination
    serializer_class = StoreSerializer

    def get_queryset(self):
        query = self.request.GET.get("query")
        queryset = Store.objects.filter(is_active=True, seller__status="active").order_by("-id")
        if query == "on_sale":
            queryset = Store.objects.filter(is_active=True, seller__status="active", on_sale=True)
        if query == "latest":
            today = datetime.datetime.now()
            last_7_days = get_previous_date(date=datetime.datetime.now(), delta=7)
            queryset = Store.objects.filter(is_active=True, seller__status="active",
                                            created_on__range=[last_7_days, today])
        return queryset

    def list(self, request, *args, **kwargs):
        response = super(MobileStoreListAPIView, self).list(request, args, kwargs)
        today = datetime.datetime.now()
        last_7_days = get_previous_date(date=datetime.datetime.now(), delta=7)
        on_sales = [{
            "id": store.id,
            "name": store.name,
            "logo": request.build_absolute_uri(store.logo.url),
            "description": store.description
        } for store in Store.objects.filter(is_active=True, seller__status="active", on_sale=True)[:5]]

        latest_store = [{
            "id": store.id,
            "name": store.name,
            "logo": store.logo.url,
            "description": store.description
        } for store in
            Store.objects.filter(is_active=True, seller__status="active", created_on__range=[last_7_days, today])[:5]]
        response.data["new_stores"] = latest_store
        response.data["on_sales"] = on_sales
        return response


class MobileStoreDetailRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = []
    serializer_class = StoreSerializer
    queryset = Store.objects.filter(is_active=True, seller__status="active")
    lookup_field = "slug"


class MiniStoreAPIView(generics.ListAPIView):
    permission_classes = []
    pagination_class = CustomPagination
    serializer_class = StoreProductSerializer

    def get_queryset(self):
        store_id = self.kwargs.get("store_id")
        order_by = self.request.GET.get('sort_by', '')
        category_id = self.request.GET.get("category_id")
        search = self.request.GET.get("search")

        query = Q(status='active', store__is_active=True, store__slug=store_id)

        if category_id:
            query &= Q(category_id=category_id)

        if search:
            query &= Q(name__icontains=search)

        if order_by:
            queryset = sorted_queryset(order_by, query)
            return queryset

        queryset = Product.objects.filter(query).distinct()
        return queryset


class ReturnReasonListAPIView(generics.ListAPIView):
    queryset = ReturnReason.objects.all()
    serializer_class = ReturnReasonSerializer
    permission_classes = []


class ReturnReasonRetrieveAPIView(generics.RetrieveAPIView):
    queryset = ReturnReason.objects.all()
    serializer_class = ReturnReasonSerializer
    permission_classes = []
    lookup_field = "id"


class StoreFollowerAPIView(APIView):
    def post(self, request):
        store = request.data.get("store", [])
        profile = Profile.objects.get(user=request.user)

        try:
            profile.following.clear()
            for store_id in store:
                profile.following.add(store_id)
            return Response({"detail": "Update successful"})
        except Exception as err:
            return Response({"detail": "An error has occurred", "error": str(err)}, status=status.HTTP_400_BAD_REQUEST)


class ProductFilterAPIView(APIView, CustomPagination):
    permission_classes = []

    def post(self, request):
        param = request.data.get("param")
        products = perform_banner_filter(request)
        result = self.paginate_queryset(products, request)
        if param == "no-paginate":
            return Response(ProductSerializer(result, many=True, context={"request": request}).data)
        serializer = ProductSerializer(result, many=True, context={"request": request}).data
        response = self.get_paginated_response(serializer).data
        return Response(response)


class CategoryFilterAPIView(APIView):
    permission_classes = []

    def post(self, request):
        cat = request.data.get("category_id", [])
        sub_cat = request.data.get("sub_category_id", [])

        result = []
        if cat:
            # category = ProductCategory.objects.filter(id__in=cat, parent__isnull=True).order_by("-id")
            category = ProductCategory.objects.filter(parent__id__in=cat, parent__isnull=False).order_by("-id")
            result = [{"id": cat.id, "name": cat.name} for cat in category]
        if sub_cat:
            # sub_category = ProductCategory.objects.filter(id__in=sub_cat, parent__isnull=False).order_by("-id")
            product_type = ProductType.objects.filter(category__id__in=sub_cat,
                                                      category__parent__isnull=False).order_by("-id")
            result = [{"id": prod.id, "name": prod.name} for prod in product_type]

        return Response(result)


# CRONJOBS
class RemoveRedundantCartCronView(APIView):
    permission_classes = []

    def get(self, request):
        response = remove_redundant_cart_cron()
        return Response({"detail": response})


class RetryOrderBookingCronView(APIView):
    permission_classes = []

    def get(self, request):
        response = retry_order_booking()
        return Response({"detail": response})
