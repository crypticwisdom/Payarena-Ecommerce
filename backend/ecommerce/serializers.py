from django.conf import settings
from django.db.models import Sum, Avg

from account.models import Profile
from superadmin.exceptions import InvalidRequestException
from .models import ProductCategory, Product, ProductDetail, ProductImage, ProductReview, Promo, ProductType, \
    ProductWishlist, CartProduct, OrderProduct, Order, ReturnedProduct, ReturnProductImage, ReturnReason, Brand, \
    DailyDeal
from rest_framework import serializers


# Hot New Arrivals Serializers #
class ProductDetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get("request")
        return [str(request.build_absolute_uri(instance.image.image.url))
                for instance in ProductImage.objects.filter(product_detail=obj)]

    class Meta:
        model = ProductDetail
        exclude = []


class VariantImageSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        request = self.context.get("request")
        data = []
        for instance in ProductImage.objects.filter(product_detail=obj):
            data.append({"image_id": instance.image.id, "image_url": str(request.build_absolute_uri(instance.image.image.url))})
        return data

    class Meta:
        model = ProductDetail
        exclude = []


class SimilarProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()

    def get_price(self, obj):
        query = ProductDetail.objects.filter(product=obj).first()
        if query:
            return query.price
        return None

    def get_discount(self, obj):
        query = ProductDetail.objects.filter(product=obj).first()
        if query:
            return query.discount
        return None

    def get_average_rating(self, obj):
        rating = 0
        query_set = ProductReview.objects.filter(product=obj).aggregate(Avg('rating'))
        if query_set:
            rating = query_set['rating__avg']
        return rating

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                image = request.build_absolute_uri(obj.image.image.url)
                return image
            return obj.image.image.url
        return None

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "is_featured", "average_rating", "image", "price", "discount"]


class ProductSerializer(serializers.ModelSerializer):
    store = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    brand_id = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    product_detail = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    category_id = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_slug = serializers.SerializerMethodField()
    sub_category_id = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()
    sub_category_slug = serializers.SerializerMethodField()
    product_type = serializers.SerializerMethodField()
    product_type_id = serializers.SerializerMethodField()
    similar = serializers.SerializerMethodField()
    also_viewed_by_others = serializers.SerializerMethodField()
    recently_viewed = serializers.SerializerMethodField()
    merchant_id = serializers.CharField(source="store.seller.merchant_id")
    checked_by = serializers.SerializerMethodField()
    approved_by = serializers.SerializerMethodField()

    def get_recently_viewed(self, obj):
        from store.serializers import StoreProductSerializer

        request = self.context.get("request")
        recent_view = Product.objects.filter(
            status="active", store__is_active=True).order_by("-last_viewed_date").exclude(pk=obj.id)[:10]
        if request.user.is_authenticated:
            if Profile.objects.filter(user=request.user).exists():
                shopper = Profile.objects.get(user=request.user)
                if shopper.recent_viewed_products:
                    shopper_views = shopper.recent_viewed_products.split(",")[1:]
                    recent_view = Product.objects.filter(id__in=shopper_views, status="active", store__is_active=True).order_by("?")[:15]
        return StoreProductSerializer(recent_view, many=True, context={"request": request}).data

    def get_checked_by(self, obj):
        if obj.checked_by:
            return obj.checked_by.email
        return None

    def get_approved_by(self, obj):
        if obj.approved_by:
            return obj.approved_by.email
        return None

    def get_similar(self, obj):
        product = Product.objects.filter(
            store__is_active=True, status='active', product_type=obj.product_type
        ).order_by('?').exclude(pk=obj.id).distinct()
        if self.context.get('seller'):
            product = product.filter(store__seller=self.context.get('seller'))
        return SimilarProductSerializer(product[:int(settings.SIMILAR_PRODUCT_LIMIT)], many=True,
                                        context={"request": self.context.get("request")}).data

    def get_also_viewed_by_others(self, obj):
        viewed = Product.objects.filter(store__is_active=True, status='active',
                                        sub_category=obj.sub_category).order_by('?').exclude(pk=obj.id).distinct()
        if self.context.get('seller'):
            viewed = viewed.filter(store__seller=self.context.get('seller'))
        return SimilarProductSerializer(viewed[:int(settings.SIMILAR_PRODUCT_LIMIT)], many=True,
                                        context={"request": self.context.get("request")}).data

    def get_store(self, obj):
        return {"id": obj.store.id, "name": obj.store.name, "slug": obj.store.slug}

    def get_total_stock(self, obj):
        query = ProductDetail.objects.filter(product=obj)
        if query:
            return query.aggregate(Sum('stock')).get('stock__sum') or 0

    def get_brand(self, obj):
        if obj.brand:
            return obj.brand.name
        return None

    def get_brand_id(self, obj):
        if obj.brand:
            return obj.brand.id
        return None

    def get_average_rating(self, obj):
        rating = 0
        query_set = ProductReview.objects.filter(product=obj)
        if query_set:
            rating = query_set.aggregate(Avg('rating'))['rating__avg'] or 0
        return rating

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                image = request.build_absolute_uri(obj.image.image.url)
                return {"image_url": image, "image_id": obj.image.id}
            return obj.image.image.url
        return None

    def get_product_detail(self, obj):
        request = self.context.get("request")
        serializer = ProductDetailSerializer(ProductDetail.objects.filter(product=obj).order_by('-stock'),
                                             many=True, context={"request": request})
        return serializer.data

    def get_variants(self, obj):
        request = self.context.get("request")
        serializer = VariantImageSerializer(ProductDetail.objects.filter(product=obj).order_by('-stock'),
                                             many=True, context={"request": request})
        return serializer.data

    def get_category(self, obj):
        return obj.category.name

    def get_category_id(self, obj):
        return obj.category.id

    def get_category_slug(self, obj):
        return obj.category.slug

    def get_sub_category_id(self, obj):
        return obj.sub_category.id

    def get_sub_category(self, obj):
        return obj.sub_category.name

    def get_sub_category_slug(self, obj):
        return obj.sub_category.slug

    def get_product_type(self, obj):
        return obj.product_type.name

    def get_product_type_id(self, obj):
        return obj.product_type.id

    class Meta:
        model = Product
        exclude = []
