from django.db.models import OuterRef, Subquery
from .models import Author

def get_first_author_name_subquery(outer_ref_field="pk"):
    """
    Returns a Subquery that fetches the name of the 'first' author
    (ordered by author_id) for the book referenced by outer_ref_field.
    """
    return Subquery(
        Author.objects.filter(
            authorbook__book=OuterRef(outer_ref_field)
        ).order_by('id').values('name')[:1]
    )
