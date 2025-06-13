from django.urls import path

from .views import (
    ProductDetailAPIView,
    ReviewAPIView,
    TagsAPIListView,
    CategoriesAPIListView,
)


app_name = "api_product"

urlpatterns = [
    path("product/<int:id>", ProductDetailAPIView.as_view(), name="product_detail"),
    path("product/<int:id>/reviews", ReviewAPIView.as_view(), name="product_review"),
    path("tags", TagsAPIListView.as_view(), name="tags"),
    path("categories", CategoriesAPIListView.as_view(), name="categories"),
]