# END #


class ProductTypeSerializer(serializers.ModelSerializer):
    sub_category_id = serializers.IntegerField(source="category.id")
    products = serializers.SerializerMethodField()

    def get_products(self, obj):
        request = self.context.get("request", None)
        container, details = list(), dict()

        if request is None:
            return []

        product_types = Product.objects.filter(product_type=obj, store__is_active=True, status='active').order_by('-id')[:10]
        for product in product_types:
            product_detail = ProductDetail.objects.filter(product=product).first()
            if product_detail:
                container.append({
                    "product_id": product_detail.id,
                    "product_name": product_detail.product.name,
                    "product_slug": product_detail.product.slug,
                    "product_image": request.build_absolute_uri(product_detail.product.image.get_image_url()),
                    "price": product_detail.price,
                    "discount": product_detail.discount,
                })
        return container

    class Meta:
        model = ProductType
        exclude = ["category"]


class CategoriesSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    sub_categories = serializers.SerializerMethodField()
    product_types = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    parent_category = serializers.SerializerMethodField()
    new_arrived_products = serializers.SerializerMethodField()

    def get_parent_category(self, obj):
        data = None
        if obj.parent:
            data = {"id": obj.parent.id, "name": obj.parent.name}
        return data

    def get_brand(self, obj):
        if not obj.parent:
            brand = [{"id": brand.id, "name": brand.name} for brand in obj.brands.all()]
            return brand
        return None

    def get_image(self, obj):
        image = None
        request = self.context.get('request')
        if obj.image:
            image = request.build_absolute_uri(obj.image.url)
        return image

    def get_sub_categories(self, obj):
        request = self.context.get("request")
        cat = None
        if ProductCategory.objects.filter(parent=obj).exists():
            cat = list()
            for sub_cat in ProductCategory.objects.filter(parent=obj):
                image = None
                if sub_cat.image:
                    image = f"{request.scheme}://{request.get_host()}{sub_cat.image.url}"
                cat.append({"id": sub_cat.id, "name": sub_cat.name, "slug": sub_cat.slug, "image": image})
        return cat

    def get_product_types(self, obj):
        prod_type = None
        request = self.context.get("request", None)
        if request:
            if ProductType.objects.filter(category=obj).exists():
                prod_type = ProductTypeSerializer(ProductType.objects.filter(category=obj), many=True, context={"request": request}).data
            return prod_type

    # Last 10 Products Under a Category or a Sub-Category.
    def get_new_arrived_products(self, obj):
        # print(obj.parent) // If obj.parent is None that means obj.parent is a sub-category and not a parent category.

        container, details = list(), dict()
        request = self.context.get("request", None)
        if not request:
            return []

        if obj.parent is None:
            query = Product.objects.filter(category__id=obj.id, store__is_active=True, status='active').order_by('-id')[:10]
        else:
            query = Product.objects.filter(sub_category__id=obj.id, store__is_active=True, status='active').order_by('-id')[:10]

        for product in query:
            price = discount = 0
            if ProductDetail.objects.filter(product=product).exists():
                product_detail = ProductDetail.objects.filter(product=product).last()
                price = product_detail.price
                discount = product_detail.discount
            container.append({
                "product_id": product.id,
                "product_name": product.name,
                "product_slug": product.slug,
                "product_image": request.build_absolute_uri(product.image.image.url),
                "price": price,
                "discount": discount,
            })
        return container

    class Meta:
        model = ProductCategory
        exclude = ["brands", "parent"]


class MallDealSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    banner_id = serializers.IntegerField(source="id")
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get("request")
        image = None
        if obj.banner_image:
            image = request.build_absolute_uri(obj.banner_image.url)
        return image

    def get_product(self, obj):
        request = self.context.get("request")
        result = list()
        for product in obj.product.all():
            price = product.productdetail_set.last().price
            discount = product.productdetail_set.last().discount
            p_discount = discount / price
            image = None
            if product.image:
                image = request.build_absolute_uri(product.image.image.url)
            data = {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'image': image,
                'price': price,
                'discount': discount,
                'percentage_discount': f"-{p_discount:.1%}",
                'category': product.category.name,
                'store_name': product.store.name,
                'seller_email': product.store.seller.user.email,
                'rating': product.productreview_set.all().aggregate(Avg('rating'))['rating__avg'] or 0
            }
            result.append(data)
        return result

    class Meta:
        model = Promo
        fields = ['banner_id', 'product', 'image', 'slug']
        depth = 1


class CartProductSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    item_price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_name(self, obj):
        if obj:
            return obj.product_detail.product.name
        return None

    def get_description(self, obj):
        if obj:
            return obj.product_detail.product.description
        return None

    def get_item_price(self, obj):
        if obj:
            return obj.product_detail.price * obj.quantity
        return None

    def get_image(self, obj):
        if self.context.get('request'):
            request = self.context.get('request')
            return request.build_absolute_uri(obj.product_detail.product.image.get_image_url())
        return obj.product_detail.product.image.get_image_url() or None

    class Meta:
        model = CartProduct
        fields = ["id", "name", "image", "description", "price", "quantity", "item_price", "discount", "product_detail"]


class ProductWishlistSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    def get_product(self, obj):
        product = None
        if obj.product:
            product = ProductSerializer(obj.product, context={"request": self.context.get("request")}).data
        return product

    class Meta:
        model = ProductWishlist
        exclude = []


class OrderProductSerializer(serializers.ModelSerializer):
    seller_id = serializers.IntegerField(source="product_detail.product.store.seller.id")
    store_name = serializers.CharField(source="product_detail.product.store.name")
    product_name = serializers.CharField(source="product_detail.product.name")
    category = serializers.CharField(source="product_detail.product.category.name")
    product_image = serializers.SerializerMethodField()

    def get_product_image(self, obj):
        request = self.context.get("request")
        image = None
        if obj.product_detail.product.image:
            image = request.build_absolute_uri(obj.product_detail.product.image.image.url)
        return image

    class Meta:
        model = OrderProduct
        exclude = ["product_detail"]


