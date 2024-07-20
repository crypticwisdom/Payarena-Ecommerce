import csv
import datetime
import time
from io import StringIO
import pandas as pd
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F, Q, Count, Avg
from django.shortcuts import get_object_or_404

from account.models import Profile
from account.utils import create_account
from ecommerce.models import Product, ProductCategory, ProductType, ProductDetail, Brand, ProductImage, Image, \
    OrderProduct, ReturnedProduct, ProductReview
from ecommerce.serializers import OrderProductSerializer
from ecommerce.utils import decrypt_text
from home.utils import log_request, get_week_start_and_end_datetime, get_month_start_and_end_datetime, \
    get_year_start_and_end_datetime, get_previous_month_date
from .models import *
from store.models import Store
from module import apis
from merchant.serializers import ProductLowAndOutOffStockSerializer


def create_product(request, seller):
    data = request.data
    store = Store.objects.get(seller=seller)

    # Product Information
    name = data.get("name")
    description = data.get("description")
    cat_id = data.get("category_id")
    sub_cat_id = data.get("sub_category_id")
    prod_type_id = data.get("product_type_id")
    brand_id = data.get("brand_id")
    image_id = data.get('image_id', '')
    tag = data.get("tags", [])

    if not all([name, cat_id, sub_cat_id, prod_type_id, brand_id, image_id, description]):
        return False, "Name, description, image, category, sub category, brand, and product type are required fields", None

    category = ProductCategory.objects.get(id=cat_id)
    sub_category = ProductCategory.objects.get(id=sub_cat_id)
    prod_type = ProductType.objects.get(id=prod_type_id)
    brand = Brand.objects.get(id=brand_id)
    image = Image.objects.get(id=image_id)

    product, created = Product.objects.get_or_create(
        name=name, store=store, category=category, sub_category=sub_category, product_type=prod_type
    )
    product.brand = brand
    product.description = description
    product.image = image
    product.save()
    if tag:
        tagging = ", ".join(tag)
        product.tags = tagging
        product.save()

    # Product Variants
    variant = data.get("variants", [])
    if not variant:
        return False, "Please add at least one variant", None

    success, detail = add_or_update_product_detail(variant, product)
    if success is False:
        return False, detail, None

    return True, "Product added successfully", product


def add_or_update_product_detail(variants, product):
    try:
        variation_list = list()
        for variation in variants:
            product_variation = None
            variation_id = variation.get('id', '')
            sku = variation.get('sku', '')
            size = variation.get('size', '')
            color = variation.get('color', '')
            discount = variation.get('discount', 0.0)
            price = variation.get('price', 0.0)
            stock = variation.get('stock', 0)
            weight = variation.get('weight', 0)
            length = variation.get('length', 0)
            width = variation.get('width', 0)
            height = variation.get('height', 0)
            low_stock_threshold = variation.get('low_stock_threshold')
            images = variation.get('images', [])
            # if not all([price, stock, weight, length, width, height, low_stock_threshold]):
            #     return False, "Product detail information are required"
            if variation_id:
                product_variation = ProductDetail.objects.get(pk=variation_id)
                product_variation.sku = sku
                product_variation.size = size
                product_variation.color = color
                product_variation.discount = discount
                product_variation.price = price
                product_variation.stock = stock
                product_variation.weight = weight
                product_variation.length = length
                product_variation.width = width
                product_variation.height = height
                product_variation.low_stock_threshold = low_stock_threshold
                product_variation.save()
            else:
                product_variation = ProductDetail.objects.create(
                    product=product, sku=sku, size=size, color=color, discount=discount, price=price, stock=stock,
                    weight=weight, width=width, height=height, length=length, low_stock_threshold=low_stock_threshold
                )

            if product_variation.id not in variation_list:
                variation_list.append(product_variation.id)

            if product_variation:
                if images:
                    add_product_detail_images(images, product_variation)
        ProductDetail.objects.filter(product=product).exclude(id__in=variation_list).delete()
        return True, "Product variations added"

    except Exception as ex:
        log_request(f"An error occurred. Error: {ex}")


def add_product_detail_images(images, product_detail):
    try:
        ProductImage.objects.filter(product_detail=product_detail).delete()
        for image_obj in images:
            image_id = image_obj.get('id', '')
            image = Image.objects.get(pk=image_id)
            ProductImage.objects.create(product_detail=product_detail, image=image)
    except Exception as ex:
        log_request(f"An error occurred. Error: {ex}")


