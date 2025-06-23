import logging

from django.db import IntegrityError
from django.db.models import Prefetch

from rest_framework import status, permissions
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import Product, Review, Tag, Category
from .serializers import (
    ProductDetailSerializer,
    ReviewSerializer,
    TagSerializer,
    CategorySerializer,
    ProductContractSerializer,
    ProductShortSerializer,
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


class CatalogView(APIView):
    def get(self, request):
        queryset = Product.objects.prefetch_related("tags", "images").all()

        # --- Разбор фильтров ---
        filter_params = request.query_params
        print("\n", "Params", filter_params, "\n")
        # deepObject фильтры
        name = filter_params.get("filter[name]")
        min_price = filter_params.get("filter[minPrice]")
        max_price = filter_params.get("filter[maxPrice]")
        free_delivery = filter_params.get("filter[freeDelivery]")
        available = filter_params.get("filter[available]")
        # Прочие параметры
        category_id = filter_params.get("category")
        tags = filter_params.getlist("tags")
        sort = filter_params.get("sort", "date")
        sort_type = filter_params.get('sortType', 'dec')
        current_page = int(filter_params.get('currentPage', 1))
        limit = int(filter_params.get('limit', 20))

        # --- Фильтрация ---
        if name:
            queryset = queryset.filter(title__icontains=name)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if free_delivery is not None:
            queryset = queryset.filter(freeDelivery=free_delivery.lower() in ['true', '1', 'yes'])
        if available is not None:
            queryset = queryset.filter(
                count__gt=0 if available.lower() in ['true', '1', 'yes'] else 0
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()

        # --- Сортировка ---
        sort_map = {
            'rating': 'rating',
            'price': 'price',
            'reviews': 'reviews_count',
            'date': 'date',
        }
        sort_field = sort_map.get(sort, 'date')
        if sort_type == 'dec':
            sort_field = '-' + sort_field
        queryset = queryset.order_by(sort_field)

        # --- Пагинация ---
        total = queryset.count()
        last_page = (total + limit - 1) // limit
        start = (current_page - 1) * limit
        end = start + limit
        queryset = queryset[start:end]

        serializer = ProductShortSerializer(queryset, many=True)

        print("\n", "Serializer data", serializer.data, "\n")

        return Response(
            {'items': serializer.data, 'currentPage': current_page, 'lastPage': last_page},
            status=status.HTTP_200_OK,
        )
