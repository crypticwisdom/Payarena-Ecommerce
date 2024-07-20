from django.contrib.auth.models import User
from django.shortcuts import render
from module.email_service import send_email
from django.conf import settings


def shopper_signup_verification_email(email, profile, source):
    if source == "hope":
        name = "Hope Marketplace"
        verify = settings.HOPE_FRONTEND_VERIFICATION_URL
    else:
        name = "Payarena Mall"
        verify = settings.FRONTEND_VERIFICATION_URL

    first_name = profile.user.first_name
    if not profile.user.first_name:
        first_name = f"{name} Shopper"

    message = f"Dear {first_name}, <br><br>Welcome to {name}. <br>Please click <a href='{verify}/{profile.verification_code}/' target='_blank'>here</a> to verify your email. "
    subject = f"{name} Email Verification"
    contents = render(None, "default_template.html", context={'message': message, 'name': name}).content.decode('utf-8')
    send_email(contents, email, subject)
    return True


def shopper_welcome_email(email, source):
    first_name = User.objects.get(email=email).first_name
    if source == "hope":
        name = "Hope Marketplace"
        frontend_link = settings.HOPE_FRONTEND_URL
    else:
        name = "Payarena Mall"
        frontend_link = settings.FRONTEND_URL

    if not first_name:
        first_name = f"{name} Shopper"

    message = f'<p class="letter-heading">Hello There, <span>{first_name}!</span> <br><br><br><br></p>' \
              f'<div class="letter-body"><p>Welcome to {name}.<br>' \
              f'<br>Your one-stop online shop, where you can get all you are looking for with ease <br><br>' \
              f'<br>Click the button below to start SHOPPING! 🥳</p>' \
              f'<div class="order-btn"><a href="{frontend_link}">Get Started </a></div>'

    subject = f"Welcome to {name}"
    contents = render(None, 'welcome_email.html', context={'message': message, 'name': name}).content.decode('utf-8')

    send_email(contents, email, subject)
    return True


def shopper_order_status_email(order_product, source):
    customer = order_product.order.customer
    order_no = order_product.order_id
    seller = order_product.product_detail.product.store.name
    product_image = order_product.product_detail.product.image.get_image_url()
    product_name = order_product.product_detail.product.name
    address = order_product.order.address.get_full_address()
    email = customer.user.email

    if source == "hope":
        name = "Hope Marketplace"
    else:
        name = "Payarena Mall"

    content = f'<div class="delivery-container"><div class="delivery-info"><p>Your Order #{order_no} has been ' \
              f'{order_product.status}</p></div></div><div class="merchant-letter"><p class="letter-header">' \
              f'Dear Esteemed Customer, </p><br><br><p class="letter-body">Thank you for shopping with PayArena Mall.' \
              f'<br><br>Click the button below to the indicate if your order with No #{order_no} has ' \
              f'been {order_product.status} by the seller: <span>{seller}</span></p><div class="order-btn">' \
              f'<a href="#">Confirm Order Status</a></div></div><div class="product-info"><div class="product">' \
              f'<p>Product</p><div class="product-img-details"><img src="{product_image}" alt="">' \
              f'<div class="product-details"><h3 class="product-name">{product_name}</h3>' \
              f'<p>VENDOR:<span>{seller}</span></p></div></div></div><div class="quantity"><p>Quantity</p>' \
              f'<p class="quantity-num">{order_product.quantity}</p></div><div class="price"><p>Price</p>' \
              f'<p class="price-num">NGN<span> {order_product.total}</span></p></div></div>' \
              f'<div class="shipping-info"><div class="shipping"><p>Shipping:</p>' \
              f'<p>Delivery by {order_product.order.shipper_name}</p></div><div class="shipping-address">' \
              f'<p>Shipping Address:</p><div class="shipping-address-info"><p>{address}</p>' \
              f'<p>{customer.phone_number}</p><p>{customer.user.email}</p></div></div></div>'

    subject = "Order Status"
    contents = render(None, 'shopper_order_status.html', context={'message': content, 'name': name}).content.decode('utf-8')

    send_email(contents, email, subject)
    return True


def shopper_order_placement_email(customer, order_id, order_product, source):
    data = dict()
    shipping_fee = order_product.delivery_fee
    sub_total = order_product.sub_total
    total = shipping_fee + sub_total
    email = customer.user.email
    data["name"] = customer.user.first_name
    data["order_id"] = order_id
    data["product_name"] = order_product.product_detail.product.name
    data["quantity"] = order_product.quantity
    data["price"] = order_product.price
    data["sub_total"] = sub_total
    data["total"] = total
    data["shipper"] = order_product.shipper_name
    data["shipping_fee"] = shipping_fee
    data["payment_method"] = order_product.payment_method
    data["seller"] = order_product.product_detail.product.store.name

    if source == "hope":
        name = "Hope Marketplace"
    else:
        name = "Payarena Mall"
    data["site"] = name

    subject = f"Order Placement on {name}"
    contents = render(None, 'customer_order_placement.html', context=data).content.decode('utf-8')
    send_email(contents, email, subject)
    return True


def shopper_order_delivered_email(customer, order_id, order_product, source):
    data = dict()
    shipping_fee = order_product.delivery_fee
    sub_total = order_product.sub_total
    total = shipping_fee + sub_total
    email = customer.user.email

    data["name"] = customer.user.first_name
    data["phone"] = customer.phone_number
    data["address"] = order_product.order.address.get_full_address()
    data["order_id"] = order_id
    data["product_name"] = order_product.product_detail.product.name
    data["quantity"] = order_product.quantity
    data["price"] = order_product.price
    data["sub_total"] = sub_total
    data["total"] = total
    data["email"] = email
    data["shipper"] = order_product.shipper_name
    data["shipping_fee"] = shipping_fee
    data["payment_method"] = order_product.payment_method
    data["seller"] = order_product.product_detail.product.store.name

    if source == "hope":
        name = "Hope Marketplace"
    else:
        name = "Payarena Mall"
    data["site"] = name

    subject = f"Order Placement on {name}"
    contents = render(None, 'customer_order_delivered.html', context=data).content.decode('utf-8')
    send_email(contents, email, subject)
    return True