def update_product(request, product):
    data = request.data
    if 'name' in data:
        product.name = data.get('name', '')
    if 'status' in data:
        if request.user.is_staff:
            product.status = data.get('status', '')
            if data.get('status') == "declined":
                product.decline_reason = data.get('declined_reason', '')
            if data.get('status') == "approve":
                product.approved_by = request.user
                product.status = "active"
                product.published_on = datetime.datetime.now()
            if data.get('status') == "checked":
                product.checked_by = request.user
    if 'category_id' in data:
        category_id = data.get('category_id', '')
        category = ProductCategory.objects.get(pk=category_id)
        product.category = category
    if 'sub_category_id' in data:
        sub_category_id = data.get('sub_category_id', '')
        sub_category = ProductCategory.objects.get(pk=sub_category_id)
        product.sub_category = sub_category
    if 'product_type_id' in data:
        product_type_id = data.get('product_type_id', '')
        product_type = ProductType.objects.get(pk=product_type_id)
        product.product_type = product_type
    if 'brand_id' in data:
        brand_id = data.get('brand_id', '')
        brand = Brand.objects.get(pk=brand_id)
        product.brand = brand
    if 'image_id' in data:
        image_id = data.get('image_id', '')
        image = Image.objects.get(pk=image_id)
        product.image = image
    if 'tags' in data:
        tags = data.get('tags', [])
        if tags:
            product.tags = ', '.join(tags)
    product.save()
    if 'variants' not in data:
        return False, "Variant(s) required"
    # if 'variants' in data:
    variants = data.get('variants', [])
    success, detail = add_or_update_product_detail(variants, product)
    if success is False:
        return False, detail
    return success, product


def get_all_banks(profile):
    # Get Auth code
    token = decrypt_text(profile.pay_auth)
    success, response = apis.get_bank_codes(token)

    if success is False:
        return False, "An error occurred while fetching banks"

    return True, response['Data']


def validate_bank_details(account_number: str, account_name: str, bank_code: str):
    """
        Validate Bank details.
    """
    # success1, response1 = apis.get_bank_codes()

    # if success1 is False:
    #     return False, "Error while fetching bank codes"
    #
    # response1 = response1['Data']

    # bank_code: str = ""
    # for bank_item in response1:
    #     bank_name = str(str(bank_name).lower())
    #     bank_item['Name'] = str(bank_item['Name']).strip().lower()
    #     if bank_name.split(" ")[0] in bank_item['Name'] and bank_name.split(" ")[1] in bank_item['Name']:
    #         bank_code = bank_item['CBNCode']
    #         break
    #
    # if bank_code == "":
    #     return False, "Bank name not found"

    # Call bank enquiry
    # '/bank code/acct_number'

    success, response = apis.call_name_enquiry(bank_code=bank_code, account_number=account_number)
    if not success:
        return False, response

    account_name = account_name.lower().split(" ")
    response_name = str(response["NameEnquiryResponse"]["AccountName"]).lower().strip()

    # Check if first or last name in 'response_name'

    if not (account_name[0] in response_name or account_name[1] in response_name):
        return False, "First name or last name does not correspond with bank account name"

    return True, "Successfully validated bank details"


