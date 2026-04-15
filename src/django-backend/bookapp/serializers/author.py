from rest_framework import serializers
from django.db import IntegrityError

from ..models import Author


def _normalize_author_name(value: str) -> str:
    return " ".join(str(value).split()).strip()


def _normalize_author_email(value: str) -> str:
    return str(value).strip().lower()

def _normalize_account_name(value: str) -> str:
    return str(value).strip()


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


class AuthorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "email", "paypal", "venmo"]

    def validate_name(self, value):
        return _validate_author_name(value)

    def validate_email(self, value):
        return _validate_author_email(value)
    
    def validate_paypal(self, value):
        return _normalize_account_name(value) if value is not None else value

    def validate_venmo(self, value):
        return _normalize_account_name(value) if value is not None else value

    def validate(self, attrs):
        """
        Optional: return nicer errors than a raw IntegrityError if duplicates exist.
        Keeps behavior consistent with your other serializers.
        """
        name = attrs.get("name")

        errors = {}
        if name and Author.objects.filter(name__iexact=name).exists():
            errors["name"] = "An author with this name already exists."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class AuthorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["name", "email", "paypal", "venmo"]

    def validate_name(self, value):
        return _validate_author_name(value)

    def validate_email(self, value):
        return _validate_author_email(value)
    
    def validate_paypal(self, value):
        return _normalize_account_name(value) if value is not None else value

    def validate_venmo(self, value):
        return _normalize_account_name(value) if value is not None else value

    def validate(self, attrs):
        """
        On update, enforce uniqueness excluding the current instance.
        """
        instance = getattr(self, "instance", None)

        name = attrs.get("name")

        errors = {}

        if instance and name is not None:
            if Author.objects.filter(name__iexact=name).exclude(pk=instance.pk).exists():
                errors["name"] = "An author with this name already exists."


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
            "paypal",
            "venmo",
            "authored_books_count",
            "total_author_royalty",
            "paid_author_royalty",
            "unpaid_author_royalty",
        ]