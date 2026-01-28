from rest_framework import serializers
from ..models import Sale

class SaleSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    author_royalties = serializers.SerializerMethodField()
    author_paid = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = ['id', 'book', 'book_title', 'date', 'quantity', 'publisher_revenue', 'author_royalties', 'author_paid']

    def get_author_royalties(self, obj):
        # Return dict of author_id: royalty_amount
        return {str(ars.author.id): ars.royalty_amount for ars in obj.author_sales.all()}

    def get_author_paid(self, obj):
        # Return dict of author_id: paid_status
        return {str(ars.author.id): ars.author_paid for ars in obj.author_sales.all()}

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
        fields = ['book', 'quantity', 'publisher_revenue', 'author_royalties', 'author_paid']
        # author_royalties is a dictionary of author_id: royalty_amount
        # author_id is the id of the author in the Author table
        # royalty_amount is the amount of royalty for that author to be stored in the AuthorSale table
        # author_paid is a dictionary of author_id: paid 
        # paid is a boolean that indicates whether the author has been paid for this sale

    def create(self, validated_data):
        author_royalties = validated_data.pop('author_royalties', {})
        author_paid = validated_data.pop('author_paid', {})
        return super().create(validated_data)
