# Sales sorting configuration
# IMPORTANT: Keep sortKeys in sync with frontend: src/features/sales/config/salesTableConfig.jsx

# Map frontend sortKey -> backend model field
SALES_SORT_FIELD_MAP = {
    'date': 'date',
    'quantity': 'quantity',
    'publisher_revenue': 'publisher_revenue',
    'publisher_revenue_original': 'publisher_revenue_original',
    'book_title': 'book__title',
    'authors': 'author_name',
    'author_royalty': 'author_royalty',
    'paid_status': 'author_paid',
    'sale_source': 'sale_source',
    'comment': 'comment',
}

SALES_DEFAULT_SORT = '-date'
