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
    email = models.EmailField(
        max_length=254,
        unique=True,
        help_text="Author's primary contact email"
    )

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

    # Relationships
    authors = models.ManyToManyField(Author, through="AuthorBook", related_name="books")

    def __str__(self):
        return self.title



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
    SALE_SOURCE_CHOICES = [
        ("distributor", "Distributor"),
        ("handsold", "Handsold"),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="sales")
    date = models.DateField()
    quantity = models.IntegerField()
    sale_source = models.CharField(max_length=20, choices=SALE_SOURCE_CHOICES, default="distributor")
    comment = models.CharField(max_length=256, blank=True, null=True) # A short single-line text field for general use (max 256 characters). It is also populated during a CSV import. Optional.

    # TODO: For handsold sales, publisher_revenue should be computed as
    #       (book.cover_price - book.print_cost) × quantity
    #       once those fields exist on Book. For now it is always an input.
    publisher_revenue = models.DecimalField(max_digits=10, decimal_places=2)

    # TODO: author_royalty should be computed as
    #       author_royalty_rate × publisher_revenue
    #       where the rate comes from book.distributor_royalty_rate or
    #       book.hand_sold_royalty_rate depending on sale_source,
    #       once those fields exist on Book. For now it is an input.
    author_royalty = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    author_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity} x {self.book.title} on {self.date.strftime('%Y-%m')}"
