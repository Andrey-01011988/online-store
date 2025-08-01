from django.contrib import admin
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


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "EXPRESS_DELIVERY_COST",
        "FREE_DELIVERY_THRESHOLD",
        "REGULAR_DELIVERY_COST",
    )
