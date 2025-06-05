import logging
from urllib import request

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework.request import Request

from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse

from .models import Profile
from .serializers import (
    SignInSerializer,
    SignUpSerializer,
    JsonStringSerializer,
    ProfileSerializer,
    PasswordSerializer,
    AvatarUploadSerializer,
)


logger = logging.getLogger(__name__)


@extend_schema(tags=["auth"])
class SignUpView(APIView):
    serializer_class = SignUpSerializer

    @extend_schema(
        request=SignUpSerializer,
        responses={
            201: OpenApiResponse(description="Created", response=None),
            400: OpenApiResponse(
                description="Validation error or user exists", response=None
            ),
            500: OpenApiResponse(description="Internal server error", response=None),
        },
        description="Регистрация нового пользователя. JSON передаётся как строка в form-data.",
    )
    def post(self, request: Request):
        wrapper_serializer = JsonStringSerializer(data=request.POST)
        if wrapper_serializer.is_valid():
            user_data = wrapper_serializer.validated_data
            serializer = self.serializer_class(data=user_data)
            if serializer.is_valid():
                name = serializer.validated_data["name"]
                username = serializer.validated_data["username"]
                password = serializer.validated_data["password"]
                if User.objects.filter(username=username).exists():
                    return Response(
                        {"detail": "Пользователь с таким username уже существует"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                try:
                    user = User.objects.create_user(
                        username=username, password=password, first_name=name
                    )
                    Profile.objects.create(user=user, fullName=name)
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                    logger.info(
                        f"User created: {username}", extra={"tags": ["registration"]}
                    )
                    return Response(status=status.HTTP_201_CREATED)
                except Exception as e:
                    logger.error(
                        f"Registration error: {str(e)}",
                        exc_info=True,  # автоматически добавит traceback
                        extra={"tags": ["registration_error"]},
                    )
                    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error(
                    f"Validation error: {serializer.errors}",
                    extra={"tags": ["validation_error"]},
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(
                f"Invalid wrapper data: {wrapper_serializer.errors}",
                extra={"tags": ["invalid_input"]},
            )
            return Response(
                wrapper_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=["auth"])
class SignInView(APIView):
    serializer_class = SignInSerializer

    @extend_schema(
        request=SignInSerializer,
        responses={
            201: OpenApiResponse(description="Created", response=None),
            400: OpenApiResponse(description="Validation error", response=None),
            401: OpenApiResponse(description="Authentication failed", response=None),
        },
        description="Аутентификация пользователя, JSON в теле передаётся как строка в form-data",
    )
    def post(self, request: Request):
        wrapper_serializer = JsonStringSerializer(data=request.POST)
        if wrapper_serializer.is_valid():
            # wrapper_serializer.validated_data — это dict с полями SignInSerializer
            serializer = self.serializer_class(data=wrapper_serializer.validated_data)
            if serializer.is_valid():
                username = serializer.validated_data.get("username")
                password = serializer.validated_data.get("password")
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    logger.info(f"User logged in: {username}", extra={"tags": ["auth"]})
                    return Response(status=status.HTTP_201_CREATED)
                else:
                    logger.warning(
                        "Authentication failed",
                        extra={"tags": ["auth_failed"], "username": username},
                    )
                    return Response(
                        {"detail": "Authentication failed"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            else:
                logger.error(
                    f"Validation error: {serializer.errors}",
                    extra={"tags": ["validation_error"]},
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning(
                f"Invalid wrapper data: {wrapper_serializer.errors}",
                extra={"tags": ["invalid_input"]},
            )
            return Response(
                wrapper_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=["auth"])
@extend_schema_view(
    post=extend_schema(
        description="Выход пользователя из системы",
        responses={200: OpenApiResponse(description="OK", response=None)},
    )
)
class SignOutView(APIView):
    def post(self, request: Request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


@extend_schema(tags=["profile"])
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    @extend_schema(
        request=ProfileSerializer,
        responses={
            200: OpenApiResponse(description="OK", response=None),
            400: OpenApiResponse(description="Validation error", response=None),
        },
        description="Получение профиля пользователя",
    )
    def get(self, request):
        profile = (
            Profile.objects.select_related("user")
            .prefetch_related("avatars")
            .get(user=request.user)
        )
        serializer = self.serializer_class(profile, context={"request": request})
        logger.debug("GET profile data: %s", serializer.data)
        return Response(serializer.data)

    @extend_schema(
        request=ProfileSerializer,
        responses={
            200: OpenApiResponse(description="OK", response=None),
            400: OpenApiResponse(description="Validation error", response=None),
        },
        description="Обновление профиля пользователя",
    )
    def post(self, request):
        logger.debug("POST data: %s", request.data)
        profile = (
            Profile.objects.select_related("user")
            .prefetch_related("avatars")
            .get(user=request.user)
        )
        serializer = self.serializer_class(
            instance=profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            logger.debug("Serializer validated data: %s", serializer.validated_data)

            user = profile.user
            user_data = serializer.validated_data.get("user", {})
            email = user_data.get("email")
            logger.debug("Email from request: %s", email)
            logger.debug("Current user email: %s", user.email)
            if email is not None and email != user.email:
                user.email = email
                user.save()
                logger.info("User email updated to: %s", email)
            phone = serializer.validated_data.get("phone")
            fullname = serializer.validated_data.get("fullName")
            if (
                phone
                and fullname is not None
                and (phone != profile.phone or fullname != profile.fullName)
            ):
                profile.phone = phone
                profile.fullName = fullname
                profile.save()
                logger.info("Profile updated: fullName=%s, phone=%s", fullname, phone)
            return Response(serializer.data)
        else:
            logger.error(
                "Profile update error: %s",
                serializer.errors,
                extra={"user": request.user.pk, "data": request.data},
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["profile"])
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PasswordSerializer

    @extend_schema(
        request=PasswordSerializer,
        responses={
            200: OpenApiResponse(description="OK", response=None),
            400: OpenApiResponse(description="Validation error", response=None),
        },
        description="Изменение пароля пользователя",
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        logger.debug("POST data: %s", request.data)
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data.get("newPassword")
            if not user.check_password(new_password):
                user.set_password(new_password)
                user.save()
                logger.info("Password changed for user: %s", user.username)
                return Response(
                    {"detail": "Пароль успешно изменён"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"newPassword": ["Новый пароль не должен совпадать с текущим"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            logger.error(
                "Password change error: %s",
                serializer.errors,
                extra={"user": request.user.pk, "data": request.data},
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["profile"],
    description="update user avatar (request.FILES['avatar'] in Django)",
    responses={
        200: OpenApiResponse(description="successful operation"),
        400: OpenApiResponse(description="Validation error"),
    },
)
class ProfileAvatarUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        logger.debug(
            "Profile_avatar_data: %s, extra=%s",
            request.FILES["avatar"],
            {"user": request.user.pk, "data": request.data},
        )

        serializer = AvatarUploadSerializer(
            data={
                "src": request.FILES["avatar"],
                "alt": request.data.get("alt", "User avatar"),
            },
            context={"request": request},
        )
        if serializer.is_valid():

            logger.debug("Serializer validated data: %s", serializer.validated_data)
            avatar = serializer.save()
            logger.info("Avatar updated: %s", avatar)
            return Response(
                {"detail": "Аватар успешно обновлён"}, status=status.HTTP_200_OK
            )
        else:
            logger.error("Avatar upload validation errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
