import base64
import datetime
import decimal
from threading import Thread

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

from account.models import Address
from home.utils import get_week_start_and_end_datetime, get_month_start_and_end_datetime, get_next_date, \
    get_year_start_and_end_datetime, get_previous_month_date, log_request
from merchant.merchant_email import merchant_order_placement_email
from module.billing_service import BillingService
from module.shipping_service import ShippingService
from transaction.models import Transaction, MerchantTransaction
from .models import Cart, Product, ProductDetail, CartProduct, ProductReview, Order, OrderProduct

from django.conf import settings

from .shopper_email import shopper_order_placement_email

encryption_key = bytes(settings.PAYARENA_CYPHER_KEY, "utf-8")
encryption_iv = bytes(settings.PAYARENA_IV, "utf-8")


def sorted_queryset(order_by, query):
    queryset = Product.objects.filter(query).distinct()
    if order_by == "latest":
        queryset = Product.objects.filter(query).order_by('-published_on').distinct()
    if order_by == 'highest_price':
        queryset = Product.objects.filter(query).order_by('-productdetail__price').distinct()
    if order_by == 'lowest_price':
        queryset = Product.objects.filter(query).order_by('productdetail__price').distinct()
    if order_by == 'highest_discount':
        queryset = Product.objects.filter(query).order_by('-productdetail__discount').distinct()
    if order_by == 'lowest_discount':
        queryset = Product.objects.filter(query).order_by('productdetail__discount').distinct()
    if order_by == 'highest_rating':
        queryset = Product.objects.filter(query).order_by('-productreview__rating').distinct()
    if order_by == 'lowest_rating':
        queryset = Product.objects.filter(query).order_by('productreview__rating').distinct()
    return queryset


def check_cart(user=None, cart_id=None, cart_uid=None):
    if cart_uid is not None:
        cart_check = Cart.objects.filter(cart_uid=cart_uid, status="open").exists()
        return cart_check, Cart.objects.filter(cart_uid=cart_uid, status="open")

    if cart_id is not None:
        return Cart.objects.filter(id=cart_id, status="open").exists(), Cart.objects.filter(id=cart_id, status="open")

    if Cart.objects.filter(user=user, status="open").exists():
        return True, Cart.objects.filter(user=user, status="open")

    return False, "Cart not found"


def create_or_update_cart_product(variant, cart):
    for variation_obj in variant:
        variation_id = variation_obj.get('variant_id', '')
        quantity = variation_obj.get('quantity', 1)

        with transaction.atomic():
            product_detail = get_object_or_404(ProductDetail.objects.select_for_update(), id=variation_id)

        # try:
        if quantity > 0:
            if product_detail.stock <= 0:
                return False, f"Selected product: ({product_detail.product.name}) is out of stock"

            if product_detail.stock < quantity:
                return False, f"Selected product: ({product_detail.product.name}) quantity cannot be greater than available"

            if product_detail.product.status != "active":
                return False, f"Selected product: ({product_detail.product.name}) is not available"

            if product_detail.product.store.is_active is False:
                return False, f"Selected product: ({product_detail.product.name}) is not available"

        # Create Cart Product
        # print(cart)
        cart.refresh_from_db()
        cart_product, _ = CartProduct.objects.get_or_create(cart=cart, product_detail=product_detail)
        cart_product.price = product_detail.price * quantity
        cart_product.discount = product_detail.discount * quantity
        if product_detail.discount > 0:
            cart_product.price = product_detail.discount * quantity
        cart_product.quantity = quantity
        cart_product.save()

        # Remove cart_product if quantity is 0
        if cart_product.quantity < 1:
            cart_product.delete()

        # cart_product = CartProduct.objects.create(
        #     cart=cart, product_detail=product_detail, price=product_detail.price,
        #     discount=product_detail.discount, quantity=1)
    return True, "Cart updated"
    # except (Exception,) as err:
    #     return False, f"{err}"


