import logging

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema

from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from api_transaction.models import Basket
from api_product.serializers import ProductContractSerializer
from api_product.models import Product, ProductImage, Tag
from api_product.pagination import CustomPagination
from .serializers import BasketItemSerializer, SaleSerializer

logger = logging.getLogger(__name__)


@extend_schema(tags=["basket"], responses=BasketItemSerializer(many=True))
class BasketAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: BasketItemSerializer(many=True)},
        description="Получение содержимого корзины пользователя",
    )
    def get(self, request):
        basket_items = (
            Basket.objects.filter(user=request.user)
            .prefetch_related('product__images', 'product__tags')
            .only(
                'count',
                'product__id',
                'product__price',
                'product__title',
                'product__description',
                'product__freeDelivery',
                'product__rating',
                'product__reviews_count',
                'product__category_id',
                'product__salePrice',
                'product__dateFrom',
                'product__dateTo',
            )
        )

        serialized_items = []
        for item in basket_items:
            serializer = BasketItemSerializer(item.product, context={'request': request})
            item_data = serializer.data
            item_data.update({'count': item.count})
            serialized_items.append(item_data)

        return Response(serialized_items)

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'count': {'type': 'integer', 'default': 1},
                },
            }
        },
        responses={200: BasketItemSerializer(many=True)},
        description="Добавление товара в корзину",
    )
    @transaction.atomic
    def post(self, request):
        try:
            product_id = request.data['id']
            if not product_id:
                raise ValidationError({'id': 'Обязательное поле'})

            count = int(request.data.get('count'))
            if count <= 0:
                raise ValidationError({'count': 'Количество должно быть от 1 и больше'})

            product = Product.objects.get(id=product_id)

            if not product.available or product.count <= 0:
                return Response(
                    {'error': 'Товар недоступен для заказа'}, status=status.HTTP_400_BAD_REQUEST
                )

            if product.count < count:
                return Response(
                    {'error': 'Недостаточно товаров на складе, доступно %s' % product.count},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            basket_item, created = Basket.objects.get_or_create(
                user=request.user, product=product, defaults={'count': count}
            )

            if not created:
                new_count = basket_item.count + count
                if new_count > product.count:
                    return Response(
                        {"error": "Недостаточно товара (доступно: %s)" % product.count},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                basket_item.count = new_count
                basket_item.save()

            return self.get(request)

        except (KeyError, ValueError) as e:
            logger.error(f"Basket POST error: {str(e)}")
            return Response(
                {'error': 'Неверные данные запроса'}, status=status.HTTP_400_BAD_REQUEST
            )

        except Product.DoesNotExist:
            logger.error("Product not found: %s", product_id)
            return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'count': {'type': 'integer', 'default': 1},
                },
            }
        },
        responses={200: BasketItemSerializer(many=True)},
        description="Удаление товара из корзины",
    )
    @transaction.atomic
    def delete(self, request):
        try:
            data = request.data if request.data else {}
            product_id = data.get('id')
            if not product_id:
                raise ValidationError({'id': 'Обязательное поле'})

            count = int(data.get('count'))
            if count <= 0:
                raise ValidationError({'count': 'Количество должно быть от 1 и больше'})

            basket_item = Basket.objects.get(user=request.user, product_id=product_id)

            if basket_item.count <= count:
                basket_item.delete()
            else:
                basket_item.count -= count
                basket_item.save()

            return self.get(request)

        except (KeyError, ValueError) as e:
            logger.error("Basket DELETE error: %s", str(e))
            return Response(
                {'error': 'Неверные данные запроса'}, status=status.HTTP_400_BAD_REQUEST
            )
        except Basket.DoesNotExist:
            logger.error("Basket item not found: %s", product_id)
            return Response(
                {'error': 'Товар не найден в корзине'}, status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(tags=["catalog"], responses=BasketItemSerializer(many=True))
class BannersAPIView(ListAPIView):
    queryset = (
        Product.objects.prefetch_related(
            Prefetch('tags', queryset=Tag.objects.only('id', 'name')),
            Prefetch('images', queryset=ProductImage.objects.only('src', 'alt', 'product_id')),
        )
        .only(
            "id",
            "category_id",
            "price",
            "count",
            "title",
            "description",
            "freeDelivery",
            "reviews_count",
            "rating",
            "available",
            "date",
            "salePrice",
            "dateFrom",
            "dateTo",
        )
        .order_by("-rating", "-reviews_count")[:3]
    )
    serializer_class = ProductContractSerializer

    def get_serializer_context(self):
        return {'request': self.request}


@extend_schema(tags=["catalog"], responses=SaleSerializer(many=True))
class SalesAPIView(ListAPIView):
    queryset = (
        Product.objects.prefetch_related("images")
        .filter(
            salePrice__gt=0,
            salePrice__isnull=False,
            dateFrom__lte=timezone.now(),
            dateTo__gte=timezone.now(),
        )
        .order_by("-salePrice")
    )
    serializer_class = SaleSerializer
    pagination_class = CustomPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def list(self, request, *args, **kwargs):
        logger.debug("SalesAPIView request: %s", request.query_params)
        response = super().list(request, *args, **kwargs)
        logger.info("SalesAPIView response: %s items", len(response.data.get('items', [])))
        return response
