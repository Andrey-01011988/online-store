from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class Product(models.Model):
    """
    Модель товара
    """

    objects = models.Manager()  # Определяет стандартный менеджер модели

    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория",
    )
    price = models.DecimalField(
        default=0, decimal_places=2, max_digits=10, verbose_name="Цена"
    )
    count = models.PositiveIntegerField(default=0, verbose_name="Количество")
    date = models.DateTimeField(
        blank=True, null=True, auto_now_add=True, verbose_name="Дата создания"
    )
    title = models.CharField(max_length=128, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    fullDescription = models.TextField(
        blank=True, null=True, verbose_name="Полное описание"
    )
    freeDelivery = models.BooleanField(default=True, verbose_name="Бесплатная доставка")
    tags = models.ManyToManyField(
        "Tag",
        blank=True,
        related_name="products",
        verbose_name="Теги",
    )
    reviews_count = models.PositiveIntegerField(
        default=0, verbose_name="Количество отзывов"
    )
    rating = models.DecimalField(
        default=0, decimal_places=2, max_digits=10, verbose_name="Рейтинг"
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.title


class Category(models.Model):
    """
    Модель категории товара
    """

    objects = models.Manager()  # Определяет стандартный менеджер модели

    title = models.CharField(max_length=128, verbose_name="Название")
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name="Родительская категория",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.title


def product_image_directory_path(instance: "ProductImage", filename):
    return f"products/{instance.product.title}_{instance.product.id}/{filename}"


def category_image_directory_path(instance: "Category", filename):
    return f"categories/{instance.category.title}_{instance.category.id}/{filename}"


class CategoryImage(models.Model):
    """
    Модель изображения категории
    """

    objects = models.Manager()  # Определяет стандартный менеджер модели

    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Категория",
    )
    src = models.ImageField(
        upload_to=category_image_directory_path, verbose_name="Изображение"
    )
    alt = models.CharField(default="image", max_length=64, verbose_name="Описание")

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"


class ProductImage(models.Model):
    """
    Модель изображения товара
    """

    objects = models.Manager()  # Определяет стандартный менеджер модели

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Товар",
    )
    src = models.ImageField(
        upload_to=product_image_directory_path, verbose_name="Изображение"
    )
    alt = models.CharField(default="image", max_length=64, verbose_name="Описание")

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"

    def __str__(self):
        return self.src.url


class Tag(models.Model):
    """
    Модель тега
    """

    objects = models.Manager()  # Определяет стандартный менеджер модели

    name = models.CharField(max_length=128, verbose_name="Название")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Review(models.Model):
    """
    Модель отзыва
    """

    objects = models.Manager()  # Определяет стандартный менеджер модели

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Товар",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Пользователь",
    )
    author = models.CharField(max_length=128, verbose_name="Автор")
    email = models.EmailField(verbose_name="Email")
    text = models.TextField(verbose_name="Текст")
    rate = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
        verbose_name="Оценка",
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"], name="unique_product_user_review"
            )
        ]

    def __str__(self):
        return f"{self.author} {self.product}"


class Specification(models.Model):
    """
    Модель характеристик товара
    """

    objects = models.Manager()  # Определяет стандартный менеджер модели

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="specifications",
        verbose_name="Товар",
    )
    name = models.CharField(max_length=128, verbose_name="Название")
    value = models.CharField(max_length=128, verbose_name="Значение")

    class Meta:
        verbose_name = "Характеристика"
        verbose_name_plural = "Характеристики"

    def __str__(self):
        return f"{self.name}, {self.value}"