def perform_operation(operation_param, product_detail, cart_product):
    # what operation to perform ?
    if operation_param not in ("+", "-", "remove"):
        log_request("Invalid operation parameter expecting -, +, remove")
        return False, "Invalid operation parameter expecting -, +, remove"

    if operation_param == "+":
        if product_detail.stock > cart_product.quantity + 1:
            cart_product.quantity += 1
            cart_product.price += product_detail.price
            cart_product.save()
            return True, "Added product to cart"
        else:
            # product is out of stock
            return False, "Product is out of stock"

    if operation_param == "-":
        if cart_product.quantity == 1:
            # remove from cart and give response.
            cart_product.delete()
            return True, "Cart product has been removed"

        if cart_product.quantity > 1:
            #   reduce prod_cart and give responses.
            cart_product.quantity -= 1
            cart_product.price -= product_detail.price
            cart_product.save()
            return True, "Cart product has been reduced"

        # Product not available
        return False, "Product is not in cart"

    if operation_param == "remove":
        # remove product and give response
        cart_product.delete()
        return True, "Cart product has been removed"


def top_weekly_products(request):
    top_products = []
    current_date = timezone.now()
    week_start, week_end = get_week_start_and_end_datetime(current_date)
    query_set = Product.objects.filter(
        created_on__gte=week_start, created_on__lte=week_end, status='active', store__is_active=True).order_by(
        "-sale_count"
    )[:10]
    for product in query_set:
        image = None
        if product.image:
            image = request.build_absolute_uri(product.image.image.url),
        review = ProductReview.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg'] or 0
        product_detail = ProductDetail.objects.filter(product=product).last()
        top_products.append(
            {"id": product.id, "name": product.name, "image": image, "rating": review, "stock": product_detail.stock,
             "product_detail_id": product_detail.id, "store_name": product.store.name, "product_slug":product.slug,
             "price": product_detail.price, "discount": product_detail.discount, "store_slug":product.store.slug,
             "featured": product.is_featured, "low_stock_threshold": product_detail.low_stock_threshold})
    return top_products


def top_monthly_categories(request):
    top_categories = []
    today_date = timezone.now()
    # month_start, month_end = get_year_start_and_end_datetime(today_date)
    # queryset = Product.objects.filter(
    #     created_on__gte=month_start, created_on__lte=month_end, status='active', store__is_active=True
    # ).order_by("-sale_count").values("category__id", "category__name", "category__image").annotate(Sum("sale_count")).order_by(
    #     "-sale_count__sum")[:100]

    date_end = get_previous_month_date(today_date, 8)
    queryset = Product.objects.filter(
        created_on__gte=date_end, created_on__lte=today_date, status='active', store__is_active=True
    ).order_by("-sale_count").values("category__id", "category__name", "category__image", "category__slug").annotate(
        Sum("sale_count")).order_by(
        "-sale_count__sum")[:20]
    for product in queryset:
        category = dict()
        category['id'] = product['category__id']
        category['name'] = product['category__name']
        category['slug'] = product['category__slug']
        category['total_sold'] = product['sale_count__sum']
        category['image'] = f"{request.scheme}://{request.get_host()}/media/{product['category__image']}"
        # category['image'] = request.build_absolute_uri(product['category__image'])
        top_categories.append(category)
    return top_categories


def validate_product_in_cart(customer):
    response = list()
    cart = Cart.objects.get(user=customer.user, status="open")
    cart_products = CartProduct.objects.filter(cart=cart)
    for product in cart_products:
        product_detail = product.product_detail
        if product_detail.product.status != "active" or product_detail.product.store.is_active is False:
            response.append({"product_name": f"{product_detail.product.name}",
                             "detail": "Product is not available for delivery at the moment"})

        if product_detail.stock == 0:
            response.append({"product_name": f"{product_detail.product.name}",
                             "detail": "Product is out of stock"})

        if product.quantity > product_detail.stock:
            response.append(
                {"product_name": f"{product_detail.product.name}",
                 "detail": f"Requested quantity is more than the available in stock: {product_detail.stock}"}
            )

    return response


