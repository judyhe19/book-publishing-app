# models.py
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.db.models.constraints import UniqueConstraint, CheckConstraint

# -----------------------------
# Shared validators
# -----------------------------
isbn_13_digits = RegexValidator(
    regex=r"^\d{13}$",
    message="ISBN-13 must be exactly 13 digits.",
)

# allow ISBN-10 check digit to be a digit OR X (upper/lower) in final position
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

    isbn_10 = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[isbn_10_format],
    )

    # NEW: single author (Evolution 2)
    # PROTECT prevents deleting an author who still has books (usually desired for accounting/history)
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="books",
    )

    # NEW: book-level royalty rates (required, defaults)
    # Stored as decimals in [0, 1], e.g. 0.50 for 50%
    distributor_author_royalty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.50,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Percentage of publisher revenue paid to the author for distributor sales (decimal, e.g. 0.50).",
    )

    hand_sold_author_royalty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.20,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Percentage of publisher revenue paid to the author for hand-sold books (decimal, e.g. 0.20).",
    )

    # NEW: required non-negative monetary values
    cover_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Non-negative cover price.",
    )

    print_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Non-negative print cost.",
    )

    # NEW: optional cover image path (served from static)
    cover_image_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional path to a web-viewable cover image (e.g. /static/covers/mybook.jpg).",
    )

    # NEW: optional series / position (must be provided together)
    series_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Optional series name. Display as "Series (position)".',
    )

    series_position = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional positive position within the series; required if series_name is set.",
    )

    class Meta:
        constraints = [
            # series_name and series_position must be both NULL or both non-NULL
            CheckConstraint(
                check=(
                    (Q(series_name__isnull=True) & Q(series_position__isnull=True))
                    | (Q(series_name__isnull=False) & Q(series_position__isnull=False))
                ),
                name="book_series_name_and_position_together",
            ),
            # (series_name, series_position) must be unique when series is present
            UniqueConstraint(
                fields=["series_name", "series_position"],
                condition=Q(series_name__isnull=False) & Q(series_position__isnull=False),
                name="unique_series_position",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def series_display(self):
        if self.series_name and self.series_position:
            return f"{self.series_name} ({self.series_position})"
        return None


# 3. SALE Table
class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="sales")
    date = models.DateField()
    quantity = models.IntegerField()

    # Financial snapshots
    publisher_revenue = models.DecimalField(max_digits=10, decimal_places=2)

    # Relationships
    authors = models.ManyToManyField(Author, through="AuthorSale", related_name="sales")

    def __str__(self):
        return f"{self.quantity} x {self.book.title} on {self.date.strftime('%Y-%m')}"

    def create_author_sales(self, author_royalties={}, author_paid={}):
        """
        Evolution 2: exactly one author per book (self.book.author)

        - If an override exists for that author id (as string), use it.
        - Otherwise compute royalty using distributor_author_royalty_rate.
          (Hand-sold rate can be used later once Sale has a way to distinguish sale type.)
        """
        author = self.book.author
        author_id_str = str(author.id)

        if author_id_str in author_royalties:
            royalty_amount = author_royalties[author_id_str]
        else:
            royalty_amount = self.publisher_revenue * self.book.distributor_author_royalty_rate

        AuthorSale.objects.create(
            sale=self,
            author=author,
            royalty_amount=royalty_amount,
            author_paid=author_paid.get(author_id_str, False),
        )


# 4. AUTHOR_SALE Table
class AuthorSale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="author_sales")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="sales_records")
    royalty_amount = models.DecimalField(max_digits=10, decimal_places=2)
    author_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.author.name} paid ${self.royalty_amount} for Sale {self.sale.id}"