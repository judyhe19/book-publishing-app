# Sales sorting configuration
# IMPORTANT: Keep sortKeys in sync with frontend: src/features/sales/config/salesTableConfig.jsx

# Map frontend sortKey -> backend model field
SALES_SORT_FIELD_MAP = {
    'date': 'date',
    'quantity': 'quantity',
    'publisher_revenue': 'publisher_revenue',
    'book_title': 'book__title',
    'total_royalties': 'total_royalties',  # annotated field
    'paid_status': 'unpaid_count',  # 0 = all paid (sorts first ascending)
}

SALES_DEFAULT_SORT = '-date'
