from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.request import Request

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse

from .models import Profile
from .serializers import SignInSerializer, SignUpSerializer, JsonStringSerializer


class SignUpView(APIView):
    serializer_class = SignUpSerializer

    @extend_schema(
        request=SignUpSerializer,
        responses={
            201: OpenApiResponse(description='Created', response=None),
            400: OpenApiResponse(description='Validation error or user exists', response=None),
            500: OpenApiResponse(description='Internal server error', response=None),
        },
        description="Регистрация нового пользователя. JSON передаётся как строка в form-data."
    )
    def post(self, request: Request):
        wrapper_serializer = JsonStringSerializer(data=request.POST)
        if wrapper_serializer.is_valid():
            user_data = wrapper_serializer.validated_data
            serializer = self.serializer_class(data=user_data)
            if serializer.is_valid():
                name = serializer.validated_data['name']
                username = serializer.validated_data['username']
                password = serializer.validated_data['password']
                if User.objects.filter(username=username).exists():
                    return Response({'detail': 'Пользователь с таким username уже существует'},
                                    status=status.HTTP_400_BAD_REQUEST)
                try:
                    user = User.objects.create_user(username=username, password=password, first_name=name)
                    Profile.objects.create(user=user, fullName=name)
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                    return Response(status=status.HTTP_201_CREATED)
                except Exception as e:
                    print(e)
                    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(wrapper_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    serializer_class = SignInSerializer

    @extend_schema(
        request=SignInSerializer,
        responses={
            201: OpenApiResponse(description='Created', response=None),
            400: OpenApiResponse(description='Validation error', response=None),
            401: OpenApiResponse(description='Authentication failed', response=None),
        },
        description="Аутентификация пользователя, JSON в теле передаётся как строка в form-data"
    )
    def post(self, request: Request):
        wrapper_serializer = JsonStringSerializer(data=request.POST)
        if wrapper_serializer.is_valid():
            # wrapper_serializer.validated_data — это dict с полями SignInSerializer
            serializer = self.serializer_class(data=wrapper_serializer.validated_data)
            if serializer.is_valid():
                username = serializer.validated_data.get('username')
                password = serializer.validated_data.get('password')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return Response(status=status.HTTP_201_CREATED)
                else:
                    return Response({'detail': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(wrapper_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    post=extend_schema(
        description="Выход пользователя из системы",
        responses={200: OpenApiResponse(description='OK', response=None)}
    )
)
class SignOutView(APIView):
    def post(self, request: Request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
