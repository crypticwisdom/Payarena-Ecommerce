import datetime

from django.contrib.auth.models import User
from django.db import models

from merchant.models import Seller
from store.choices import product_status_choices, cart_status_choices, payment_status_choices, order_status_choices, \
    order_entry_status

status_choice = (('active', 'Active'), ('inactive', 'Inactive'))
BANNER_POSITION_CHOICES = (
    ("header_banner", "Header Banner"), ("footer_banner", "Footer Banner"),
    ("big_banner", "Big Banner"), ("medium_banner", "Medium Banner"), ("small_banner", "Small Banner"),
    ("big_deal", "Big Deal"), ("medium_deal", "Medium Deal"), ("small_deal", "Small Deal")
)


# Create your models here.
class Brand(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='brand-images', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=500, null=True, blank=True, editable=False)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='category-images', null=False, blank=True)
    brands = models.ManyToManyField(Brand, related_name='brands', blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=500, null=True, blank=True, editable=False)
    image = models.ImageField(upload_to='product-type-images', blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    percentage_commission = models.DecimalField(max_digits=50, decimal_places=2, default=0, null=True, blank=True)
    fixed_commission = models.DecimalField(max_digits=50, decimal_places=2, default=0, null=True, blank=True)
    commission_applicable = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Image(models.Model):
    image = models.ImageField(upload_to='product-images')
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Image'

    def get_image_url(self):
        if not self.image:
            return None
        else:
            return self.image.url


class Product(models.Model):
    store = models.ForeignKey("store.Store", on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=500, null=True, blank=True, editable=False)
    description = models.TextField(help_text='Describe the product', null=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, blank=True, null=True, related_name='category')
    sub_category = models.ForeignKey(ProductCategory, blank=True, null=True, on_delete=models.CASCADE)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.TextField(blank=True, null=True)
    status = models.CharField(choices=product_status_choices, max_length=10, default='pending')
    decline_reason = models.CharField(max_length=200, blank=True, null=True)

    # Recommended Product: should be updated to 'True' once the merchant makes' payment.
    is_featured = models.BooleanField(default=False)

    # View Count: number of times the product is viewed by users.
    view_count = models.PositiveBigIntegerField(default=0)
    last_viewed_date = models.DateTimeField(blank=True, null=True)

    # Top Selling: The highest sold product. Field updates when this product has been successfully paid for.
    sale_count = models.IntegerField(default=0)

    published_on = models.DateTimeField(blank=True, null=True)
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="product_checked_by")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="product_approved_by")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductDetail(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    # description = models.TextField(help_text='Describe the product')
    sku = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=100, default='White')
    weight = models.FloatField(default=0)
    length = models.FloatField(default=0)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    stock = models.IntegerField(default=1)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    discount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    low_stock_threshold = models.IntegerField(default=5)
    shipping_days = models.IntegerField(default=3)
    out_of_stock_date = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}: {self.product}'


class ProductImage(models.Model):
    product_detail = models.ForeignKey(ProductDetail, on_delete=models.CASCADE, related_name='product_detail')
    image = models.ForeignKey(Image, on_delete=models.CASCADE, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id}:{self.product_detail}'


class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    headline = models.CharField(max_length=250)
    review = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {}".format(self.user, self.product)


class ProductWishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {}".format(self.user, self.product)

    class Meta:
        verbose_name_plural = "Product Wishlists"


class Shipper(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    slug = models.CharField(max_length=20, unique=True)
    vat_fee = models.DecimalField(max_digits=10, decimal_places=2, default=7.5)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    cart_uid = models.CharField(max_length=100, default="", null=True, blank=True)
    status = models.CharField(max_length=20, default='open', choices=cart_status_choices)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.cart_uid}-{self.user}-{self.status}"


class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_detail = models.ForeignKey(ProductDetail, on_delete=models.CASCADE)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    quantity = models.IntegerField(default=0)
    discount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    # status = models.CharField(max_length=20, default='open', choices=cart_status_choices)
    shipper_name = models.CharField(max_length=200, null=True, blank=True)
    company_id = models.CharField(max_length=200, null=True, blank=True)
    delivery_fee = models.DecimalField(default=0, decimal_places=2, max_digits=50, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}: {} {}".format(self.id, self.cart, self.product_detail)


# class CartBill(models.Model):
#     cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
#     # shipper = models.ForeignKey(Shipper, on_delete=models.SET_NULL, blank=True, null=True)
#     shipper_name = models.CharField(max_length=100, default="")
#     item_total = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
#     discount = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
#     delivery_fee = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
#     management_fee = models.DecimalField(decimal_places=2, max_digits=10, default=0.0)
#     total = models.DecimalField(default=0.0, decimal_places=2, max_digits=10)
#     created_on = models.DateTimeField(auto_now_add=True)
#     updated_on = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return "{} {}".format(self.cart, self.total)


DEAL_DISCOUNT_TYPE_CHOICES = (
    ('fixed', 'Fixed Amount'), ('percentage', 'Percentage'), ('amount_off', 'Amount Off')
)
PROMO_TYPE = (
    ('banner', 'Banner'), ('deal', 'Deal'), ('promo', 'Promo')
)


