from rest_framework import serializers

from ..models import Book, AuthorBook, Author


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
    royalty_rate = serializers.DecimalField(
        max_digits=5, 
        decimal_places=4
    )

    class Meta:
        model = AuthorBook
        fields = [
            "author_id",
            "name",
            "royalty_rate",
        ]

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            if isinstance(exc.detail, dict) and 'royalty_rate' in exc.detail:
                # Check for various validation codes
                # 'invalid' -> usually format (e.g. text instead of number)
                # 'max_whole_digits', 'max_digits' -> digit constraints
                errors = exc.detail['royalty_rate']
                # Standardize as list
                if not isinstance(errors, list):
                    errors = [errors]

                aid = data.get('author_id')
                try:
                    author_obj = Author.objects.filter(pk=aid).first()
                    author_name = author_obj.name if author_obj else str(aid)
                except:
                    author_name = str(aid) if aid else "unknown"

                new_errors = []
                for e in errors:
                    code = getattr(e, 'code', str(e))
                    if code == 'invalid':
                        new_errors.append(f"Royalty rate for author {author_name} must be a valid decimal number.")
                    elif code in ('max_digits', 'max_whole_digits'):
                        new_errors.append(f"Royalty rate for author {author_name} must calculate to a valid percentage (e.g. 0.15).")
                    else:
                        new_errors.append(e)
                
                exc.detail['royalty_rate'] = new_errors
            raise exc


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
    
    def validate(self, attrs):
        """
        Custom validation for book creation.
        """
        error = {}
        
        # Required Fields - title, date, isbn13 handled by model/serializer fields usually, 
        # but explicit checks for custom messages:
        if not attrs.get('title'):
             error['title'] = "Title is required."

        if not attrs.get('publication_date'):
             error['publication_date'] = "Publication date is required."

        if not attrs.get('isbn_13'):
             error['isbn_13'] = "ISBN-13 is required."
        
        # The nested serializer source is 'authorbook_set', so that's the key in attrs
        authors = attrs.get('authorbook_set', [])
        if not authors:
             error['authors'] = "At least one author is required."
        else:
            # Check for duplicate authors and valid royalty rates
            author_ids = set()
            for i, entry in enumerate(authors):
                # entry is a dict with 'author_id' and 'royalty_rate' because of AuthorBookSerializer
                aid = entry.get('author_id')
                rate = entry.get('royalty_rate')
                author_obj = Author.objects.filter(pk=aid).first()
                author_name = author_obj.name if author_obj else str(aid)

                if aid in author_ids:
                    error['authors'] = f"Author {author_name} is added more than once."
                author_ids.add(aid)

                if rate is not None:
                    # Rate is already a Decimal thanks to serializer field, but we check value
                    if rate < 0:
                         error[f'authors[{i}].royalty_rate'] = f"Royalty rate for author {author_name} cannot be negative."
                    if rate > 1:
                         error[f'authors[{i}].royalty_rate'] = f"Royalty rate for author {author_name} must be less than or equal to 1 (decimal percentage)."
        # ISBN length checks
        isbn13 = attrs.get('isbn_13')
        if isbn13 and len(isbn13) != 13:
            error['isbn_13'] = "ISBN-13 must be exactly 13 characters."
        
        isbn10 = attrs.get('isbn_10')
        if isbn10 and len(isbn10) != 10:
             error['isbn_10'] = "ISBN-10 must be exactly 10 characters."

        if error:
            raise serializers.ValidationError(error)

        return attrs


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