def create_seller(request, user, email, phone_number):
    store, seller, seller_detail, bank_account, = None, None, None, None
    try:
        first_name: str = request.data.get('first_name', None)
        if not first_name:
            return False, "First name is required"

        last_name: str = request.data.get('last_name', None)
        if not last_name:
            return False, "Last name is required"

        business_name: str = request.data.get("business_name", None)
        if not business_name:
            return False, "Business name is required"

        product_category: list = request.data.get("product_category", [])  # drop-down
        if not product_category:
            return False, "Product category is required"

        business_address: str = request.data.get("business_address", None)
        if not business_address:
            return False, "Business address is required"

        business_town: str = request.data.get("business_town", None)
        town_id: str = request.data.get("town_id", None)
        if not business_town:
            return False, "Business town is required"

        business_state: str = request.data.get("business_state", None)  # drop-down
        if not business_state:
            return False, "Business State is required"

        business_city: str = request.data.get("business_city", None)  # drop-down
        if not business_city:
            return False, "Business City is required"

        latitude: float = request.data.get("latitude", 0.0)  # drop-down
        # if not latitude:
        #     return False, "Latitude is required"

        longitude: float = request.data.get("longitude", 0.0)  # drop-down
        # if not longitude:
        #     return False, "Longitude is required"

        business_drop_off_address: str = request.data.get("business_drop_off_address", None)
        # if not business_drop_off_address:
        #     return False, "Business drop off address is required"

        business_type: str = request.data.get("business_type", None)
        if not business_type:
            return False, "Business type is required"

        bank_account_number: str = request.data.get("bank_account_number", None)
        if not bank_account_number:
            return False, "Bank account number is required"

        bank_code: str = request.data.get("bank_code", None)  # drop-down
        if not bank_code:
            return False, "Bank is required"

        bank_account_name: str = request.data.get("bank_account_name", None)
        if not bank_account_name:
            return False, "Bank account name is required"
        bank_account_name = bank_account_name.strip()
        # ---------------------------- Check Bank Details ----------------------------
        success, msg = validate_bank_details(account_number=bank_account_number, account_name=bank_account_name,
                                             bank_code=bank_code)
        if not success:
            return False, msg

        # Get bank name
        auth_user = Profile.objects.get(user=request.user)
        success, detail = get_all_banks(auth_user)
        # detail = [{"Name": "Access Bank", "CBNCode": "044"}]
        bank_name = ""
        if success is True:
            result = [bank["Name"] for bank in detail if bank["CBNCode"] == bank_code]
            bank_name = str(result[0])
        # ----------------------------------------------------------------------------

        # directors = request.data.get("directors", [])
        market_size: int = request.data.get("market_size", None)
        number_of_outlets: int = request.data.get("number_of_outlets", None)
        maximum_price_range: float = request.data.get("maximum_price_range", None)  # drop-down

        if not str(bank_account_number).isnumeric():
            if len(bank_account_number) != 10:
                return False, "Invalid account number format"

        # -------------------------------------------------------------------------------------
        user.first_name = first_name.capitalize()
        user.last_name = last_name.capitalize()
        user.email = email
        user.save()

        # Create Seller
        seller, created = Seller.objects.get_or_create(user=user)
        seller.phone_number = phone_number
        seller.address = business_address
        seller.town = business_town
        seller.city = business_city
        seller.state = business_state
        seller.town_id = town_id
        seller.longitude = longitude
        seller.latitude = latitude
        seller.save()
        # Create seller detail
        seller_detail, created = SellerDetail.objects.get_or_create(seller=seller)
        seller_detail.market_size = market_size
        seller_detail.business_type = business_type
        seller_detail.number_of_outlets = number_of_outlets
        seller_detail.maximum_price_range = maximum_price_range
        seller_detail.business_address = business_address
        seller_detail.business_city = business_city
        seller_detail.business_state = business_state
        seller_detail.business_drop_off_address = business_drop_off_address
        seller_detail.save()

        # Create Bank Seller Account
        bank_account = BankAccount.objects.create(
            seller=seller, bank_name=bank_name, account_name=bank_account_name,
            account_number=bank_account_number, bank_code=bank_code
        )

        # Create Store for seller
        store, created = Store.objects.get_or_create(seller=seller, name=business_name.capitalize())

        if seller is None or not seller:
            return False, "Failed to create a Seller Instance"

        if business_type == "unregistered-individual-business":
            seller_detail.company_name = business_name
            seller_detail.save()
            if product_category:
                store.categories.clear()

                for item in product_category:
                    product_category = ProductCategory.objects.get(id=item)
                    store.categories.add(product_category)

            # send email notification
            return True, f"Created {business_name}"
        elif business_type == "registered-individual-business":
            company_name: str = request.data.get("company_name", None)
            company_type: str = request.data.get("company_type", None)
            cac_number = request.data.get("cac_number", None)
            company_tin_number = request.data.get("company_tin_number", None)

            if not company_name:
                return False, "Company name is required"

            if company_type not in ['sole-proprietorship', 'partnership']:
                return False, "Company type is required"

            if not cac_number:
                return False, "CAC Number is required"

            if not company_tin_number:
                return False, "Company TIN number is required"

            if not market_size:
                return False, "Market size is required"

            if not number_of_outlets:
                return False, "Number of outlet is required"

            if not maximum_price_range:
                return False, "Maximum price range is required"

            # Update seller_detail
            seller_detail.company_name = company_name.capitalize()
            seller_detail.company_type = company_type
            seller_detail.cac_number = cac_number
            seller_detail.company_tin_number = company_tin_number
            seller_detail.save()

            # send email notification
            return True, f"Created {business_name}"
        elif business_type == "limited-liability-company":

            company_name = request.data.get("company_name", None)
            cac_number = request.data.get("cac_number", None)
            company_tin_number = request.data.get("company_tin_number", None)
            directors = request.data.get("directors", [])

            if not company_name:
                return False, "Company name is required"

            # if company_type not in ['sole-proprietorship', 'partnership']:
            #     return "Company type is required", False
            company_type = "partnership"

            if not cac_number:
                return False, "CAC Number is required"

            if not company_tin_number:
                return False, "Company TIN number is required"

            if not market_size:
                return False, "Market size is required"

            if not number_of_outlets:
                return False, "Number of outlet is required"

            if not maximum_price_range:
                return False, "Maximum price range is required"

            if not directors:
                return False, "Please input your partner's name and number."

            # directors // expect a dictionary --> [
            #          ->                             {
            #                                               'name': 'Nwachukwu Wisdom',
            #          ->                                   'phone number': 08057784796
            #                                           }
            #          ->                          ]

            # Update seller_detail
            seller_detail.company_name = company_name
            seller_detail.company_type = company_type
            seller_detail.cac_number = cac_number
            seller_detail.company_tin_number = company_tin_number

            for item in directors:
                if item['name'] and item['phone_number'] and ['address']:
                    direct = Director.objects.create(name=item['name'],
                                                     phone_number=f"+234{item['phone_number'][-10:]}")
                    seller_detail.director = direct
            seller_detail.save()

            return True, f"Created {company_name}"

        else:
            return False, "Invalid Business Type"
    except (Exception,) as err:
        # store, seller, seller_detail, bank_account
        message = None
        # Delete 'store' instance when an 'Error' occur.
        if store is not None:
            store.delete()

        # Delete 'seller' instance when an 'Error' occur.
        if seller is not None:
            seller.delete()

        # Delete 'seller_detail' instance when an 'Error' occur.
        if seller_detail is not None:
            seller_detail.delete()

        # Delete 'bank_account' instance when an 'Error' occur.
        if bank_account is not None:
            bank_account.delete()

        # Check: if this user is not an authenticated user trying to register.
        # User instance will be created for this type of 'user' but he would need to login to complete registration
        if request.user.is_authenticated is False and user is not None:
            return True, "improper merchant creation"
        return False, f"{err}."


