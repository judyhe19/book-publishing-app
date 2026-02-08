# serializers (ONLY change: do NOT recreate AuthorSale rows on update; apply overrides to existing rows only if provided)

from rest_framework import serializers
import datetime
from ..models import Sale, Book, Author, AuthorSale, AuthorBook

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
   
    # Override fields to allow custom validation messages
    quantity = serializers.IntegerField(required=False, allow_null=True)
    publisher_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), required=False, allow_null=True)
    
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
        Custom validation to ensure logical consistency.
        """
        error = {}
        # Get values from data or instance (for partial updates)
        qty = data.get('quantity')
        if qty is None and self.instance:
            qty = self.instance.quantity
            
        rev = data.get('publisher_revenue')
        if rev is None and self.instance:
            rev = self.instance.publisher_revenue
            
        # Handle date logic
        date = data.get('date')
        if date:
            if isinstance(date, str):
                try:
                    parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                    data['date'] = parsed_date # Use lowercase 'date' -> matches model field
                    date = parsed_date
                except ValueError:
                    error['date'] = "Please provide sale date in month, year format."
                    date = None # Invalid date
        elif self.instance:
            date = self.instance.date

        book = data.get('book') 
        if not book and self.instance:
            book = self.instance.book
            
        author_royalties = data.get('author_royalties', {})

        # Required Field Checks
        if qty is None:
            error['quantity'] = "Quantity is required."
        if not date and 'date' not in error:
            error['date'] = "Date is required."
        if not book:
            error['book'] = "Book is required."
        if rev is None:
            error['publisher_revenue'] = "Publisher revenue is required."

        # Logic Checks (only run if value exists)
        if qty is not None:
             # Check if it's a float that is an integer
             if isinstance(qty, float) and not qty.is_integer():
                 error['quantity'] = "Quantity must be a valid integer."
             elif isinstance(qty, (int, float)) and qty <= 0:
                 error['quantity'] = "Quantity must be a positive integer."

        if rev is not None and rev < 0:
            error['publisher_revenue'] = "Publisher revenue cannot be negative."

        # Date vs Book Check (needs both to be valid)
        if date and book and date < book.publication_date:
            error['date'] = f"Sale date ({date}) cannot be before book publication date ({book.publication_date})."

        # Author Royalties
        error_author_royalties = []
        for author_id, amount in author_royalties.items():
            if amount < 0:
                author_name = str(author_id)
                try:
                    author = Author.objects.get(id=author_id)
                    author_name = author.name
                except Author.DoesNotExist:
                     pass 
                error_author_royalties.append(f"Royalty amount for author {author_name} cannot be negative.")
        
        if error_author_royalties:
            error['author_royalties'] = "\n".join(error_author_royalties)
        
        if error:
            raise serializers.ValidationError(error)
        
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
        Update a Sale instance WITHOUT recreating associated AuthorSales.
        (Past sales must not change authors/default royalties retroactively.)
        """
        author_royalties = validated_data.pop('author_royalties', {})
        author_paid = validated_data.pop('author_paid', {})

        sale = super().update(instance, validated_data)

        # Apply explicit overrides ONLY to existing AuthorSale rows (no recreation).
        if author_royalties or author_paid:
            qs = sale.author_sales.all()
            for ars in qs:
                key = str(ars.author_id)
                if key in author_royalties:
                    ars.royalty_amount = author_royalties[key]
                if key in author_paid:
                    ars.author_paid = bool(author_paid[key])
                ars.save()

        return sale
