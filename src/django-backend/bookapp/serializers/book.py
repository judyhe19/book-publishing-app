from rest_framework import serializers

from ..models import Book, AuthorBook


# ------------------------------------
# AuthorBook (shared, simple serializer)
# ------------------------------------

class AuthorBookSerializer(serializers.ModelSerializer):
    """
    Represents the relationship between an Author and a Book,
    including royalty_rate.
    """
    author_id = serializers.IntegerField()
    name = serializers.CharField(source="author.name", read_only=True)

    class Meta:
        model = AuthorBook
        fields = [
            "author_id",
            "name",
            "royalty_rate",
        ]


# ------------------------------------
# READ serializers (GET)
# ------------------------------------

class BookListSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for book list views.
    Returns one book with nested authors + royalty_rate.
    """
    authors = AuthorBookSerializer(source="authorbook_set", many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "total_sales_to_date",
            "authors",
        ]


class BookDetailSerializer(BookListSerializer):
    """
    For now, detail view returns the same shape as list view.
    Split exists so you can extend detail later without
    breaking the list.
    """
    pass


# ------------------------------------
# WRITE serializers (POST / PATCH)
# ------------------------------------

class BookCreateSerializer(serializers.ModelSerializer):
    """
    Serializer used ONLY for creating books.
    Accepts nested authors with royalty_rate.
    """
    authors = AuthorBookSerializer(source="authorbook_set", many=True)

    class Meta:
        model = Book
        fields = [
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "authors",
        ]

    def create(self, validated_data):
        authors_data = validated_data.pop("authorbook_set", [])
        book = Book.objects.create(**validated_data)

        for entry in authors_data:
            AuthorBook.objects.create(
                book=book,
                author_id=entry["author_id"],
                royalty_rate=entry["royalty_rate"],
            )

        return book


class BookUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer used for PATCH/PUT.
    Authors are OPTIONAL:
      - omitted => authors unchanged
      - provided => author list replaced
    """
    authors = AuthorBookSerializer(
        source="authorbook_set",
        many=True,
        required=False,
    )

    class Meta:
        model = Book
        fields = [
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "authors",
        ]

    def update(self, instance, validated_data):
        authors_data = validated_data.pop("authorbook_set", None)

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Replace authors ONLY if provided
        if authors_data is not None:
            instance.authorbook_set.all().delete()

            for entry in authors_data:
                AuthorBook.objects.create(
                    book=instance,
                    author_id=entry["author_id"],
                    royalty_rate=entry["royalty_rate"],
                )

        return instance
