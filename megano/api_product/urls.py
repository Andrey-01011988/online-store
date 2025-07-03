from django.urls import path

from .views import (
    ProductDetailAPIView,
    ReviewAPIView,
    TagsAPIListView,
    CategoriesAPIListView,
    ProductPopularAPIView,
    ProductLimitedAPIView,
    CatalogView,
)


app_name = "api_product"

urlpatterns = [
    path("product/<int:id>/", ProductDetailAPIView.as_view(), name="product_detail"),
    path("product/<int:id>/reviews", ReviewAPIView.as_view(), name="product_review"),
    path("products/popular/", ProductPopularAPIView.as_view(), name="product_popular"),
    path("products/limited/", ProductLimitedAPIView.as_view(), name="product_limited"),
    path("tags/", TagsAPIListView.as_view(), name="tags"),
    path("categories/", CategoriesAPIListView.as_view(), name="categories"),
    path("catalog/", CatalogView.as_view(), name="catalog"),
]
