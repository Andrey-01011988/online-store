from rest_framework import serializers
from django.apps import apps
from api_product.serializers import ImageSerializer, TagSerializer


class BasketItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk")
    images = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    category = serializers.IntegerField(
        source="category_id", allow_null=True
    )  # allow_null=True - обработка пустых значений
    reviews = serializers.IntegerField(source="reviews_count")
    rating = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        allow_null=True,
    )
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    freeDelivery = serializers.BooleanField()
    count = serializers.IntegerField(default=1, read_only=True)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, source='current_price'
    )

    class Meta:
        model = apps.get_model('api_product', 'Product')
        fields = [
            'id',
            'category',
            'price',
            'count',
            'title',
            'description',
            'freeDelivery',
            'images',
            'tags',
            'reviews',
            'rating',
        ]

    def get_images(self, obj) -> list:
        images = obj.images.all()
        if not images.exists():
            return [{'src': None, 'alt': 'No image'}]
        return ImageSerializer(images, many=True, context=self.context).data

    def get_tags(self, obj) -> list:
        tags = obj.tags.all()
        if not tags.exists():
            return []
        return TagSerializer(tags, many=True, context=self.context).data


class SaleSerializer(serializers.ModelSerializer):
    dateFrom = serializers.DateTimeField(format="%m-%d")
    dateTo = serializers.DateTimeField(format="%m-%d")
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = apps.get_model('api_product', 'Product')
        fields = [
            'id',
            'price',
            'salePrice',
            'dateFrom',
            'dateTo',
            'title',
            'images',
        ]
