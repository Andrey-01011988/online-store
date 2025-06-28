import logging

from django.db import IntegrityError
from django.db.models import Prefetch, Count

from rest_framework import status, permissions
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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
        response_data = {
            'items': data,
            'currentPage': self.page.number,
            'lastPage': self.page.paginator.num_pages,
        }

        logger.info(
            "Пагинация: показано %d из %d товаров (страница %d/%d)",
            len(data),
            self.page.paginator.count,
            self.page.number,
            self.page.paginator.num_pages,
        )
        return Response(response_data)

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            logger.warning(
                "Запрошена несуществующая страница: %s",
                request.query_params.get(self.page_query_param),
            )
            raise
        except Exception as e:
            logger.error("Ошибка пагинации: %s", str(e))
            raise


class CatalogView(ListAPIView):
    serializer_class = ProductShortSerializer
    pagination_class = CustomPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        logger.debug('Получен запрос на каталог с параметрами: %s', self.request.query_params)
        queryset = Product.objects.prefetch_related('tags', 'images', 'reviews').select_related(
            'category'
        )

        # Фильтрация
        queryset = self.apply_filters(queryset)
        # Сортировка
        queryset = self.apply_sorting(queryset)

        logger.debug('Формируется queryset с %s товарами', queryset.count())
        return queryset

    def apply_filters(self, queryset):
        params = self.request.query_params

        min_price = params.get('filter[minPrice]', 0)
        max_price = params.get('filter[maxPrice]', 50000)
        logger.debug('Фильтрация по цене: min=%s, max=%s', min_price, max_price)
        queryset = queryset.filter(price__gte=min_price, price__lte=max_price)

        if 'filter[name]' in params:
            logger.debug(
                'Фильтрация по названию продукта, содержащему переданную строку (без учета регистра): %s',
                params['filter[name]'],
            )
            queryset = queryset.filter(title__icontains=params['filter[name]'])

        if 'filter[available]' in params:
            logger.debug('Фильтрация по доступности: %s', params['filter[available]'])
            queryset = queryset.filter(available=params['filter[available]'] == 'true')

        if 'filter[freeDelivery]' in params:
            logger.debug('Фильтрация по бесплатной доставке: %s', params['filter[freeDelivery]'])
            queryset = queryset.filter(freeDelivery=params['filter[freeDelivery]'] == 'true')

        if category_id := params.get('category'):
            logger.debug('Фильтрация по категории: %s', category_id)
            queryset = queryset.filter(category_id=category_id)

        if tags := params.getlist('tags[]'):
            logger.debug('Фильтрация по тегам: %s', tags)
            queryset = queryset.filter(tags__id__in=tags).distinct()

        logger.debug('Queryset после фильтрации содержит %s товаров', queryset.count())
        return queryset

    def apply_sorting(self, queryset):
        sort_field = self.request.query_params.get('sort', 'date')
        sort_type = self.request.query_params.get('sortType', 'dec')

        logger.debug('Сортировка по полю: %s, тип: %s', sort_field, sort_type)

        if sort_field == 'reviews':
            logger.debug(
                'Выполняется аннотирование queryset по количеству отзывов для сортировки: %s',
                sort_field,
            )
            queryset = queryset.annotate(total_reviews=Count('reviews'))
            sort_field = 'total_reviews'

        prefix = '' if sort_type == 'inc' else '-'

        valid_fields = {'price', 'rating', 'date', 'total_reviews'}
        if sort_field not in valid_fields:
            logger.debug('Некорректное поле сортировки: %s. Используется "date".', sort_field)
            sort_field = 'date'

        logger.debug('Queryset отсортирован по: %s%s', prefix, sort_field)
        return queryset.order_by(f'{prefix}{sort_field}')
