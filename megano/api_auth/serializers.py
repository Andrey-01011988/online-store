import json

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Avatar, Profile


class JsonStringSerializer(serializers.Serializer):
    """
    Принимает тело запроса в виде form-data с одним ключом,
    где ключ — это JSON-строка с нужными полями.
    """

    def to_internal_value(self, data):
        if isinstance(data, dict) and len(data) == 1:
            json_str = next(iter(data.keys()))
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise serializers.ValidationError({"json": [f"Invalid JSON: {str(e)}"]})
            return parsed
        raise serializers.ValidationError({"json": ["Invalid JSON format"]})

    def to_representation(self, instance):
        return instance


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)


class AvatarSerializer(serializers.ModelSerializer):
    src = serializers.SerializerMethodField()

    class Meta:
        model = Avatar
        fields = ["src", "alt"]

    def get_src(self, obj):
        return obj.src.url


class ProfileSerializer(serializers.Serializer):
    avatar = AvatarSerializer(allow_null=True)
    email = serializers.EmailField(source='user.email', required=False)
    fullName = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)

    def validate_phone(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Неверный формат номера телефона")


class PasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(max_length=255)
    newPassword = serializers.CharField(max_length=255)

    def validate_currentPassword(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value

    def validate_newPassword(self, value):
        validate_password(value)
        return value
