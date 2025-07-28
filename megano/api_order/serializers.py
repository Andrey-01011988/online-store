from rest_framework import serializers

from .models import Order
from api_product.models import Product


class OrderProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, source='current_price')
    count = serializers.IntegerField(default=1)
    category = serializers.IntegerField(source="category_id", read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'category',
            'price',
            'count',
            'date',
            'title',
            'description',
            'freeDelivery',
            'images',
            'tags',
            'reviews',
            'rating',
        ]
        read_only_fields = ['reviews', 'rating']

    def get_images(self, obj):
        # Используем prefetched images без дополнительных запросов
        images = getattr(obj, 'prefetched_images', [])
        request = self.context.get('request')
        return [
            {
                'src': request.build_absolute_uri(image.src.url) if request else image.src.url,
                'alt': image.alt,
            }
            for image in images
            if image.src
        ]

    def get_tags(self, obj):
        # Используем prefetched tags без дополнительных запросов
        tags = getattr(obj, 'prefetched_tags', [])
        return [{'id': tag.id, 'name': tag.name} for tag in tags]

    def get_reviews(self, obj):
        return obj.reviews_count

    def _get_image_url(self, image):
        request = self.context.get('request')
        if image.src and hasattr(image.src, 'url'):
            return request.build_absolute_uri(image.src.url) if request else image.src.url
        return None


class OrderSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    fullName = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Order
        fields = "__all__"

    def get_fullName(self, obj):
        return obj.fullName  # Использует property из модели

    def get_email(self, obj):
        return obj.email  # Использует property из модели

    def get_phone(self, obj):
        return obj.phone  # Использует property из модели

    def get_products(self, obj):
        items = getattr(obj, '_prefetched_objects_cache', {}).get('items', obj.items.all())

        # Подготавливаем продукты с доп. полями
        products = []
        for item in items:
            product = item.product
            product.count = item.count  # Добавляем count из OrderItem
            product.price = item.price  # Используем цену из заказа

            # Добавляем prefetched данные если они есть
            if hasattr(item, 'prefetched_images'):
                product.prefetched_images = item.prefetched_images
            if hasattr(item, 'prefetched_tags'):
                product.prefetched_tags = item.prefetched_tags

            products.append(product)

        return OrderProductSerializer(products, many=True, context=self.context).data
