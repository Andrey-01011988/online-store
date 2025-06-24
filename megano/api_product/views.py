import logging
import re

from django.db import IntegrityError
from django.db.models import Prefetch, QuerySet, Count

from rest_framework import status, permissions
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from drf_spectacular.utils import extend_schema

from .models import Product, Review, Tag, Category
from .serializers import (
    ProductDetailSerializer,
    ProductShortSerializer,
    ReviewSerializer,
    TagSerializer,
    CategorySerializer,
    ProductContractSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(tags=["product"], responses=ProductDetailSerializer)
class ProductDetailAPIView(RetrieveAPIView):
    queryset = Product.objects.prefetch_related("tags", "specifications", "reviews", "images").all()
    serializer_class = ProductDetailSerializer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        logger.debug("ProductDetailAPIView GET: id=%s, user=%s", kwargs.get("id"), request.user)
        response = super().get(request, *args, **kwargs)
        logger.info("ProductDetailAPIView response: %s", response.data)
        return response


@extend_schema(tags=["product"], responses=ReviewSerializer)
class ReviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, id: int):
        logger.debug(
            "ReviewAPIView POST: product_id=%s, data=%s, user=%s",
            id,
            request.data,
            request.user,
        )
        try:
            review = Review.objects.create(**request.data, product_id=id, user=request.user)
            serializer = ReviewSerializer(review)
            logger.info("Review created: %s", serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            logger.warning("Duplicate review by user %s for product %s", request.user, id)
            return Response(
                {"error": "Вы уже оставили отзыв на этот товар"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error("Error creating review: %s", str(e))
            return Response(
                {"error": "Ошибка при создании отзыва"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(tags=["tags"], responses=TagSerializer)
class TagsAPIListView(ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get(self, request, *args, **kwargs):
        logger.debug("TagsAPIListView GET: user=%s", request.user)
        response = super().get(request, *args, **kwargs)
        logger.info("TagsAPIListView response: %s", response.data)
        return response


@extend_schema(tags=["catalog"], responses=CategorySerializer)
class CategoriesAPIListView(ListAPIView):
    queryset = (
        Category.objects.filter(parent=None)
        .select_related("image")
        .prefetch_related(
            Prefetch("subcategories", queryset=Category.objects.select_related("image"))
        )
    )
    serializer_class = CategorySerializer

    def get(self, request, *args, **kwargs):
        logger.debug("CategoriesAPIListView GET: user=%s", request.user)
        response = super().get(request, *args, **kwargs)
        logger.info("CategoriesAPIListView response: %s", response.data)
        return response


@extend_schema(tags=["catalog"], responses=ProductContractSerializer)
class ProductPopularAPIView(ListAPIView):
    queryset = Product.objects.prefetch_related("tags", "images").all()
    serializer_class = ProductContractSerializer

    def get(self, request, *args, **kwargs):
        logger.debug("ProductPopularAPIView GET: user=%s", request.user)
        response = super().get(request, *args, **kwargs)
        titles = [item.get("title") for item in response.data]
        logger.info(
            "ProductPopularAPIView response: %s товаров. Названия: %s",
            len(response.data),
            ", ".join(titles),
        )
        return response


class ProductLimitedAPIView(ListAPIView):
    queryset = Product.objects.prefetch_related("tags", "images").all()
    serializer_class = ProductContractSerializer

    def get(self, request, *args, **kwargs):
        logger.debug("ProductLimitedAPIView GET: user=%s", request.user)
        response = super().get(request, *args, **kwargs)
        titles = [item.get("title") for item in response.data]
        logger.info(
            "ProductLimitedAPIView response: %s товаров. Названия: %s",
            len(response.data),
            ", ".join(titles),
        )
        return response


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100
    page_query_param = "currentPage"

    def get_paginated_response(self, data):
        return Response(
            {
                'items': data,
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
            }
        )


class CatalogView(ListAPIView):
    serializer_class = ProductShortSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = queryset = Product.objects.prefetch_related(
            Prefetch("tags"), Prefetch("images")
        ).select_related("category")
        filter_params = {}

        # Обработка фильтров
        name = self.request.query_params.get("filter[name]")
        if name:
            filter_params["title__icontains"] = name

        min_price = self.request.query_params.get("filter[minPrice]")
        if min_price:
            filter_params["price__gte"] = min_price

        max_price = self.request.query_params.get("filter[maxPrice]")
        if max_price:
            filter_params["price__lte"] = max_price

        # Обработка freeDelivery
        free_delivery = self.request.query_params.get("filter[freeDelivery]", "").lower()
        if free_delivery in ("true", "1", "yes"):
            filter_params["freeDelivery"] = True
        elif free_delivery in ("false", "0", "no"):
            filter_params["freeDelivery"] = False

        # Обработка available
        available = self.request.query_params.get("filter[available]", "").lower()
        if available in ("true", "1", "yes"):
            filter_params["count__gt"] = 0

        # Обработка категории
        category = self.request.query_params.get("category")
        if category:
            filter_params["category"] = category

        # Обработка тегов
        tags = self.request.query_params.getlist("tags[]") or self.request.query_params.getlist(
            "tags"
        )
        if tags:
            filter_params["tags__id__in"] = tags

        # Применение фильтров
        if filter_params:
            queryset = queryset.filter(**filter_params).distinct()

        # Обработка сортировки
        sort = self.request.query_params.get("sort", "date")
        sort_type = self.request.query_params.get("sortType", "dec")

        # Определение направления сортировки
        sort_prefix = "" if sort_type == "inc" else "-"

        # Специальная обработка для reviews (количество отзывов)
        if sort == "reviews":
            sort_field = f"{sort_prefix}reviews_count"
        else:
            # Стандартные поля сортировки
            sort_field = f"{sort_prefix}{sort}"

        # Применение сортировки
        return queryset.order_by(sort_field)

    def list(self, request, *args, **kwargs):
        logger.debug(f"Catalog request: {request.query_params}")
        response = super().list(request, *args, **kwargs)
        logger.info(f"Catalog response: {len(response.data['items'])} items")
        return response
