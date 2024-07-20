import datetime

from ecommerce.models import Cart, OrderProduct
from ecommerce.utils import perform_order_pickup


def remove_redundant_cart_cron():
    # This function removes cart that are not mapped to any user
    Cart.objects.filter(user__isnull=True, created_on__lt=datetime.datetime.now()).delete()
    return "Redundant carts removed successfully"


def retry_order_booking():
    # This function retried failed order placement
    # GET Order Products
    orders = [
        ordered_product.order for ordered_product in
        OrderProduct.objects.filter(booked=False, order__payment_status="success")
    ]
    for order in orders:
        order_product = OrderProduct.objects.filter(booked=False, order=order, order__payment_status="success")
        perform_order_pickup(order_product, order.address, True)

    return "Pickup job ran successfully"

