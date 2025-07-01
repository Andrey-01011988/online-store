from django.urls import path

from .views import BasketAPIView

app_name = "api_transaction"

urlpatterns = [
    path("basket", BasketAPIView.as_view(), name="basket"),
]