def update_seller(request, seller_id):
    # store, seller, seller_detail, bank_account, = None, None, None, None
    seller = Seller.objects.get(id=seller_id)
    try:
        business_name: str = request.data.get("business_name")
        product_category: list = request.data.get("product_category", [])  # drop-down
        business_address: str = request.data.get("business_address")
        business_town: str = request.data.get("business_town")
        town_id: str = request.data.get("town_id")
        business_state: str = request.data.get("business_state")  # drop-down
        business_city: str = request.data.get("business_city")  # drop-down
        latitude: float = request.data.get("latitude")  # drop-down
        longitude: float = request.data.get("longitude")  # drop-down
        business_drop_off_address: str = request.data.get("business_drop_off_address")
        business_type: str = request.data.get("business_type")
        bank_account_number: str = request.data.get("bank_account_number")
        bank_code: str = request.data.get("bank_code")  # drop-down
        bank_account_name: str = request.data.get("bank_account_name")
        bank_account_name = bank_account_name.strip()

        status: str = request.data.get("status")

        if status == "checked":
            seller.status = status
            seller.checked_by = request.user

        seller.address = business_address
        seller.town = business_town
        seller.town_id = town_id
        seller.city = business_city
        seller.state = business_state
        if longitude:
            seller.longitude = longitude
        if latitude:
            seller.latitude = latitude
        seller.save()

        # ---------------------------- Check Bank Details ----------------------------
        bank_name = ""
        if bank_account_name and bank_code:
            success, msg = validate_bank_details(
                account_number=bank_account_number, account_name=bank_account_name, bank_code=bank_code
            )
            if not success:
                return False, msg

            # Get bank name
            auth_user = Profile.objects.get(user=request.user)
            success, detail = get_all_banks(auth_user)
            if success is True:
                result = [bank["Name"] for bank in detail if bank["CBNCode"] == bank_code]
                bank_name = str(result[0])

        # ----------------------------------------------------------------------------

        # directors = request.data.get("directors", [])
        market_size: int = request.data.get("market_size")
        number_of_outlets: int = request.data.get("number_of_outlets")
        maximum_price_range: float = request.data.get("maximum_price_range")  # drop-down

        if not str(bank_account_number).isnumeric():
            if len(bank_account_number) != 10:
                return False, "Invalid account number format"

        # -------------------------------------------------------------------------------------
        store = Store.objects.filter(seller=seller).last()

        seller_detail = SellerDetail.objects.get(seller=seller)
        seller_detail.market_size = market_size
        seller_detail.business_type = business_type
        seller_detail.number_of_outlets = number_of_outlets
        seller_detail.maximum_price_range = maximum_price_range
        if business_name:
            store.name = business_name.capitalize()
            seller_detail.company_name = business_name.capitalize()
        store.save()
        seller_detail.save()

        bank_account = BankAccount.objects.get(seller=seller)
        bank_account.bank_name = bank_name
        bank_account.bank_code = bank_code
        bank_account.account_name = bank_account_name
        bank_account.account_number = bank_account_number
        bank_account.save()

        if product_category:
            store.categories.clear()

            for item in product_category:
                product_category = ProductCategory.objects.get(id=item)
                store.categories.add(product_category)

            # send email notification
            return True, f"Updated {store.name}"
        elif business_type == "limited-liability-company":
            directors = request.data.get("directors", [])
            company_type = "partnership"

            # directors // expect a dictionary --> [
            #          ->                             {
            #                                               'name': 'Nwachukwu Wisdom',
            #          ->                                   'phone number': 08057784796
            #                                           }
            #          ->                          ]

            seller_detail.company_type = company_type

            for item in directors:
                if item['name'] and item['phone_number'] and ['address']:
                    direct = Director.objects.create(name=item['name'],
                                                     phone_number=f"+234{item['phone_number'][-10:]}")
                    seller_detail.director = direct
            seller_detail.save()

            return True, f"Updated {store.name}"

        else:
            return False, "Invalid Business Type"
    except (Exception,) as err:
        return False, f"{err}."


