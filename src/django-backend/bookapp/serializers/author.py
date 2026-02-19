from rest_framework import serializers
from ..models import Author


class AuthorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class AuthorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "email"]

    def validate_name(self, value):
        # normalize spacing
        cleaned = " ".join(value.split()).strip()
        if not cleaned:
            raise serializers.ValidationError("Name cannot be blank.")
        return cleaned
    
    def validate_email(self, value):
        cleaned = (value or "").strip().lower()
        if not cleaned:
            raise serializers.ValidationError("Email cannot be blank.")
        return cleaned
