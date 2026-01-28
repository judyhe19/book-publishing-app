from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate(self, data):
        if User.objects.filter(is_staff=False, is_superuser=False).exists():
            raise serializers.ValidationError(
                {"detail": "Registration is disabled. A user already exists."}
            )

        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match")

        validate_password(data["password"])
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)