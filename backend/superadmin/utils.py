import decimal
import json
import logging

from django.db.models import Q

from ecommerce.models import ProductCategory, ProductType, Product, Promo
from home.utils import log_request
from merchant.models import Seller
from superadmin.models import AdminUser


def create_or_update_category(data, image, cat_id=None):
    name = data.get("name")
    parent = data.get("parent")
    brands = data.get("brands")

    if cat_id:
        cat_obj = ProductCategory.objects.get(id=cat_id)
        cat_obj.name = name
        cat_obj.parent_id = parent
    else:
        cat_obj, _ = ProductCategory.objects.get_or_create(name=name, parent_id=parent)

    if image:
        cat_obj.image = image

    if brands:
        cat_obj.brands.clear()
        for brand in brands:
            try:
                cat_obj.brands.add(brand)
            except Exception as ex:
                logging.exception(ex)
    cat_obj.save()

    return cat_obj


def check_permission(request):
    admin_user = AdminUser.objects.get(user=request.user)
    if not (admin_user.role.admin_type == "super_admin" or admin_user.role.admin_type == "admin"):
        return False
    return True


def perform_banner_filter(request):
    query = Q(status='active')
    if request.data.get('merchant'):
        merchant = Seller.objects.filter(id__in=json.loads(request.data.get('merchant')))
        query &= Q(store__seller__in=merchant)
    if request.data.get('category'):
        cat = ProductCategory.objects.filter(id__in=json.loads(request.data.get('category')))
        query &= Q(category__in=cat)
    if request.data.get('sub_category'):
        sub_cat = ProductCategory.objects.filter(id__in=json.loads(request.data.get('sub_category')))
        query &= Q(sub_category__in=sub_cat)
    if request.data.get('product_type'):
        prod_type = ProductType.objects.filter(id__in=json.loads(request.data.get('product_type')))
        query &= Q(product_type__in=prod_type)
    if request.data.get('min_price'):
        query &= Q(productdetail__price__gte=request.data.get('min_price'))
    if request.data.get('max_price'):
        query &= Q(productdetail__price__lte=request.data.get('max_price'))
    if request.data.get('min_discount'):
        query &= Q(productdetail__discount__gte=request.data.get('min_discount'))
    if request.data.get('max_discount'):
        query &= Q(productdetail__discount__lte=request.data.get('max_discount'))

    result = Product.objects.filter(query, store__is_active=True, store__seller__status='active').distinct()

    return result


def create_or_edit_banner_obj(data, instance=None):
    name = data.get('title')
    image = data.getlist('banner_image')
    promo_type = data.get("promo_type")
    description = data.get("description")
    position = data.get("position")
    status = data.get("status")

    if not promo_type:
        return False, "Promo type is required"

    if not position:
        return False, "Please select advert position"

    discount_type = data.get("discount_type")
    fixed_price = data.get("fixed_price")
    percentage_discount = data.get("percentage_discount", 0)
    amount_discount = data.get("amount_discount", 0)

    if not discount_type:
        return False, "Please select a discount type"
    if discount_type == "fixed" and not fixed_price:
        return False, "Please set Fix Price"
    if discount_type == "percentage" and not percentage_discount:
        return False, "Please set Percentage Discount"
    if discount_type == "amount_off" and not amount_discount:
        return False, "Please set Amount Discount"

    if not data.get("product"):
        return False, "At least one product is required"

    if instance:
        obj = instance
    else:
        obj = Promo.objects.create(title=name)

    if status:
        obj.status = status
    if description:
        obj.details = description
    obj.title = name
    obj.promo_type = promo_type
    if image:
        obj.banner_image = image[0]
    obj.discount_type = discount_type
    obj.fixed_price = fixed_price
    obj.percentage_discount = percentage_discount
    obj.amount_discount = amount_discount

    if data.get("merchant"):
        obj.merchant.clear()
        for merchant in json.loads(data.get("merchant")):
            try:
                obj.merchant.add(merchant)
            except Exception as ex:
                log_request(ex)

    if data.get("category"):
        obj.category.clear()
        for category in json.loads(data.get("category")):
            try:
                obj.category.add(category)
            except Exception as ex:
                log_request(ex)

    if data.get("sub_category"):
        obj.sub_category.clear()
        for sub_category in json.loads(data.get("sub_category")):
            try:
                obj.sub_category.add(sub_category)
            except Exception as ex:
                log_request(ex)

    if data.get("product_type"):
        obj.product_type.clear()
        for product_type in json.loads(data.get("product_type")):
            try:
                obj.product_type.add(product_type)
            except Exception as ex:
                log_request(ex)

    obj.product.clear()
    for product in json.loads(data.get("product")):
        try:
            obj.product.add(product)
        except Exception as ex:
            log_request(ex)

    obj.position = position
    obj.save()

    # Update Product(s) Discount
    for prod in obj.product.all():
        discount = 0
        prod_detail_price = prod.productdetail_set.first().price
        prod_detail_all = prod.productdetail_set.all()
        if discount_type == "fixed" and fixed_price:
            discount = decimal.Decimal(fixed_price)
        if discount_type == "percentage" and percentage_discount:
            discount_amount = prod_detail_price * (decimal.Decimal(percentage_discount) / 100)
            discount = prod_detail_price - decimal.Decimal(discount_amount)
        if discount_type == "amount_off" and amount_discount:
            discount = prod_detail_price - decimal.Decimal(amount_discount)
        if obj.status == "inactive":
            discount = 0

        prod_detail_all.update(discount=discount)

    return True, obj