class Promo(models.Model):
    title = models.CharField(max_length=100)
    slug = models.CharField(max_length=500, null=True, blank=True, editable=False)
    fixed_price = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, default=0)
    percentage_discount = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, default=0)
    amount_discount = models.DecimalField(max_digits=50, decimal_places=2, null=True, blank=True, default=0)
    discount_type = models.CharField(max_length=50, default='fixed', choices=DEAL_DISCOUNT_TYPE_CHOICES)
    promo_type = models.CharField(max_length=50, default='promo', choices=PROMO_TYPE)
    details = models.TextField(null=True, blank=True)
    merchant = models.ManyToManyField(Seller, blank=True)
    category = models.ManyToManyField(ProductCategory, blank=True)
    sub_category = models.ManyToManyField(ProductCategory, blank=True, related_name='sub_category')
    product_type = models.ManyToManyField(ProductType, blank=True)
    product = models.ManyToManyField(Product, blank=True)
    banner_image = models.ImageField(upload_to='promo-banners', null=True, blank=True)
    position = models.CharField(max_length=300, choices=BANNER_POSITION_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=50, default='active', choices=status_choice)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.merchant} - {self.status}"


class Order(models.Model):
    customer = models.ForeignKey("account.Profile", on_delete=models.SET_NULL, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    address = models.ForeignKey("account.Address", on_delete=models.SET_NULL, null=True)
    payment_status = models.CharField(max_length=200, choices=payment_status_choices, default="pending")
    created_on = models.DateTimeField(auto_now_add=True)
    updates_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ID: {self.id}, {self.customer} - {self.cart_id}"


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_detail = models.ForeignKey(ProductDetail, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=50, decimal_places=2, default=0)
    quantity = models.IntegerField(default=1)
    discount = models.DecimalField(max_digits=50, decimal_places=2, default=0)
    sub_total = models.DecimalField(max_digits=50, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=50, decimal_places=2, default=0)
    shipper_name = models.CharField(max_length=200, null=True, blank=True)
    company_id = models.CharField(max_length=200, null=True, blank=True)
    tracking_id = models.CharField(max_length=200, null=True, blank=True)
    waybill_no = models.CharField(max_length=200, null=True, blank=True)
    payment_method = models.CharField(max_length=200, null=True, blank=True)
    delivery_fee = models.DecimalField(default=0, decimal_places=2, max_digits=50, null=True, blank=True)
    status = models.CharField(max_length=50, choices=order_status_choices, default='paid')
    delivery_date = models.DateField(null=True, blank=True)
    booked = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    cancelled_on = models.DateTimeField(null=True, blank=True)
    packed_on = models.DateTimeField(null=True, blank=True)
    shipped_on = models.DateTimeField(null=True, blank=True)
    delivered_on = models.DateTimeField(null=True, blank=True)
    returned_on = models.DateTimeField(null=True, blank=True)
    payment_on = models.DateTimeField(null=True, blank=True)
    refunded_on = models.DateTimeField(null=True, blank=True)
    request_for_return = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Order Products"
        indexes = [
            models.Index(
                fields=['price', 'quantity', 'discount', 'total', 'status', 'delivery_date', 'created_on',
                        'updated_on', 'cancelled_on', 'packed_on', 'shipped_on', 'delivered_on', 'returned_on',
                        'payment_on', 'refunded_on', 'request_for_return']
            )
        ]

    def __str__(self):
        return "{}: {} {}".format(self.pk, self.order, self.product_detail)


class ReturnReason(models.Model):
    reason = models.CharField(max_length=200)

    def __str__(self):
        return self.reason


RETURNED_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('success', 'Success'),
    ('failed', 'Failed'),
    ('rejected', 'Rejected'),
)


class ReturnedProduct(models.Model):
    returned_by = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True)
    product = models.ForeignKey(OrderProduct, on_delete=models.CASCADE, )
    reason = models.ForeignKey(ReturnReason, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=50, choices=RETURNED_STATUS_CHOICES, default='pending', blank=True, null=True)
    payment_status = models.CharField(max_length=50, choices=RETURNED_STATUS_CHOICES, default='pending', blank=True,
                                      null=True)
    comment = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_by', blank=True, null=True,
                                   default='')
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} {} {}".format(self.returned_by, self.product, self.reason)

    class Meta:
        indexes = [
            models.Index(
                fields=['status', 'payment_status', 'created_on', 'updated_on']
            )
        ]


class ReturnProductImage(models.Model):
    return_product = models.ForeignKey(ReturnedProduct, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="returns", null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        # return f'{self.return_product} {self.image}'
        return f'{self.return_product}'


class OrderEntry(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True,)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    item_total = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    management_fee = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    delivery_fee = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    total = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    status = models.CharField(max_length=50, choices=order_entry_status, default='packed')
    notified_for = models.CharField(max_length=200, null=True, blank=True)
    order_no = models.CharField(max_length=100, blank=True, null=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    shipper_settled = models.BooleanField(null=True, blank=True, default=False)
    shipper_settled_date = models.DateTimeField(null=True, blank=True)
    merchant_settled = models.BooleanField(null=True, blank=True, default=False)
    merchant_settled_date = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "(ID: {}) - {}: {}".format(self.id, self.merchant, self.cart)

    class Meta:
        verbose_name_plural = "Order Entries"
        indexes = [
            models.Index(
                fields=['item_total', 'management_fee', 'delivery_fee', 'total', 'status', 'order_no', 'tracking_id',
                        'merchant_settled', 'created_on', 'updated_on']
            )
        ]


class DailyDeal(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ID {self.id}: - {self.product.name}"
