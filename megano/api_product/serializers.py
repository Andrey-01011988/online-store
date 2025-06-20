from rest_framework import serializers
from .models import (
    CategoryImage,
    Product,
    ProductImage,
    Tag,
    Review,
    Specification,
    Category,
)


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "src",
            "alt",
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
        )


class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    email = serializers.EmailField()
    rate = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        exclude = "product", "user"


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        exclude = (
            "id",
            "product",
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, required=True)
    tags = TagSerializer(many=True, required=False)
    reviews = ReviewSerializer(many=True, required=False)
    specifications = SpecificationSerializer(many=True, required=False)
    category = serializers.IntegerField(source="category.id", read_only=True)

    class Meta:
        model = Product
        exclude = ("reviews_count",)


class CategoryImageSerializer(serializers.ModelSerializer):
    src = serializers.ImageField()
    alt = serializers.CharField()

    class Meta:
        model = CategoryImage
        fields = (
            "src",
            "alt",
        )


class SubcategorySerializer(serializers.ModelSerializer):
    image = CategoryImageSerializer()

    class Meta:
        model = Category
        fields = (
            "id",
            "title",
            "image",
        )


class CategorySerializer(serializers.ModelSerializer):
    image = CategoryImageSerializer(read_only=True)
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "title",
            "image",
            "subcategories",
        )


class ProductContractSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    category = serializers.IntegerField(source="category.id", read_only=True)
    reviews = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = Product
        exclude = ("reviews_count", "fullDescription")

    def get_reviews(self, obj):
        return obj.reviews_count  # поле есть в объекте, но не сериализуется напрямую

    def get_date(self, obj):
        if obj.date:
            return obj.date.strftime(
                "%a %b %d %Y %H:%M:%S GMT+0100 (Central European Standard Time)"
            )
        return ""