def get_total_sales(store):
    total_sales = 0
    total_sales_data: OrderProduct = \
        OrderProduct.objects.filter(product_detail__product__store=store, order__payment_status="success"
                                    ).aggregate(total_sales=Sum('sub_total'))['total_sales']
    if total_sales_data:
        total_sales = total_sales_data
    return total_sales


def get_sales_data(store=None):
    sales = dict()
    weekly = []
    monthly = []
    yearly = []
    current_date = datetime.datetime.now()
    for delta in range(6, -1, -1):
        week_total_sales = 0
        month_total_sales = 0
        year_total_sales = 0
        week_date = current_date - relativedelta(weeks=delta)
        month_date = current_date - relativedelta(months=delta)
        year_date = current_date - relativedelta(years=delta)
        week_start, week_end = get_week_start_and_end_datetime(week_date)
        month_start, month_end = get_month_start_and_end_datetime(month_date)
        year_start, year_end = get_year_start_and_end_datetime(year_date)
        # print(year_start, year_end)
        query = Q(order__payment_status="success")
        if store:
            query &= Q(product_detail__product__store=store)
        total_sales = OrderProduct.objects.filter(query, created_on__gte=week_start, created_on__lte=week_end
                                                  ).aggregate(total_sales=Sum('total'))['total_sales']

        if total_sales:
            week_total_sales = total_sales
        weekly.append({"week": week_start.strftime("%d %b"), "sales": week_total_sales})
        total_sales = OrderProduct.objects.filter(
            query, created_on__gte=month_start, created_on__lte=month_end).aggregate(
            total_sales=Sum('total'))['total_sales']
        if total_sales:
            month_total_sales = total_sales
        monthly.append({"month": month_start.strftime("%b"), "sales": month_total_sales})
        total_sales = OrderProduct.objects.filter(query, created_on__gte=year_start, created_on__lte=year_end
                                                  ).aggregate(total_sales=Sum('total'))['total_sales']
        if total_sales:
            year_total_sales = total_sales
        yearly.append({"year": year_start.strftime("%Y"), "sales": year_total_sales})
    sales['weekly'] = weekly
    sales['monthly'] = monthly
    sales['yearly'] = yearly
    return sales


def get_best_sellers_data(store, request):
    best_sellers = []
    query_set = OrderProduct.objects.filter(product_detail__product__store=store, order__payment_status="success"
                                            ).values('product_detail__id').annotate(Sum('quantity')).order_by(
        '-quantity__sum')[:4]
    for data in query_set:
        product = dict()
        product_variant = ProductDetail.objects.get(pk=data['product_detail__id'])
        product['id'] = product_variant.product.id
        product['sku'] = product_variant.sku
        product['name'] = product_variant.product.name
        if product_variant.product.image:
            product['image'] = request.build_absolute_uri(product_variant.product.image.image.url)
        else:
            product['image'] = None
        product['price'] = product_variant.price
        product['units'] = data['quantity__sum']
        best_sellers.append(product)
    return best_sellers


def get_top_categories_data(store):
    top_categories = []
    query_set = OrderProduct.objects.filter(product_detail__product__store=store, order__payment_status="success"
                                            ).values(
        'product_detail__product__category__id',
        'product_detail__product__category__name').annotate(
        Sum('quantity')).order_by('-quantity__sum')[:6]
    for order_product in query_set:
        category = dict()
        category['id'] = order_product['product_detail__product__category__id']
        category['name'] = order_product['product_detail__product__category__name']
        category['units'] = order_product['quantity__sum']
        top_categories.append(category)
    return top_categories


def get_recent_orders_data(request, store):
    serializer = OrderProductSerializer(
        OrderProduct.objects.filter(product_detail__product__store=store, order__payment_status="success"
                                    ).order_by('-created_on')[:10],
        many=True, context={"request": request})
    return serializer.data