def get_shipping_rate(customer, address_id=None):
    response = list()
    sellers_products = list()

    if Address.objects.filter(id=address_id, customer=customer).exists():
        address = Address.objects.get(id=address_id, customer=customer)
    elif Address.objects.filter(customer=customer, is_primary=True).exists():
        address = Address.objects.filter(customer=customer, is_primary=True).first()
    else:
        address = Address.objects.filter(customer=customer).first()

    cart = Cart.objects.get(user=customer.user, status="open")

    # Get products in cart
    cart_products = CartProduct.objects.filter(cart=cart)

    # Get each seller in cart
    sellers_in_cart = list()
    for product in cart_products:
        seller = product.product_detail.product.store.seller
        sellers_in_cart.append(seller)

    # for product in cart_products:
    #     products_for_seller = {
    #         'seller': product.product_detail.product.store.seller,
    #         'seller_id': product.product_detail.product.store.seller_id,
    #         'products': [
    #             {
    #                 'cart_product_id': product.id,
    #                 'quantity': product.quantity,
    #                 'weight': product.product_detail.weight,
    #                 'price': product.product_detail.price,
    #                 'product': product.product_detail.product,
    #                 'detail': product.product_detail.product.description,
    #             }
    #         ],
    #     }
    #     if products_for_seller not in sellers_products:
    #         sellers_products.append(products_for_seller)
    #
    # Get products belonging to each seller
    for seller in sellers_in_cart:
        products_for_seller = {
            'seller': seller,
            'seller_id': seller.id,
            'products': [
                {
                    'merchant_id': cart_product.product_detail.product.store.seller.id,
                    'quantity': cart_product.quantity,
                    'weight': cart_product.product_detail.weight,
                    'price': cart_product.product_detail.price,
                    'product': cart_product.product_detail.product,
                    'detail': cart_product.product_detail.product.description,
                }
                for cart_product in cart_products.distinct()
                if cart_product.product_detail.product.store.seller == seller
            ],
        }
        if products_for_seller not in sellers_products:
            sellers_products.append(products_for_seller)

    # Call shipping API
    rating = ShippingService.rating(
        sellers=sellers_products, customer=customer, customer_address=address
    )

    result = list()
    # detail = dict()
    # shipping_info = dict()
    # shipping info will be in store_detail, store_detail will be in detail, and detail in result

    for rate in rating:
        if decimal.Decimal(rate["TotalPrice"]) > 0:
            quote_list = rate["QuoteList"]
            for item in quote_list:
                if item["Id"] is not None:
                    data = dict()
                    from store.models import Store
                    # store_name = Store.objects.get(seller_id=item["Id"]).name
                    data["store_name"] = Store.objects.get(seller_id=item["Id"]).name
                    data["shipper"] = rate["ShipperName"]
                    data["company_id"] = item["CompanyID"]
                    data["shipping_fee"] = item["Total"]
                    result.append(data)

    store_names = []
    for store in result:
        store_name = store.get('store_name')
        if store_name not in store_names:
            store_names.append(store_name)

    # Compile results per store
    count = 0
    for store in store_names:
        shippers_list = []
        cart_prod = []
        carted_prod = cart_products.filter(product_detail__product__store__name=store)
        for item in carted_prod:
            cart_prod.append(item.id)

        for item in result:
            count += 1
            store_name = item.get('store_name')
            shipper = item.get('shipper')
            shipping_fee = item.get('shipping_fee')
            company_id = item.get('company_id')
            if store_name == store:
                shippers_list.append({
                    "shipper": shipper, "shipping_fee": shipping_fee, "company_id": company_id,
                    "cart_product_id": cart_prod, "uid": str(count)
                })
        response.append({"store_name": store, "shipping_information": shippers_list})
    return response


