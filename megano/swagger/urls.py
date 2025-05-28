from django.urls import path
from . import views

app_name = 'swagger'

urlpatterns = [
    path('upload/', views.upload_swagger, name='swagger-upload'),
    path('yaml/<str:filename>/', views.swagger_yaml_view, name='swagger-yaml'),
    path('ui/<str:filename>/', views.swagger_ui_view, name='swagger-ui'),
]
