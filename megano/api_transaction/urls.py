from django.urls import path

from .views import BasketAPIView, BannersAPIView, SalesAPIView

app_name = "api_transaction"

urlpatterns = [
    path("basket", BasketAPIView.as_view(), name="basket"),
    path("banners/", BannersAPIView.as_view(), name="banners"),
    path("sales/", SalesAPIView.as_view(), name="sales"),
]
