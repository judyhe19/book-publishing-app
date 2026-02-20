# serializers/validators.py
"""
Shared validation helpers for Book and AuthorBook serializers.
These raise serializers.ValidationError and are serializer-specific.
"""
import re
from decimal import Decimal
from rest_framework import serializers


def normalize_isbn(value):
    """
    Allow users to type ISBNs with hyphens/spaces.
    We store the normalized version (digits, and possibly trailing X for ISBN-10).
    """
    if value in (None, ""):
        return value
    return re.sub(r"[\s\-]", "", str(value)).strip()


def normalize_author_name(value: str) -> str:
    """Normalize spacing (matches AuthorCreateSerializer behavior)."""
    return " ".join(str(value).split()).strip()


def is_isbn10_format(v: str) -> bool:
    """9 digits + final digit or X/x."""
    return bool(re.fullmatch(r"\d{9}[\dXx]$", v))


def validate_royalty_rate(value):
    """Shared royalty-rate validation used by both AuthorBook serializers."""
    if value is None:
        raise serializers.ValidationError("Royalty rate is required.")
    if value < Decimal("0"):
        raise serializers.ValidationError("Royalty rate cannot be negative.")
    if value > Decimal("1"):
        raise serializers.ValidationError("Royalty rate must be less than or equal to 1 (decimal percentage).")
    return value


def rewrite_royalty_errors(errors, author_label):
    """
    Convert DRF's default royalty_rate error codes into author-prefixed messages.
    Used by both AuthorBookSerializer and AuthorBookByNameInputSerializer.
    """
    if not isinstance(errors, list):
        errors = [errors]

    new_errors = []
    for e in errors:
        code = getattr(e, "code", None)

        if code == "invalid":
            new_errors.append(
                f"Royalty rate for author {author_label} must be a positive valid decimal number."
            )
        elif code in ("max_digits", "max_whole_digits"):
            new_errors.append(
                f"Royalty rate for author {author_label} must calculate to a valid percentage (e.g. 0.15)."
            )
        else:
            msg = str(e)
            if "negative" in msg.lower():
                new_errors.append(
                    f"Royalty rate for author {author_label} cannot be negative."
                )
            elif "less than or equal to 1" in msg.lower() or "exceed" in msg.lower():
                new_errors.append(
                    f"Royalty rate for author {author_label} must be less than or equal to 1 (decimal percentage)."
                )
            else:
                new_errors.append(msg)

    return new_errors


def validate_isbn_13(value, required=True):
    """Shared ISBN-13 validation. Set required=False for PATCH (update) usage."""
    v = normalize_isbn(value)
    if not v:
        if required:
            raise serializers.ValidationError("ISBN-13 is required.")
        return v
    if not v.isdigit():
        raise serializers.ValidationError("ISBN-13 must contain only digits.")
    if len(v) != 13:
        raise serializers.ValidationError("ISBN-13 must be exactly 13 digits.")
    return v


def validate_isbn_10(value):
    """Shared ISBN-10 validation. Allows trailing X and stores as uppercase."""
    if value in (None, ""):
        return value
    v = normalize_isbn(value)
    if len(v) != 10:
        raise serializers.ValidationError("ISBN-10 must be exactly 10 characters.")
    if not is_isbn10_format(v):
        raise serializers.ValidationError("ISBN-10 must be 9 digits followed by a digit or X.")
    return v.upper()
