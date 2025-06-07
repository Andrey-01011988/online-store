from django.core.management import BaseCommand
from django.core.files import File
from pathlib import Path

from api_product.models import Product, Category, Tag, ProductImage, Specification

class Command(BaseCommand):
    """
    Mass create or update products with images and related data.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--images_dir',
            type=str,
            required=True,
            help='Путь к папке с изображениями для продуктов'
        )

    def handle(self, *args, **options):
        images_dir = Path(options['images_dir'])
        if not images_dir.exists() or not images_dir.is_dir():
            self.stdout.write(self.style.ERROR(f"Папка {images_dir} не найдена!"))
            return

        self.stdout.write(f"Start creating or updating products. Images dir: {images_dir}")

        products_data = [
            {
                "title": "Laptop",
                "description": "High-performance laptop",
                "fullDescription": "A laptop with high specs for professionals.",
                "price": 2399.99,
                "count": 10,
                "category": "Electronics",
                "freeDelivery": True,
                "tags": ["computers", "portable"],
                "images": ["laptop1.jpg", "laptop2.jpg"],
                "specifications": [
                    {"name": "CPU", "value": "Intel i7"},
                    {"name": "RAM", "value": "16GB"},
                ],
            },
            {
                "title": "Smartphone",
                "description": "Latest model smartphone",
                "fullDescription": "Flagship smartphone with AMOLED display.",
                "price": 987.50,
                "count": 25,
                "category": "Electronics",
                "freeDelivery": False,
                "tags": ["mobile", "touchscreen"],
                "images": ["smartphone1.jpg"],
                "specifications": [
                    {"name": "Screen", "value": "6.5 inch"},
                    {"name": "Battery", "value": "4000mAh"},
                ],
            },
        ]

        for prod_data in products_data:
            # Категория (объект)
            category, _ = Category.objects.get_or_create(title=prod_data["category"])
            # Теги
            tag_objs = []
            for tag_title in prod_data["tags"]:
                tag, _ = Tag.objects.get_or_create(title=tag_title)
                tag_objs.append(tag)

            # Создание или обновление продукта
            product, created = Product.objects.get_or_create(
                title=prod_data["title"],
                defaults={
                    "description": prod_data["description"],
                    "fullDescription": prod_data.get("fullDescription"),
                    "price": prod_data["price"],
                    "count": prod_data["count"],
                    "category": category,
                    "freeDelivery": prod_data["freeDelivery"],
                }
            )
            if created:
                self.stdout.write(f"Created product: {product.title}")
            else:
                updated = False
                for field in ["description", "fullDescription", "price", "count", "category", "freeDelivery"]:
                    if field == "category":
                        new_value = category
                    else:
                        new_value = prod_data.get(field, getattr(product, field))
                    if getattr(product, field) != new_value:
                        setattr(product, field, new_value)
                        updated = True
                if updated:
                    product.save()
                    self.stdout.write(f"Updated product: {product.title}")
                else:
                    self.stdout.write(f"Product {product.title} already exists, updating tags/images/specs.")

            # Привязка тегов
            product.tags.set(tag_objs)

            # Добавление характеристик (не дублируем)
            for spec in prod_data.get("specifications", []):
                Specification.objects.get_or_create(
                    product=product,
                    name=spec["name"],
                    value=spec["value"]
                )

            # Получаем все файлы в папке, имя которых содержит название продукта (без учёта регистра)
            product_title_lower = product.title.lower()
            image_files = [f for f in images_dir.iterdir() if product_title_lower in f.name.lower()]

            existing_images = set(product.images.values_list("src", flat=True))
            for img_path in image_files:
                img_name = img_path.name
                if img_path.exists():
                    if not any(img_name in str(existing) for existing in existing_images):
                        with open(img_path, "rb") as img_file:
                            ProductImage.objects.create(
                                product=product,
                                src=File(img_file, name=img_name),
                                alt=f"{product.title} image"
                            )
                            self.stdout.write(f"Added image {img_name} to {product.title}")
                    else:
                        self.stdout.write(f"Image {img_name} already exists for {product.title}")
                else:
                    self.stdout.write(self.style.WARNING(f"Image {img_name} not found for {product.title}"))

        self.stdout.write(self.style.SUCCESS("Products created or updated successfully."))

# python manage.py create_products --images_dir /home/uservm/python_django_diploma/explanations/images
