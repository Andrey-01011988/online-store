from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review, Product
from django.db.models import Avg, Count
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Review)
def update_product_reviews(sender, instance, **kwargs):
    """
    Обновляет reviews_count и rating продукта при сохранении/удалении отзыва
    """
    try:
        with transaction.atomic():
            product = Product.objects.filter(id=instance.product_id).select_for_update().first()

            if not product:
                return

            reviews_data = Review.objects.filter(product_id=product.id).aggregate(
                avg_rating=Avg("rate"), reviews_count=Count("id")
            )

            Product.objects.filter(id=product.id).update(
                rating=reviews_data["avg_rating"] or 0,
                reviews_count=reviews_data["reviews_count"],
            )
            logger.debug("Отзывы для продукта %s обновлены", product.id)
    except Exception as e:
        logger.error(f"Ошибка обновления отзывов для продукта {instance.product_id}: {str(e)}")