def order_payment(request, payment_method, delivery_amount, order, source, pin=None):
    from account.utils import get_wallet_info

    # create Transaction
    # get order amount
    product_amount = CartProduct.objects.filter(cart__order=order).aggregate(Sum("price"))["price__sum"] or 0

    amount = product_amount + delivery_amount
    trans, created = Transaction.objects.get_or_create(
        order=order, payment_method=payment_method, amount=amount, source=source
    )
    customer = order.customer
    email = customer.user.email
    # redirect_url = f"{request.scheme}://{request.get_host()}/payment-verify"
    # redirect_url = request.build_absolute_uri(reverse('home:payment-verify'))
    redirect_url = f"https://{request.get_host()}/payment-verify"

    if payment_method == "wallet":
        if not pin:
            return False, "PIN is required"
        balance = 0
        # Check wallet balance
        wallet_info = get_wallet_info(customer)
        if "wallet" in wallet_info:
            bal = wallet_info["wallet"]["balance"]
            balance = decimal.Decimal(bal)
        if balance < amount:
            # return False, f"Wallet Balance {balance} cannot be less than order amount, please fund wallet"
            return False, "Insufficient wallet balance. Please fund your wallet and try again"

        # Charge wallet
        response = BillingService.charge_customer(
            payment_type="wallet", customer_id=email, narration=f"Payment for OrderID: {order.id}",
            pin=pin, amount=str(amount)
        )
        if "success" in response and response["success"] is False:
            return False, "Could not debit your wallet at the moment. Please try later, or use another payment method"
        # Update transaction status
        trans.status = "success"
        trans.transaction_detail = f"Payment for OrderID: {order.id}"
        trans.save()

        # update order_payment
        order.payment_status = "success"
        order.save()

        update_purchase(order, payment_method, source)
        return True, "Order created"

    if payment_method == "card" or payment_method == "pay_attitude":
        # call billing service to get payment link
        response = BillingService.charge_customer(
            payment_type=payment_method, customer_id=email, narration=f"Payment for OrderID: {order.id}",
            pin=pin, amount=str(amount), callback_url=redirect_url
        )
        if "paymentUrl" in response:

            payment_link = response["paymentUrl"]
            transaction_ref = response["transactionId"]
            status = str(response["status"]).lower()

            trans.status = status
            trans.transaction_reference = transaction_ref
            trans.transaction_detail = f"Payment for OrderID: {order.id}"
            trans.save()

            return True, payment_link

        else:
            return False, "An error has occurred, please try again later"


def add_order_product(order):
    cart_product = CartProduct.objects.filter(cart__order=order)
    for product in cart_product:
        # total = product.price - product.discount
        total = product.price + product.delivery_fee
        three_days_time = get_next_date(timezone.datetime.now(), 3)
        # Create order product instance for items in cart
        order_product, _ = OrderProduct.objects.get_or_create(order=order, product_detail=product.product_detail)
        order_product.price = product.price
        order_product.quantity = product.quantity
        # order_product.discount = product.discount
        order_product.sub_total = product.price
        order_product.total = total
        order_product.delivery_date = three_days_time
        order_product.payment_on = timezone.datetime.now()
        order_product.shipper_name = product.shipper_name
        order_product.company_id = product.company_id
        order_product.delivery_fee = product.delivery_fee
        order_product.save()

        # Increase sale count
        order_product.product_detail.product.sale_count += order_product.quantity
        order_product.product_detail.product.save()
        # Reduce Item stock
        order_product.product_detail.stock -= order_product.quantity
        order_product.product_detail.save()

    # Discard the cart
    order.cart.status = "closed"
    order.cart.save()

    order_products = OrderProduct.objects.filter(order=order)

    return order_products


def check_product_stock_level(product):
    # This function is to be called when an Item is packed or reduced from the stock
    product_detail = ProductDetail.objects.get(product=product)
    if product_detail.stock <= product_detail.low_stock_threshold:
        product_detail.out_of_stock_date = timezone.datetime.now()
        product_detail.save()
        # Send email to merchant
    return True


def perform_order_cancellation(order, user):
    order_products = OrderProduct.objects.filter(order=order)
    for order_product in order_products:
        if order_product.status != "paid":
            return False, "This order has been processed, and cannot be cancelled"
    order_products.update(status="cancelled", cancelled_on=timezone.datetime.now(), cancelled_by=user)
    return True, "Order cancelled successfully"


