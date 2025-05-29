import json

from rest_framework import serializers


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
                raise serializers.ValidationError(f"Invalid JSON: {str(e)}")
            return parsed
        raise serializers.ValidationError("Expected single key with JSON string")

    def to_representation(self, instance):
        return instance

class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)

class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)