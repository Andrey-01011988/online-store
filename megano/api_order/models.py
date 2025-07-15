from django.db import models
from django.core.exceptions import ValidationError


class Order(models.Model):
    """
    Модель заказа
    """

    user = models.ForeignKey(
        "api_auth.Profile",
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="Пользователь",
    )
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    deliveryType = models.CharField(max_length=255, verbose_name="Тип доставки", default="")
    paymentType = models.CharField(max_length=255, verbose_name="Тип оплаты", default="")
    totalCost = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Сумма заказа", default=0
    )
    status = models.CharField(max_length=255, verbose_name="Статус заказа", default="")
    city = models.CharField(max_length=255, verbose_name="Город", default="")
    address = models.CharField(max_length=255, verbose_name="Адрес", default="")
    products = models.ManyToManyField(
        "api_product.Product", through="OrderItem", verbose_name="Товары", related_name="orders"
    )

    class Meta:
        ordering = ["-createdAt"]
        indexes = [
            models.Index(fields=["-createdAt"]),
        ]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    @property
    def email(self):
        return self.user.user.email

    @property
    def fullName(self):
        return self.user.fullName

    @property
    def phone(self):
        return self.user.phone

    @property
    def orderId(self):
        return str(self.pk)

    def get_total_cost(self):
        try:
            if not self.pk:  # Если заказ ещё не сохранён
                return 0
            return sum(item.get_cost() for item in self.items.all())
        except Exception as e:
            raise ValidationError(f"Ошибка расчета стоимости товара: {str(e)}")

    def calculate_delivery_cost(self):
        try:
            if not self.pk:  # Если заказ ещё не сохранён
                return 0
            delivery_settings = DeliverySettings.objects.first()
            if not delivery_settings:
                raise ValidationError("Настройки доставки не найдены")

            if self.deliveryType == "express":
                return delivery_settings.EXPRESS_DELIVERY_COST
            elif self.get_total_cost() < delivery_settings.FREE_DELIVERY_THRESHOLD:
                return delivery_settings.REGULAR_DELIVERY_COST
            return 0
        except Exception as e:
            raise ValidationError(f"Ошибка расчета стоимости доставки: {str(e)}")

    def save(self, *args, **kwargs):
        try:
            # if not self.pk:
            #     super().save(*args, **kwargs)
            # self.totalCost = self.get_total_cost() + self.calculate_delivery_cost()
            # if self.pk:  # Убедимся, что запись существует
            #     kwargs.pop('force_insert', None)  # Удаляем force_insert, если он есть
            #     super().save(update_fields=['totalCost'], *args, **kwargs)

            # Всегда рассчитываем стоимость
            self.totalCost = self.get_total_cost() + self.calculate_delivery_cost()
            # Сохраняем все поля
            super().save(*args, **kwargs)
        except Exception as e:
            raise ValidationError(f"Ошибка сохранения заказа: {str(e)}")

    def __str__(self):
        return f"Заказ No{self.id}"


class OrderItem(models.Model):
    """
    Модель товара в заказе
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ"
    )
    product = models.ForeignKey(
        "api_product.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Товар",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    count = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        unique_together = ('order', 'product')
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

    def get_cost(self):
        try:
            return self.price * self.count
        except Exception as e:
            raise ValidationError("Ошибка расчета стоимости товара: %s", e)

    def __str__(self):
        return f"Товар No{self.id}"


class DeliverySettings(models.Model):
    EXPRESS_DELIVERY_COST = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Стоимость экспресс-доставки", default=500
    )
    FREE_DELIVERY_THRESHOLD = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Порог бесплатной доставки", default=2000
    )
    REGULAR_DELIVERY_COST = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Стоимость обычной доставки", default=200
    )

    def __str__(self):
        return "Настройки доставки"
