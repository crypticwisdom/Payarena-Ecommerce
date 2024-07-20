from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ecommerce.serializers import ProductWishlistSerializer
from home.pagination import CustomPagination
from rest_framework.views import APIView
from rest_framework import generics, status

from .serializers import *
from .utils import create_or_update_store


class BrandView(APIView, CustomPagination):
    permission_classes = []

    def get(self, request, brand_id=None):
        if brand_id:
            serializer = BrandSerializer(get_object_or_404(Brand, id=brand_id)).data
        else:
            brands = self.paginate_queryset(Brand.objects.all(), request)

            serializer = BrandSerializer(brands, many=True).data
        return Response(serializer)


class ProductCategoryView(APIView):
    permission_classes = []

    def get(self, request, cat_id=None):
        if cat_id:
            serializer = ProductCategorySerializer(get_object_or_404(ProductCategory, id=cat_id)).data
        else:
            serializer = ProductCategorySerializer(ProductCategory.objects.all(), many=True).data
        return Response(serializer)


class StoreView(APIView):
    permission_classes = []

    def get(self, request, store_id=None):
        if store_id:
            if request.user.is_anonymous:
                return Response({"status": False, "detail": "You must be logged in to perform this operation"},
                                status=status.HTTP_401_UNAUTHORIZED)
            store = Store.objects.get(id=store_id, seller__user=request.user)
            if not store:
                return Response({"status": False, "detail": "You are not permitted to view this item"},
                                status=status.HTTP_401_UNAUTHORIZED)
            serializer = StoreSerializer(store, context={"request": request}).data
        else:
            serializer = StoreSerializer(Store.objects.all(), many=True, context={"request": request}).data
        return Response(serializer)

    def put(self, request, store_id):
        if request.user.is_anonymous:
            return Response({"status": False, "detail": "You must be logged in to perform this operation"},
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            store = Store.objects.get(id=store_id, seller__user=request.user)
            success = create_or_update_store(store, request)
            if success is True:
                serializer = StoreSerializer(store).data
                return Response({"success": True, "detail": serializer})
        except Exception as ex:
            return Response({"success": False, "detail": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


class ProductView(APIView, CustomPagination):
    permission_classes = []

    # list and retrieve products
    def get(self, request, slug=None):
        products = serializer = None
        if slug is None:
            products = Product.objects.all()  # queryset
            paginated_query = self.paginate_queryset(products, request)  # paginating query set
            serialized_data = ProductSerializer(paginated_query, many=True).data  # serialize the paginated query set
            paginated_response = self.get_paginated_response(serialized_data)  # get paginated response
            return Response(paginated_response.data)
        elif slug is not None:
            product = get_object_or_404(Product, slug=slug)
            serializer = ProductSerializer(product, many=False)
        return Response(serializer.data)

    def post(self, request):
        try:
            store_id = request.data.get('store', '')
            store = get_object_or_404(Store, pk=store_id)
            name = request.data.get('name', '').lower()
            # slug = name.replace(' ', '-')
            category = request.data.get('category', '')
            category_obj = ProductCategory.objects.get(pk=category)
            sub_category = request.data.get('sub_category', '')
            sub_category_obj = ProductCategory.objects.get(pk=sub_category)
            tags = request.data.get('tags', '')

            # use any other but not status, to avoid collision btw/
            # rest_framework.status, imported already
            product_status = request.data.get('status', '')

            product_instance = Product.objects.create(
                store=store,
                name=name,
                # slug=slug,
                category=category_obj,
                sub_category=sub_category_obj,
                tags=tags,
                status=product_status,
            )

        except Exception as err:
            return Response({"success": False, "message": "An error occurred. Please try again", "exception": str(err)},
                            status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"success": True, "message": f"Successfully created {name}"},
                            status=status.HTTP_201_CREATED)

    def put(self, request, slug=None):
        if slug is None:
            return Response({"error": "Provide a product slug field in URL"})

        try:
            product = Product.objects.get(slug=slug)
            store_id = request.data.get('store', '')
            product.store = Store.objects.get(pk=store_id)

            product.name = request.data.get('name', '')
            product.slug = request.data.get('name', '').replace(' ', '-')

            category = request.data.get('category', '')
            category_obj = ProductCategory.objects.get(pk=category)

            sub_category = request.data.get('sub_category', '')
            sub_category_obj = ProductCategory.objects.get(pk=sub_category)

            product.category = category_obj
            product.sub_category = sub_category_obj
            product.tags = request.data.get('tags', '')
            product.status = request.data.get('status', '')
            product.save()
            return Response({"success": True, "message": f"Succussfully updated {product.name}"})

        except Exception as err:
            return Response({"success": False, "message": "An error occurred. Please try again",
                             "exception": str(err)}, status=status.HTTP_403_FORBIDDEN)


class ProductDetailView(APIView):
    permission_classes = []

    def get(self, request, slug=None):
        queryset = ProductDetail.objects.get(product__slug=slug)
        serializer = ProductDetailSerializer(queryset, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductImageView(APIView):
    permission_classes = []

    def get(self, request):
        queryset = ProductImage.objects.all()
        serializer = ProductImageSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductReviewView(APIView):
    permission_classes = []

    def get(self, request):
        queryset = ProductReview.objects.all()
        serializer = ProductReviewSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductWishlistView(APIView):
    permission_classes = []

    def get(self, request):
        queryset = ProductWishlist.objects.all()
        serializer = ProductWishlistSerializer(queryset, many=True)
        # print(serializer.is_valid, serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShipperView(APIView):
    permission_classes = []

    def get(self, request):
        queryset = Shipper.objects.all()
        serializer = ShipperSerializer(queryset, many=True)
        # print(serializer.is_valid, serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


