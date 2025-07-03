from django.urls import path

from .views import BasketAPIView, BannersAPIView

app_name = "api_transaction"

urlpatterns = [
    path("basket", BasketAPIView.as_view(), name="basket"),
    path("banners/", BannersAPIView.as_view(), name="banners"),
]
