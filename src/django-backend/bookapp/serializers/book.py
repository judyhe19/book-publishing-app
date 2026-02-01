from rest_framework import serializers

from ..models import Book, AuthorBook


class AuthorBookSerializer(serializers.ModelSerializer):
    """
    Represents the relationship between an Author and a Book, including royalty_rate.
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


class BookSerializer(serializers.ModelSerializer):
    """
    Book serializer that supports writing/reading authors through the AuthorBook
    through-table (so we can include royalty_rate per author).
    """
    authors = AuthorBookSerializer(source="authorbook_set", many=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "publication_date",
            "isbn_13",
            "isbn_10",
            "total_sales_to_date",
            "publisher_user",
            "authors",
        ]
        read_only_fields = [
            "id",
            "publisher_user",
            "total_sales_to_date",
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

    def update(self, instance, validated_data):
        authors_data = validated_data.pop("authorbook_set", None)

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If authors were included in the PATCH/PUT payload, replace the through rows
        if authors_data is not None:
            instance.authorbook_set.all().delete()

            for entry in authors_data:
                AuthorBook.objects.create(
                    book=instance,
                    author_id=entry["author_id"],
                    royalty_rate=entry["royalty_rate"],
                )

        return instance
