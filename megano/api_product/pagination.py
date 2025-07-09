from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "limit"
    max_page_size = 100
    page_query_param = "currentPage"

    def get_count(self, queryset):
        return super().get_count(queryset)

    def get_paginated_response(self, data):
        response_data = {
            'items': data,
            'currentPage': self.page.number,
            'lastPage': self.page.paginator.num_pages,
        }

        logger.info(
            "Пагинация: показано %d из %d товаров (страница %d/%d)",
            len(data),
            self.page.paginator.count,
            self.page.number,
            self.page.paginator.num_pages,
        )
        return Response(response_data)

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except NotFound:
            logger.warning(
                "Запрошена несуществующая страница: %s",
                request.query_params.get(self.page_query_param),
            )
            raise
        except Exception as e:
            logger.error("Ошибка пагинации: %s", str(e))
            raise
