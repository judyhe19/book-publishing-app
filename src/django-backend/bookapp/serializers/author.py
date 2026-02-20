from rest_framework import serializers
from django.db import IntegrityError

from ..models import Author


def _normalize_author_name(value: str) -> str:
    return " ".join(str(value).split()).strip()


def _normalize_author_email(value: str) -> str:
    return str(value).strip().lower()


def _validate_author_name(value: str) -> str:
    cleaned = _normalize_author_name(value)
    if not cleaned:
        raise serializers.ValidationError("Name cannot be blank.")
    return cleaned


def _validate_author_email(value: str) -> str:
    cleaned = _normalize_author_email(value)
    if not cleaned:
        raise serializers.ValidationError("Email cannot be blank.")
    return cleaned


class AuthorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "email"]


class AuthorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "email"]

    def validate_name(self, value):
        return _validate_author_name(value)

    def validate_email(self, value):
        return _validate_author_email(value)

    def validate(self, attrs):
        """
        Optional: return nicer errors than a raw IntegrityError if duplicates exist.
        Keeps behavior consistent with your other serializers.
        """
        name = attrs.get("name")
        email = attrs.get("email")

        errors = {}
        if name and Author.objects.filter(name__iexact=name).exists():
            errors["name"] = "An author with this name already exists."
        if email and Author.objects.filter(email__iexact=email).exists():
            errors["email"] = "An author with this email already exists."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class AuthorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "email"]

    def validate_name(self, value):
        return _validate_author_name(value)

    def validate_email(self, value):
        return _validate_author_email(value)

    def validate(self, attrs):
        """
        On update, enforce uniqueness excluding the current instance.
        """
        instance = getattr(self, "instance", None)

        name = attrs.get("name")
        email = attrs.get("email")

        errors = {}

        if instance and name is not None:
            if Author.objects.filter(name__iexact=name).exclude(pk=instance.pk).exists():
                errors["name"] = "An author with this name already exists."

        if instance and email is not None:
            if Author.objects.filter(email__iexact=email).exclude(pk=instance.pk).exists():
                errors["email"] = "An author with this email already exists."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

class AuthorListSerializer(serializers.ModelSerializer):
    authored_books_count = serializers.IntegerField(read_only=True)
    total_author_royalty = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    paid_author_royalty = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    unpaid_author_royalty = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "email",
            "authored_books_count",
            "total_author_royalty",
            "paid_author_royalty",
            "unpaid_author_royalty",
        ]