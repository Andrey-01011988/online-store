from django.db import models
from django.conf import settings


class Basket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='basket_items'
    )
    product = models.ForeignKey(
        "api_product.Product",  # Строковая ссылка на модель в другом приложении
        on_delete=models.CASCADE,
        related_name='basket_entries',
    )
    count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.count})"
