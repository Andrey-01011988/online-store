from django.contrib import admin
from django.db.models import Count, Prefetch
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Product,
    Category,
    CategoryImage,
    ProductImage,
    Tag,
    Review,
    Specification,
)


class CategoryImageInline(
    admin.TabularInline
):  # или admin.StackedInline для другого вида
    model = CategoryImage
    extra = 1  # Количество пустых форм для добавления
    fields = ("src", "alt", "image_preview")  # Поля, которые можно редактировать
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if hasattr(obj, "src") and obj.src:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.src.url,
            )
        return "Нет изображения"

    image_preview.short_description = "Превью"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "price",
        "count",
        "date",
        "category_link",
        "freeDelivery",
        "rating",
        "reviews_count",
        "tags_display",
    )
    list_display_links = ("id", "title")
    ordering = ("id",)
    search_fields = ("title", "price", "count")
    list_filter = ("category", "freeDelivery", "tags")
    filter_horizontal = ("tags",)
    list_per_page = 50
    autocomplete_fields = ("tags",)

    def get_queryset(self, request):
        queryset = Product.objects.select_related("category").prefetch_related(
            Prefetch("tags", queryset=Tag.objects.only("name")),
            Prefetch("images", queryset=ProductImage.objects.only("src", "product")),
            Prefetch("reviews", queryset=Review.objects.only("product", "rate")),
            Prefetch(
                "specifications", queryset=Specification.objects.only("product", "name")
            ),
        )
        return queryset

    def category_link(self, obj):
        if obj.category:
            url = reverse("admin:api_product_category_change", args=[obj.category.id])
            return format_html('<a href="{}">{}</a>', url, obj.category.title)
        return "-"

    category_link.short_description = "Категория"

    def tags_display(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    tags_display.short_description = "Теги"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "parent_link", "image_preview", "products_count")
    list_display_links = ("id", "title")
    ordering = ("id",)
    search_fields = ("title",)
    list_filter = ("parent",)
    list_select_related = ("parent",)
    inlines = [CategoryImageInline]

    def get_queryset(self, request):
        queryset = Category.objects.select_related("parent").annotate(
            products_count=Count("products", distinct=True)
        )
        return queryset

    def parent_link(self, obj):
        if obj.parent:
            url = reverse("admin:api_product_category_change", args=[obj.parent.id])
            return format_html('<a href="{}">{}</a>', url, obj.parent.title)
        return "-"

    parent_link.short_description = "Родительская категория"

    def image_preview(self, obj):
        if hasattr(obj, "image") and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.src.url,
            )
        return "Нет изображения"

    image_preview.short_description = "Превью"

    def products_count(self, obj):
        return obj.products_count

    products_count.short_description = "Товары"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "alt", "thumbnail_preview", "product_link")
    list_display_links = ("id", "alt")
    ordering = ("id",)
    search_fields = ("alt", "product__title")
    list_select_related = ("product",)  # Оптимизация для ForeignKey

    def get_queryset(self, request):
        # Оптимизация: загружаем связанный товар одним запросом
        return super().get_queryset(request).select_related("product")

    def product_link(self, obj):
        if obj.product:
            url = reverse("admin:api_product_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.title)
        return "-"

    product_link.short_description = "Товар"

    def thumbnail_preview(self, obj):
        if obj.src:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.src.url,
            )
        return "-"

    thumbnail_preview.short_description = "Превью"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "products_count")
    list_display_links = ("id", "name")
    ordering = ("id",)
    search_fields = ("name",)
    list_per_page = 100

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(products_count=Count("products"))

    def products_count(self, obj):
        return obj.products_count

    products_count.short_description = "Товары"
    products_count.admin_order_field = "products_count"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "product_link",
        "rate",
        "date",
        "user_verbose",
        "short_text",
    )
    list_display_links = ("id", "author")
    ordering = ("-date",)
    search_fields = ("author", "product__title", "text")
    list_filter = ("rate", "date")
    list_select_related = ("product", "user")
    list_per_page = 50
    raw_id_fields = ("product", "user")

    def get_queryset(self, request):
        queryset = (
            super()
            .get_queryset(request)
            .select_related("product", "user")
            .only(
                "id",
                "author",
                "rate",
                "date",
                "text",
                "product__id",
                "product__title",
                "user__id",
                "user__username",
                "user__first_name",
            )
        )
        return queryset

    def product_link(self, obj):
        if obj.product:
            url = reverse("admin:api_product_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.title)
        return "-"

    product_link.short_description = "Товар"

    def user_verbose(self, obj):
        return obj.user.first_name or obj.user.username

    user_verbose.short_description = "Пользователь"

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    short_text.short_description = "Текст"


@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "value", "product_link")
    list_display_links = ("id", "name")
    ordering = ("id",)
    search_fields = ("name", "value", "product__title")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product")

    def product_link(self, obj):
        if obj.product:
            url = reverse("admin:api_product_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.title)
        return "-"

    product_link.short_description = "Товар"
