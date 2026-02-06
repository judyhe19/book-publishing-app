from rest_framework import serializers
from ..models import Author


class AuthorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name"]


class AuthorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name"]

    def validate_name(self, value):
        # normalize spacing
        cleaned = " ".join(value.split()).strip()
        if not cleaned:
            raise serializers.ValidationError("Name cannot be blank.")
        return cleaned
