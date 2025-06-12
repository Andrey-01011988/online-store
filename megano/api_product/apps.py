from django.apps import AppConfig


class ApiProductConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_product'

    def ready(self):
        import api_product.signals