class OrderSerializer(serializers.ModelSerializer):
    order_products = serializers.SerializerMethodField()
    no_of_products = serializers.SerializerMethodField()
    order_calculation = serializers.SerializerMethodField()

    def get_order_calculation(self, obj):
        data = dict()
        order_product_total = OrderProduct.objects.filter(order=obj).aggregate(Sum("sub_total"))["sub_total__sum"] or 0
        shipping_fee_total = OrderProduct.objects.filter(order=obj).aggregate(Sum("delivery_fee"))["delivery_fee__sum"] or 0
        data["product_total"] = order_product_total
        data["shipping_fee"] = shipping_fee_total
        data["total"] = order_product_total + shipping_fee_total
        return data

    def get_no_of_products(self, obj):
        prod = 0
        if OrderProduct.objects.filter(order=obj).exists():
            prod = OrderProduct.objects.filter(order=obj).count()
        return prod

    def get_order_products(self, obj):
        if OrderProduct.objects.filter(order=obj).exists():
            return OrderProductSerializer(OrderProduct.objects.filter(order=obj), many=True, context={"request": self.context.get("request")}).data
        return None

    class Meta:
        model = Order
        exclude = ["customer"]
        depth = 1


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        exclude = []


class ReturnProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                image = request.build_absolute_uri(obj.image.url)
                return image
            return obj.image.url
        return None

    class Meta:
        model = ReturnProductImage
        exclude = ["id", "return_product", "image"]


class ReturnReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnReason
        exclude = []


class ReturnedProductSerializer(serializers.ModelSerializer):
    return_images = serializers.SerializerMethodField()
    return_date = serializers.SerializerMethodField()
    reason = ReturnReasonSerializer()

    def get_return_date(self, obj):
        if obj:
            return obj.created_on
        return None

    def get_return_images(self, obj):
        if ReturnProductImage.objects.filter(return_product=obj).exists():
            return_product_image = ReturnProductImage.objects.filter(return_product=obj)
            context = self.context.get("request")
            return ReturnProductImageSerializer(return_product_image, many=True, context={"request": context}).data
        return None

    class Meta:
        model = ReturnedProduct
        fields = ['id', 'returned_by', 'return_images', 'product', 'reason', 'status', 'payment_status', 'comment',
                  'return_date', 'updated_by', 'updated_on']


class ProductReviewSerializerOut(serializers.ModelSerializer):
    reviewed_by = serializers.CharField(source="user.get_full_name")

    class Meta:
        model = ProductReview
        exclude = ["user"]


class ProductReviewSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    product_id = serializers.IntegerField()
    rating = serializers.IntegerField()
    headline = serializers.CharField()
    content = serializers.CharField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        product = validated_data.get("product_id")
        headline = validated_data.get("headline")
        rating = validated_data.get("rating")
        content = validated_data.get("content")

        # Check if user has previously purchased product
        if not OrderProduct.objects.filter(order__customer__user=user, product_detail__product_id=product, status="delivered").exists():
            raise InvalidRequestException({"detail": "You have no recent purchase for selected product"})

        # create review
        review, _ = ProductReview.objects.get_or_create(user=user, product_id=product)
        review.headline = headline
        review.rating = rating
        review.review = content
        review.save()

        data = ProductReviewSerializerOut(review).data
        return data


# Mobile APP
class MobileCategorySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    sub_categories = serializers.SerializerMethodField()

    def get_sub_categories(self, obj):
        cat = None
        if ProductCategory.objects.filter(parent=obj).exists():
            cat = [category.id for category in ProductCategory.objects.filter(parent=obj)]
        return cat

    def get_products(self, obj):
        request = self.context.get("request")
        if Product.objects.filter(category=obj).exists():
            return ProductSerializer(Product.objects.filter(category=obj, status="active"), many=True, context={"request": request}).data

    class Meta:
        model = ProductCategory
        exclude = []


class DailyDealSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = DailyDeal
        exclude = []


# class ReturnReasonSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReturnReason
#         exclude = []


