from rest_framework import serializers

from .models import Order
from api_product.serializers import ProductContractSerializer


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор заказа
    """

    # products = ProductContractSerializer(many=True, required=True)
    products = serializers.SerializerMethodField()
    fullName = serializers.StringRelatedField()
    email = serializers.StringRelatedField()
    phone = serializers.StringRelatedField()
    createdAt = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Order
        fields = "__all__"

    def get_products(self, obj):
        items = (
            obj.items.select_related('product')
            .prefetch_related('product__images', 'product__tags')
            .all()
        )

        # Явно передаем контекст с request
        product_serializer = ProductContractSerializer(
            [item.product for item in items],
            many=True,
            context={'request': self.context.get('request')},  # Критически важно!
        )

        products_data = product_serializer.data
        for product_data, item in zip(products_data, items):
            product_data['count'] = item.count
            product_data['price'] = item.price

        return products_data
