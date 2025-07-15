from django.urls import path

from .views import OrdersAPIView, OrderDetailAPIView

app_name = "api_order"

urlpatterns = [
    path('orders', OrdersAPIView.as_view(), name='orders-list'),
    path('order/<int:pk>', OrderDetailAPIView.as_view(), name='order-detail'),
]
