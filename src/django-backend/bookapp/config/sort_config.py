# Sales sorting configuration
# IMPORTANT: Keep sortKeys in sync with frontend: src/features/sales/config/salesTableConfig.jsx

# Map frontend sortKey -> backend model field
SALES_SORT_FIELD_MAP = {
    'date': 'date',
    'quantity': 'quantity',
    'publisher_revenue': 'publisher_revenue',
    'book_title': 'book__title',
    'authors': 'first_author_name',  # annotated field - first author's name
    'total_royalties': 'total_royalties',  # annotated field - total royalties for this sale
    'paid_status': 'unpaid_count',  # annotated field - 0 = all paid (sorts first ascending)
}

SALES_DEFAULT_SORT = '-date'
