# Sales sorting configuration
# IMPORTANT: Keep sortKeys in sync with frontend: src/features/sales/config/salesTableConfig.jsx

# Map frontend sortKey -> backend model field
SALES_SORT_FIELD_MAP = {
    'date': 'date',
    'quantity': 'quantity',
    'publisher_revenue': 'publisher_revenue',
    'book_title': 'book__title',
    'authors': 'first_author_name',  # annotated field - first author's name
    'total_royalties': 'author_royalty',  # direct field on Sale
    'paid_status': 'author_paid',  # direct boolean field on Sale
}

SALES_DEFAULT_SORT = '-date'
