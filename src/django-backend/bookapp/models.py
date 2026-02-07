# models.py
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

# -----------------------------
# Shared validators
# -----------------------------
isbn_13_digits = RegexValidator(
    regex=r"^\d{13}$",
    message="ISBN-13 must be exactly 13 digits.",
)

# CHANGED: allow ISBN-10 check digit to be a digit OR X (upper/lower) in final position
isbn_10_format = RegexValidator(
    regex=r"^\d{9}[\dXx]$",
    message="ISBN-10 must be 10 characters: 9 digits followed by a digit or X.",
)


# 1. AUTHOR Table
class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# 2. BOOK Table
class Book(models.Model):
    title = models.CharField(max_length=255)
    publication_date = models.DateField()

    isbn_13 = models.CharField(
        max_length=13,
        unique=True,
        validators=[isbn_13_digits],
    )

    # CHANGED: validator now allows X/x as the last character
    isbn_10 = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[isbn_10_format],
    )

    # Financials
    total_sales_to_date = models.IntegerField(default=0)

    # Relationships
    authors = models.ManyToManyField(Author, through="AuthorBook", related_name="books")

    def __str__(self):
        return self.title

    def update_total_sales(self, quantity_delta):
        """Update total_sales_to_date by the given delta."""
        self.total_sales_to_date += quantity_delta
        self.save(update_fields=["total_sales_to_date"])


# 3. AUTHOR_BOOK Table (Through Table)
class AuthorBook(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    royalty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Royalty rate as a decimal (e.g. 0.15 for 15%)",
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )

    class Meta:
        unique_together = ("author", "book")

    def __str__(self):
        return f"{self.author.name} - {self.book.title} ({self.royalty_rate})"


# 4. SALE Table
class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="sales")
    date = models.DateField()
    quantity = models.IntegerField()

    # Financial snapshots
    publisher_revenue = models.DecimalField(max_digits=10, decimal_places=2)

    # Relationships
    authors = models.ManyToManyField(Author, through="AuthorSale", related_name="sales")

    def __str__(self):
        return f"{self.quantity} x {self.book.title} on {self.date.strftime('%Y-%m-%d')}"

    def create_author_sales(self, author_royalties={}, author_paid={}):
        author_books = AuthorBook.objects.filter(book=self.book)
        for ab in author_books:
            # Check for override
            if str(ab.author.id) in author_royalties:
                royalty_amount = author_royalties[str(ab.author.id)]
            else:
                royalty_amount = self.publisher_revenue * ab.royalty_rate

            AuthorSale.objects.create(
                sale=self,
                author=ab.author,
                royalty_amount=royalty_amount,
                author_paid=author_paid.get(str(ab.author.id), False),
            )


# 5. AUTHOR_SALE Table
class AuthorSale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="author_sales")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="sales_records")
    royalty_amount = models.DecimalField(max_digits=10, decimal_places=2)
    author_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.author.name} paid ${self.royalty_amount} for Sale {self.sale.id}"
