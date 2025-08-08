from django.contrib import admin
from django.utils import timezone
from .models import Order, OrderItem, DeliverySettings


class OrderItemInline(admin.StackedInline):
    model = OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    list_display = (
        "id",
        "user",
        "createdAt",
        "deliveryType",
        "paymentType",
        "totalCost",
        "status",
        "city",
        "address",
        "is_deleted",
        "deleted_at",
    )
    list_display_links = (
        "id",
        "user",
        "createdAt",
    )
    search_fields = (
        "id",
        "user",
        "createdAt",
        "deliveryType",
        "paymentType",
        "totalCost",
        "status",
        "city",
        "address",
    )
    list_per_page = 50
    ordering = ["-createdAt"]
    list_filter = (
        "createdAt",
        "deliveryType",
        "paymentType",
        "totalCost",
        "status",
        "city",
        "address",
    )
    actions = ["soft_delete", "hard_delete", "restore"]

    def soft_delete(self, request, queryset):
        queryset.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self, request, queryset):
        queryset.delete()

    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)

    soft_delete.short_description = "Пометить как удаленные"
    hard_delete.short_description = "Удалить навсегда"
    restore.short_description = "Восстановить"

    def get_queryset(self, request):
        qs = Order.objects.all_with_deleted().select_related("user")
        return qs


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "EXPRESS_DELIVERY_COST",
        "FREE_DELIVERY_THRESHOLD",
        "REGULAR_DELIVERY_COST",
    )
