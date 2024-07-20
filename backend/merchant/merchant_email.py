from django.shortcuts import render
from module.email_service import send_email


def merchant_order_placement_email(customer, order, order_product):
    data = dict()
    shipping_fee = order_product.delivery_fee
    sub_total = order_product.sub_total
    total = shipping_fee + sub_total
    email = customer.user.email
    data["email"] = customer.user.email
    data["phone_no"] = customer.phone_number
    data["address"] = order.address.get_full_address()
    data["order_id"] = order.id
    data["name"] = customer.user.get_full_name()
    data["quantity"] = order_product.quantity
    data["product_name"] = order_product.product_detail.product.name
    data["sub_total"] = sub_total
    data["price"] = order_product.price
    data["shipper"] = order_product.shipper_name
    data["shipping_fee"] = shipping_fee
    data["total"] = total
    data["payment_method"] = order_product.payment_method
    data["seller"] = order_product.product_detail.product.store.name

    subject = "Order Placement on PayArena Mall"
    contents = render(None, 'merchant_order_placement.html', context=data).content.decode('utf-8')
    send_email(contents, email, subject)
    return True


def merchant_order_delivered_email(customer, order_id, order_product):
    # To be reviewed
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

    subject = "Order Placement on PayArena Mall"
    contents = render(None, 'customer_order_placement.html', context=data).content.decode('utf-8')
    send_email(contents, email, subject)
    return True


def merchant_account_creation_email(email):
    contents = render(None, 'merchant_account_created.html').content.decode('utf-8')
    subject = "Merchant Registration Successful"
    send_email(contents, email, subject)
    return True


def merchant_account_approval_email(email):
    contents = render(None, 'merchant_account_approved.html').content.decode('utf-8')
    subject = "Merchant Registration Confirmed!"
    send_email(contents, email, subject)
    return True


def merchant_upload_guide_email(email):
    contents = render(None, 'merchant_upload_guide.html').content.decode('utf-8')
    subject = "Uploading to Payarena Mall"
    send_email(contents, email, subject)
    return True



