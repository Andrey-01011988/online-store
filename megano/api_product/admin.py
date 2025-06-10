from django.contrib import admin

from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = "id", "title", "price", "count", "date",
    list_display_links = "id", "title"
    ordering = "id",
    search_fields = "title", "price", "count"
