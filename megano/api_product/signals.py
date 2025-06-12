from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review, Product
from django.db.models import Avg, Count


@receiver([post_save, post_delete], sender=Review)
def update_product_reviews(sender, instance, **kwargs):
    """
    Обновляет reviews_count и rating продукта при сохранении/удалении отзыва
    """
    product_id = instance.product_id
    reviews_data = Review.objects.filter(product_id=product_id).aggregate(
        avg_rating=Avg("rate"), reviews_count=Count("id")
    )
    Product.objects.filter(id=product_id).update(
        rating=reviews_data["avg_rating"] or 0,
        reviews_count=reviews_data["reviews_count"],
    )
