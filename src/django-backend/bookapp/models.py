from django.db import models
from django.contrib.auth.models import User

# 1. AUTHOR Table
class Author(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# 2. BOOK Table
class Book(models.Model):
    title = models.CharField(max_length=255)
    publication_date = models.DateField()
    isbn_13 = models.CharField(max_length=13, unique=True)
    isbn_10 = models.CharField(max_length=10, blank=True, null=True)
    
    # Financials
    author_royalty_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage, e.g. 0.15 for 15%")
    total_sales_to_date = models.IntegerField(default=0)
    
    # Relationships
    publisher_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='published_books')
    authors = models.ManyToManyField(Author, related_name='books')

    def __str__(self):
        return self.title

# 3. SALE Table
class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='sales')
    date = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField()
    
    # Financial snapshots
    publisher_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    author_paid = models.BooleanField(default=False)
    author_royalty_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.book.title} on {self.date.strftime('%Y-%m-%d')}"