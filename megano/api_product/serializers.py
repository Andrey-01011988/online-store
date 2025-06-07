from rest_framework import serializers
from .models import Product, ProductImage, Tag, Review, Specification


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = "src", "alt",


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "id", "title",


class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    email = serializers.EmailField()
    rate = serializers.IntegerField(min_value = 1, max_value = 5)

    class Meta:
        model = Review
        exclude = "product", "user"


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        exclude = "id", "product",


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, required=True)
    tags = TagSerializer(many=True, required=False)
    reviews = ReviewSerializer(many=True, required=False)
    specifications = SpecificationSerializer(many=True, required=False)
    category = serializers.IntegerField(source="category.id", read_only=True)

    class Meta:
        model = Product
        exclude = "reviews_count",