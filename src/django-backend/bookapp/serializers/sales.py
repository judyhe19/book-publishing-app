from rest_framework import serializers
from ..models import Sale, AuthorBook

class SaleSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    author_details = serializers.SerializerMethodField()
    class Meta:
        model = Sale
        fields = ['id', 'book', 'book_title', 'date', 'quantity', 'publisher_revenue', 'author_details']

    def get_author_details(self, obj):
        """Get author details for the sale - royalty amounts and paid status."""
        details = []
        for ars in obj.author_sales.select_related('author').all():
            details.append({
                "id": ars.author.id,
                "name": ars.author.name,
                "royalty_amount": ars.royalty_amount,
                "paid": ars.author_paid
            })
        return details

# TODO: need to get all authors (id, name) of the book to display the authors to allow the user the option to put a royalty amount for each author (instead of using the default amount) 
class SaleCreateSerializer(serializers.ModelSerializer):
    author_royalties = serializers.DictField(
        child=serializers.DecimalField(max_digits=10, decimal_places=2),
        required=False,
        write_only=True
    )
    author_paid = serializers.DictField(
        child=serializers.BooleanField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Sale
        fields = ['book', 'quantity', 'publisher_revenue', 'author_royalties', 'author_paid', 'date']
        # author_royalties is a dictionary of author_id: royalty_amount
        # author_id is the id of the author in the Author table
        # royalty_amount is the amount of royalty for that author to be stored in the AuthorSale table
        # author_paid is a dictionary of author_id: paid 
        # paid is a boolean that indicates whether the author has been paid for this sale

    def validate(self, data):
        """
        Check that quantity is positive, revenue is non-negative, royalties are non-negative,
        and sale date is not before publication date.
        """
        # 1. Quantity Check
        print(f"Validating data: {data}")
        if 'quantity' in data and data['quantity'] <= 0:
            raise serializers.ValidationError("Quantity must be a positive integer.")

        # 2. Revenue Check
        if data.get('publisher_revenue') is not None and data['publisher_revenue'] < 0:
            raise serializers.ValidationError("Publisher revenue cannot be negative.")

        # 3. Royalties Check
        author_royalties = data.get('author_royalties', {})
        for aid, amount in author_royalties.items():
            if amount < 0:
                raise serializers.ValidationError(f"Royalty amount for author {aid} cannot be negative.")

        # 4. Date Check
        book = data.get('book')
        sale_date = data.get('date')
        
        if book and sale_date:
            # book.publication_date is a date object
            if sale_date < book.publication_date:
                raise serializers.ValidationError(f"Sale date ({sale_date}) cannot be before book publication date ({book.publication_date}).")

        return data

    def create(self, validated_data):
        """
        Create a Sale instance and associated AuthorSales based on the validated data.
        """
        author_royalties = validated_data.pop('author_royalties', {})
        author_paid = validated_data.pop('author_paid', {})
        sale = super().create(validated_data)
        sale.create_author_sales(author_royalties, author_paid)
        return sale

    def update(self, instance, validated_data):
        """
        Update a Sale instance and recreate associated AuthorSales.
        """
        author_royalties = validated_data.pop('author_royalties', {})
        author_paid = validated_data.pop('author_paid', {})
        sale = super().update(instance, validated_data)
        sale.create_author_sales(author_royalties, author_paid)
        return sale