def get_low_in_stock(store, request):
    # used the F() to compare 'low_stock_threshold' and 'stock' fields in ProductDetail, it returns a queryset of
    # ProductDetail instances that their 'low_stock_threshold' fields are greater than their 'stock' fields.
    low_in_stock = ProductDetail.objects.filter(product__store=store,
                                                low_stock_threshold__gt=F('stock'), stock__gte=1).order_by('id')[:10]

    serialized_data = ProductLowAndOutOffStockSerializer(low_in_stock, many=True, context={"request": request})
    return serialized_data.data


def out_of_stock(store, request):
    out_off_stock = ProductDetail.objects.filter(product__store=store, stock=0).order_by('id')[:10]
    serialized_data = ProductLowAndOutOffStockSerializer(out_off_stock, many=True, context={"request": request})
    return serialized_data.data


def get_dashboard_data(store, request):
    data = dict()
    data['store_name'] = store.name
    data['total_orders'] = OrderProduct.objects.filter(product_detail__product__store=store,
                                                       order__payment_status="success").count()
    data['total_sales'] = get_total_sales(store)
    data['product_views'] = Product.objects.filter(store=store).aggregate(Sum('view_count'))['view_count__sum']
    data['total_product'] = ProductDetail.objects.filter(product__store=store).aggregate(Sum('stock'))['stock__sum']
    data['returned_product_count'] = ReturnedProduct.objects.filter(product__product_detail__product__store=store,
                                                                    status="approved").count()
    data['sales'] = get_sales_data(store)
    data['low_in_stock'] = get_low_in_stock(store, request)
    data['out_of_stock'] = out_of_stock(store, request)
    data['best_sellers'] = get_best_sellers_data(store, request)
    # data['sales_analytics'] = ""
    # data['transactions'] = "Still pending ... [Transaction has no relation to merchant.]"
    # data['top_categories'] = get_top_categories_data(store)
    data['recent_orders'] = get_recent_orders_data(request, store)
    data['best_selling_product'] = get_seller_best_selling_product(store)
    return data


def get_seller_best_selling_product(store):
    best_selling_products = Product.objects.filter(store=store).order_by("-sale_count")[:10]

    # if date_from and date_to:
    #     best_selling_products = Product.objects.filter(store=store, updated_on__range=(start_date, end_date)).order_by(
    #         "-sale_count")[:10]
    result = list()
    for product in best_selling_products:
        data = dict()
        data["id"] = product.id
        data["name"] = product.name
        data["category"] = product.category.name
        data["product_type"] = product.product_type.name
        data["sale_count"] = product.sale_count
        result.append(data)
    return result


def get_best_selling_product(request, seller=None, date_from=None, date_to=None):
    present_date = datetime.datetime.now()
    last_3_month = get_previous_month_date(date=present_date, delta=3)
    product_list = list()
    result = list()
    query = Q(
        order__payment_status="success", product_detail__product__store__is_active=True,
        product_detail__product__store__seller__status='active'
    )
    if seller:
        query &= Q(product_detail__product__store__seller=seller)

    # GET orderProducts within period
    sold = OrderProduct.objects.filter(query, created_on__range=[last_3_month, present_date])
    if not sold:
        last_12_month = get_previous_month_date(date=present_date, delta=12)
        sold = OrderProduct.objects.filter(query, created_on__range=[last_12_month, present_date])
    if date_from and date_to:
        sold = OrderProduct.objects.filter(query, created_on__range=[date_from, date_to])

    sold = sold.values("product_detail__product").annotate(ordered_count=Count('product_detail')).order_by(
        "-ordered_count")[:10]
    ordered_products = [{"product": prod['product_detail__product'],
                         "count": prod['ordered_count']} for prod in sold]
    for order_product_list in ordered_products:
        product = order_product_list['product']
        sales_count = order_product_list['count']
        if product not in product_list:
            stock_count = ProductDetail.objects.filter(product=product).aggregate(Sum('stock')).get(
                'stock__sum') or 0
            brand = None
            product_detail = ProductDetail.objects.filter(product=product).first()
            if product_detail.product.brand:
                brand = product_detail.product.brand.name
            average_rating = ProductReview.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg'] or 0

            data = dict()
            data["product_id"] = product_detail.product.id
            data["product_name"] = product_detail.product.name
            if product_detail.product.image:
                data["image"] = request.build_absolute_uri(product_detail.product.image.image.url)
            else:
                data["image"] = None
            data["category_name"] = product_detail.product.category.name
            data["brand_name"] = brand
            data["store_name"] = product_detail.product.store.name
            data["store_id"] = product_detail.product.store.id
            data["total_stock"] = stock_count
            data["rating"] = average_rating
            data["sale_count"] = sales_count
            data["product_detail_id"] = product_detail.id
            data["size"] = product_detail.size
            data["color"] = product_detail.color
            data["discount"] = product_detail.discount
            data["price"] = product_detail.price
            data["stock"] = product_detail.stock
            result.append(data)
            product_list.append(product)

    return result


