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
        blank=True,
        null=True,
        help_text="Author's primary contact email"
    )
    paypal = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Author's account name for PayPal (paypal.me username, not email)"
    )
    venmo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Author's account name for Venmo"
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

    amazon_asin_ebook = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9]{10}$",
                message="Amazon ASIN must be exactly 10 uppercase alphanumeric characters (e.g. B09XYZ1234).",
            )
        ],
        help_text="Amazon's unique identifier for the ebook edition of this book (e.g. B09XYZ1234). Optional.",
    )

    released = models.BooleanField(
        default=False,
        help_text="Indicates whether this book has been released to the public. "
                  "Only released books are eligible for author royalty payment.",
    )

    kickstarter_item_tag_ebook = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^\S+$",
                message="Kickstarter item tag must contain no whitespace.",
            )
        ],
        help_text='Kickstarter tag for the ebook edition (e.g. "ebook-the-hobbit"). Optional.',
    )

    kickstarter_item_tag_print = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^\S+$",
                message="Kickstarter item tag must contain no whitespace.",
            )
        ],
        help_text='Kickstarter tag for the print edition (e.g. "paperback-the-hobbit"). Optional.',
    )

    # Single author per book
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name="books",
    )

    # Book-level royalty rates (decimals in [0, 1])
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

    # Required non-negative monetary values
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

    # Optional cover image path (served from static)
    cover_image_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional path to a web-viewable cover image (e.g. /static/covers/mybook.jpg).",
    )

    # Optional series / position (must be provided together)
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
                condition=(
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
    SALE_SOURCE_CHOICES = [
        ("distributor", "Distributor"),
        ("handsold", "Handsold"),
        ("kickstarter", "Kickstarter"),
    ]

    FORMAT_CHOICES = [
        ("print", "Print"),
        ("ebook", "eBook"),
        ("kindle unlimited", "Kindle Unlimited"),
    ]

    DISTRIBUTOR_CHOICES = [
        ("Ingram Spark", "Ingram Spark"),
        ("Amazon", "Amazon"),
        ("Other", "Other"),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="sales")
    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )
    date = models.DateField()
    quantity = models.PositiveIntegerField(blank=True, null=True) # unspecified if format is "kindle unlimited".
    sale_source = models.CharField(max_length=20, choices=SALE_SOURCE_CHOICES, default="distributor")
    comment = models.CharField(max_length=256, blank=True, null=True)

    # Required if sale source is distributor; unspecified when sale source is handsold.
    distributor = models.CharField(max_length=100, blank=True, null=True, choices=DISTRIBUTOR_CHOICES) 
    format = models.CharField(max_length=30, choices=FORMAT_CHOICES, default="print")
    currency = models.CharField(max_length=3, default="USD") # Locked to USD for handsold records
    publisher_revenue_original = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    # field only available if format is "kindle unlimited", in which case it is a required non-negative numeric input indicating the number of KENP (def 26) for this sales record.
    kenp = models.PositiveIntegerField(blank=True, null=True)

    publisher_revenue = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="Publisher revenue normalized to USD. Used for royalty computations.")
    author_royalty = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Computed author royalty in USD. Cannot be overridden.")
    author_paid = models.BooleanField(default=False)

    def __str__(self):
        qty = self.kenp if self.format == "kindle unlimited" else self.quantity
        return f"{qty} x {self.book.title} on {self.date.strftime('%Y-%m')}"  # noqa: E501