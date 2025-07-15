import logging

from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction

from .models import Order, OrderItem
from .serializers import OrderSerializer
from api_product.models import Product
from api_transaction.models import Basket


logger = logging.getLogger(__name__)


class OrdersAPIView(APIView):

    def get(self, request: Request, pk=None):
        data = Order.objects.filter(user_id=request.user.profile.pk)
        for i in data:
            print("\ndata", i.pk, i.city, i.products.all(), "\n")
            # logger.debug("GET order data: %s", i)
        serializer = OrderSerializer(data, many=True, context={'request': request})
        print("\nserializer.data", serializer.data, "\n")
        # logger.debug("\nGET orders data: \n%s", "\n".join(map(str, serializer.data)))
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request: Request, *args, **kwargs):
        print("\nrequest data", request.data, "\n")
        # logger.debug("\nPOST order data: %s", request.data, "\n")

        products_in_order = [(obj["id"], obj["count"], obj["price"]) for obj in request.data]
        if not products_in_order:
            return Response(
                {"error": "Заказ не может быть пустым"}, status=status.HTTP_400_BAD_REQUEST
            )
        products = Product.objects.filter(id__in=[obj[0] for obj in products_in_order])
        if products.count() != len(products_in_order):
            missing_ids = set([obj[0] for obj in products_in_order]) - set(
                products.values_list("id", flat=True)
            )
            return Response(
                {"error": f"Товары с ID {missing_ids} не найдены"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаем словарь для быстрого доступа к цене и количеству по ID товара
        product_info = {pid: (count, price) for pid, count, price in products_in_order}

        order = Order.objects.create(
            user=request.user.profile,
            totalCost=sum([obj[1] * obj[2] for obj in products_in_order]),
        )
        data = {
            "orderId": order.pk,
        }
        print("\n", products, "\n")
        # logger.debug("\nPOST order products: %s", products.all(), "\n")
        # Создаем OrderItem с указанием цены для каждого товара
        order_items = [
            OrderItem(
                order=order,
                product=product,
                count=product_info[product.id][0],
                price=product_info[product.id][1],
            )
            for product in products
        ]
        OrderItem.objects.bulk_create(order_items)
        order.products.set(products)  # Явно устанавливаем связь между заказом и товарами
        return Response(data, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(APIView):

    def get(self, request: Request, pk):
        if pk:
            # Детали одного заказа
            try:
                order = Order.objects.get(id=pk, user=request.user.profile)
                print("\norder", order.pk, order.city, order.products.all(), "\n")
                for i in order.products.all():
                    print("\norder", i.pk, i.title, i.count, i.price, i.images.all(), "\n")
                serializer = OrderSerializer(order, context={'request': request})
                return Response(serializer.data)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Список заказов
            orders = Order.objects.filter(user=request.user.profile)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)

    @transaction.atomic
    def post(self, request: Request, pk=None):
        try:
            data = request.data
            print("\ndata", data, "\n")
            # logger.debug("\nPOST order data: \n%s", "\n".join(map(str, data)), "\n")
            # Для гостевых заказов
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required', 'redirect': '/sign-in/?next=/orders/'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            # Создание заказа
            order_data = {
                'user': request.user.profile,
                # 'fullName': data.get('fullName'),
                # 'phone': data.get('phone'),
                # 'email': data.get('email'),
                'deliveryType': data.get('deliveryType', 'ordinary'),
                'city': data.get('city'),
                'address': data.get('address'),
                'paymentType': data.get('paymentType', 'online'),
                'status': 'Ожидает оплаты',
            }
            print("\norder_data", order_data, "\n")
            # Код не сохраняет заказ
            if pk:
                order = Order.objects.get(pk=pk, user=request.user.profile)
                for key, value in order_data.items():
                    setattr(order, key, value)
                order.save()
            else:
                order = Order.objects.create(**order_data)

            # Добавление товаров
            products = data.get('products', [])
            if not products:
                return Response(
                    {"error": "Заказ не может быть пустым"}, status=status.HTTP_400_BAD_REQUEST
                )
            for product in products:
                OrderItem.objects.update_or_create(
                    order=order, product_id=product['id'], defaults={'count': product['count']}
                )
            # Обновляем связь между заказом и товарами
            product_ids = [product['id'] for product in products]
            order.products.set(Product.objects.filter(id__in=product_ids))

            # Очистка корзины
            if request.user.is_authenticated:
                Basket.objects.filter(user=request.user).delete()
            elif 'basket' in request.session:
                del request.session['basket']

            return Response({'orderId': order.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Order error: {str(e)}")
            return Response(
                {'error': 'Order processing failed'}, status=status.HTTP_400_BAD_REQUEST
            )