def bulk_upload_thread(user, upload):
    file = upload.file.read().decode('utf-8', 'ignore')
    read = csv.reader(StringIO(file), delimiter=",")
    next(read)
    error_list = list()

    name = ""
    for row in read:
        try:
            name = row[0]
            description = row[1]
            category_name = row[2]
            sub_category_name = row[3]
            product_type_name = row[4]
            brand_name = row[5]
            sku = row[6]
            size = row[7]
            color = row[8]
            discount = row[9]
            price = row[10]
            stock = row[11]
            weight = row[12]
            length = row[13]
            width = row[14]
            height = row[15]
            low_stock_threshold = row[16]
            store_name = row[17]

            if user.is_staff:
                seller_id = row[18]
                merchant = get_object_or_404(Seller, id=seller_id)
            else:
                merchant = get_object_or_404(Seller, user=user)

            category = ProductCategory.objects.get(name__iexact=category_name, parent__isnull=True)
            sub_category = ProductCategory.objects.get(name__iexact=sub_category_name, parent__isnull=False)
            prod_type = ProductType.objects.get(name__iexact=product_type_name)
            brand = Brand.objects.get(name__iexact=brand_name)
            store = Store.objects.get(name__iexact=store_name, seller=merchant)

            # Create Product
            product, created = Product.objects.get_or_create(
                name=name, store=store, category=category, sub_category=sub_category, product_type=prod_type
            )
            product.brand = brand
            product.description = description
            product.save()

            # Create Product Detail
            ProductDetail.objects.create(
                product=product, sku=sku, size=size, color=color, discount=discount, price=price, stock=stock,
                weight=weight, width=width, height=height, length=length, low_stock_threshold=low_stock_threshold
            )
            log_request(f"Product Name: {name} created successfully")

        except Exception as ex:
            error_list.append(f"Product Name: {name} - {ex}")
            log_request(f"Product Name: {name} - {ex}")

    # Update uploaded file
    upload.errors = error_list
    upload.used = True
    upload.save()

    return True


