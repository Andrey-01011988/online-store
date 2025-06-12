import logging

from django.db import IntegrityError

from rest_framework import status
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import Product, Review, Tag
from .serializers import ProductDetailSerializer, ReviewSerializer, TagSerializer


logger = logging.getLogger(__name__)


@extend_schema(tags=["product"], responses=ProductDetailSerializer)
class ProductDetailAPIView(RetrieveAPIView):
    queryset = Product.objects.prefetch_related(
        "tags", "specifications", "reviews", "images"
    ).all()
    serializer_class = ProductDetailSerializer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        logger.debug(
            "ProductDetailAPIView GET: id=%s, user=%s", kwargs.get("id"), request.user
        )
        response = super().get(request, *args, **kwargs)
        logger.info("ProductDetailAPIView response: %s", response.data)
        return response


@extend_schema(tags=["product"], responses=ReviewSerializer)
class ReviewAPIView(APIView):
    def post(self, request: Request, id: int):
        logger.debug(
            "ReviewAPIView POST: product_id=%s, data=%s, user=%s",
            id,
            request.data,
            request.user,
        )
        try:
            review = Review.objects.create(
                **request.data, product_id=id, user=request.user
            )
            serializer = ReviewSerializer(review)
            logger.info("Review created: %s", serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            logger.warning(
                "Duplicate review by user %s for product %s", request.user, id
            )
            return Response(
                {"error": "Вы уже оставили отзыв на этот товар"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error("Error creating review: %s", str(e))
            return Response(
                {"error": "Ошибка при создании отзыва"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class TagsAPIListView(ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get(self, request, *args, **kwargs):
        logger.debug("TagsAPIListView GET: user=%s", request.user)
        response = super().get(request, *args, **kwargs)
        logger.info("TagsAPIListView response: %s", response.data)
        return response