def perform_order_pickup(order_product, address, retry):
    summary = f"Shipment Request to {address.get_full_address()}"
    response = ShippingService.pickup(order_products=order_product, address=address, order_summary=summary, retry=retry)

    if "error" in response:
        log_request(f"Error while booking Order: {response}")
        return False, "Order cannot be placed at the moment"

    # Update OrderProduct
    for data in response:
        shipper = str(data["Shipper"]).upper()
        order_no = data["OrderNo"]
        delivery_fee = data["TotalAmount"]
        waybill = data["TrackingNo"]

        order_product.filter(shipper_name=shipper).update(
            tracking_id=order_no, delivery_fee=delivery_fee, waybill_no=waybill, status="processed",
            packed_on=datetime.datetime.now(), booked=True
        )
        if data["TrackingNo"] is None:
            order_product.filter(shipper_name=shipper).update(booked=False)

    return True, "Pickup request was successful"


def perform_order_tracking(order_product):
    tracking_id = order_product.tracking_id
    response = ShippingService.track_order(tracking_id)
    shipper = str(order_product.shipper_name).lower()

    if "error" in response:
        return False, "An error occurred while tracking order. Please try again later"

    detail = list()
    for item in response:
        data = dict()
        if shipper == "redstar":
            if item["StatusCode"] == "00":
                order_product.status = "delivered"
            data["status"] = item["StatusDescription"]
        elif shipper == "dellyman":
            if str(item["Status"]).lower() == "completed":
                order_product.status = "delivered"
            data["status"] = item["Status"]
        else:
            ...

        detail.append(data)

    order_product.save()

    return True, detail


def encrypt_text(text: str):
    key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])
    fernet = Fernet(key)
    secure = fernet.encrypt(f"{text}".encode())
    return secure.decode()


def decrypt_text(text: str):
    key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])
    fernet = Fernet(key)
    decrypt = fernet.decrypt(text.encode())
    return decrypt.decode()


def encrypt_payarena_data(data):
    cipher = AES.new(encryption_key, AES.MODE_CBC, iv=encryption_iv)
    plain_text = bytes(data, "utf-8")
    encrypted_text = cipher.encrypt(pad(plain_text, AES.block_size))
    # Convert byte to hex
    result = encrypted_text.hex()
    return result


def decrypt_payarena_data(data):
    cipher = AES.new(encryption_key, AES.MODE_CBC, iv=encryption_iv)
    plain_text = bytes.fromhex(data)
    decrypted_text = unpad(cipher.decrypt(plain_text), AES.block_size)
    # Convert to string
    result = decrypted_text.decode("utf-8")
    return result


def update_purchase(order, payment_method, source):
    # update order
    order_products = add_order_product(order)
    # Update payment method
    order_products.update(payment_method=payment_method)
    # Call pickup order request
    Thread(target=perform_order_pickup, args=[order_products, order.address, False]).start()

    merchant_list = list()
    trans = Transaction.objects.filter(order=order).first()

    for order_product in order_products:
        merchant = order_product.product_detail.product.store.seller
        if merchant not in merchant_list:
            merchant_list.append(order_product.product_detail.product.store.seller)
        # Send order placement email to shopper
        Thread(target=shopper_order_placement_email, args=[order.customer, order.id, order_product, source]).start()
        # Send order placement email to seller
        Thread(target=merchant_order_placement_email, args=[order.customer, order, order_product]).start()
        # Send order placement email to admins

    for seller in merchant_list:
        order_prod = order_products.filter(product_detail__product__store__seller=seller)
        delivery_fee = order_prod.first().delivery_fee
        shipper_name = order_prod.first().shipper_name
        seller_price = order_prod.aggregate(Sum("sub_total"))["sub_total__sum"] or 0
        seller_total = delivery_fee + seller_price

        # Create Merchant Transaction
        merchant_trans, _ = MerchantTransaction.objects.get_or_create(order=order, merchant=seller, transaction=trans)
        merchant_trans.shipper = shipper_name
        merchant_trans.delivery_fee = delivery_fee
        merchant_trans.amount = seller_price
        merchant_trans.total = seller_total
        merchant_trans.save()

    return "Order Updated"