def bulk_upload_merchant_thread(upload, request):
    from account.utils import register_payarena_user
    error_list, success_count, failed_count, record_count = list(), 0, 0, 0
    try:

        excel_file_dataframe = pd.read_excel(upload.file)
        record_count = len(excel_file_dataframe)

        for index, row in excel_file_dataframe.iterrows():
            row = dict(row)
            row = {f'{key}': f'{value}' for key, value in row.items()}

            merchant_id_col = row.get('MERCHANT ID') if row.get('MERCHANT ID') != "nan" else None
            vendor_code_col = row.get('VENDOR CODE') if row.get('VENDOR CODE') != 'nan' else None
            merchant_first_name_col = row.get('MERCHANT FIRST NAME') if row.get('MERCHANT FIRST NAME') != 'nan' else None
            merchant_last_name_col = row.get('MERCHANT LAST NAME') if row.get('MERCHANT LAST NAME') != 'nan' else None

            store_name_col = row.get('STORE NAME') if row.get('STORE NAME') != 'nan' else None
            contact_name_col = row.get('CONTACT NAME') if row.get('CONTACT NAME') != 'nan' else None
            default_password_col = row.get('DEFAULT PASSWORD') if row.get('DEFAULT PASSWORD') != 'nan' else None
            fep_type_fee_col = row.get('FEP TYPE (FEE)') if row.get('FEP TYPE (FEE)') != 'nan' else None
            fep_type_rate_col = row.get('FEP TYPE (RATE)') if row.get('FEP TYPE (RATE)') != 'nan' else None
            fep_type_flat_col = row.get('FEP TYPE (FLAT)') if row.get('FEP TYPE (FLAT)') != 'nan' else None
            phone_number_col = row.get('PHONE NUMBER') if row.get('PHONE NUMBER') != 'nan' else None
            physical_address_col = row.get('PHYSICAL ADDRESS') if row.get('PHYSICAL ADDRESS') != 'nan' else None
            terminal_model_code = row.get('TERMINAL MODEL CODE') if row.get('TERMINAL MODEL CODE') != 'nan' else None
            terminal_id_col = row.get('TERMINAL ID') if row.get('TERMINAL ID') != 'nan' else None
            bank_code_col = row.get('BANK CODE') if row.get('BANK CODE') != 'nan' else None
            account_name_col = row.get('ACCOUNT NAME') if row.get('ACCOUNT NAME') != 'nan' else None
            bank_name_col = row.get('BANK NAME') if row.get('BANK NAME') != 'nan' else None
            bank_account_no_col = row.get('BANK ACC NO') if row.get('BANK ACC NO') != 'nan' else None
            email_col = row.get('EMAIL') if row.get('EMAIL') != 'nan' else None

            # exclude 'fep_type_flat_col'
            all_fields = all([merchant_id_col, vendor_code_col, merchant_first_name_col, merchant_last_name_col,
                  store_name_col, contact_name_col, default_password_col, fep_type_fee_col, fep_type_rate_col,
                  phone_number_col, physical_address_col, terminal_model_code, terminal_id_col,
                  bank_code_col, account_name_col, bank_name_col, bank_account_no_col])

            # If fields contains 'nan' (None), ignore and move to the next record
            if not all_fields:
                error_list.append(f"Error: Incomplete merchant record for: {row}")
                failed_count += 1
                continue

            if all_fields:
                # create user instance
                merchant_first_name_col = str(merchant_first_name_col).capitalize()
                merchant_last_name_col = str(merchant_last_name_col).capitalize()
                phone_number_col = str(phone_number_col)

                if phone_number_col is not None and str(phone_number_col[-10:]).isnumeric():
                    phone_number_col = f"{234}{phone_number_col[-10:]}"

                a_success, detail = register_payarena_user(
                    email_col, phone_number_col, merchant_first_name_col, merchant_last_name_col, default_password_col
                )
                if not a_success:
                    error_list.append(f"Error: An error occurred while creating user on Payarena "
                                      f"{email_col}\n{merchant_first_name_col} {merchant_last_name_col}")
                    failed_count += 1

                success, profile_or_err_msg = create_account(email_col, phone_number_col, default_password_col,
                                                             merchant_first_name_col, merchant_last_name_col)

                if not success:
                    error_list.append(f"Error: Failed to create a User Instance {merchant_first_name_col} "
                                      f"{merchant_last_name_col} {merchant_id_col}; {profile_or_err_msg}")
                    failed_count += 1
                    continue

                try:
                    seller = Seller.objects.create(
                        user=profile_or_err_msg.user,
                        phone_number=phone_number_col,
                        address=physical_address_col,
                        merchant_id=merchant_id_col,
                        feel=fep_type_flat_col,
                        status='approve',
                        checked_by=request.user,
                        approved_by=request.user
                    )

                except (Exception, ) as err:
                    error_list.append(f"Error: Failed to create a Seller Instance {merchant_first_name_col} "
                                      f"{merchant_last_name_col} {merchant_id_col}; Error: {err}")
                    failed_count += 1
                    continue

                if seller is None:
                    error_list.append(f"Error: Failed to create a Seller Instance {merchant_first_name_col} "
                                      f"{merchant_last_name_col} {merchant_id_col}")
                    failed_count += 1
                    continue

                # Create seller detail
                seller_detail, created = SellerDetail.objects.get_or_create(seller=seller)
                seller_detail.business_type = 'registered-individual-business'
                seller_detail.company_name = str(store_name_col).capitalize()
                seller_detail.company_type = 'sole-proprietorship'
                seller_detail.business_address = physical_address_col
                seller_detail.verified = True
                seller_detail.save()

                if seller_detail is None or not created:
                    error_list.append(f"Error: Failed to create a Seller Detail Instance {merchant_first_name_col} "
                                      f"{merchant_last_name_col} {merchant_id_col}")
                    failed_count += 1
                    continue

                # Create Bank Seller Account
                bank_account = BankAccount.objects.create(
                    seller=seller, bank_name=bank_name_col, account_name=account_name_col,
                    account_number=bank_account_no_col, bank_code=bank_code_col
                )

                if bank_account is None:
                    error_list.append(f"Error: Failed to create Bank Account Instance for "
                                      f"{merchant_first_name_col} {merchant_last_name_col} {merchant_id_col}")
                    failed_count += 1
                    continue

                # Create Store for seller
                store = Store.objects.create(
                    seller=seller, name=str(store_name_col).capitalize(), is_active=True)

                if store is None:
                    error_list.append(f"Error: Failed to create Store Instance for "
                                      f"{merchant_first_name_col} {merchant_last_name_col} {merchant_id_col}")
                    failed_count += 1
                    continue

                # use flat type and make sure feel is set to 2.5
                if success and seller and seller_detail and bank_account and store:
                    error_list.append("Info: Successfully Create account for "
                                      f"{merchant_first_name_col} {merchant_last_name_col} {merchant_id_col}")
                    success_count += 1

        error_list.append(f"Info: Successful Creation Count: {success_count}; Failed Creation Count: {failed_count}; "
                          f"Total Record Count: {record_count}")
    except (Exception, ) as err:
        error_list.append(err)
        return False

    finally:
        upload.errors = error_list

    # Update uploaded file
    upload.used = True
    upload.save()
    return True
