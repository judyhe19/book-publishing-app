"""
Shared pagination class for all ViewSets.
Produces the same response shape the frontend expects:
  { count, page, page_size, total_pages, results }
"""
from math import ceil

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        Support `?all=1` to bypass pagination and return all results.
        """
        show_all = request.query_params.get("all") in ("1", "true", "True", "yes")

        if show_all:
            self._show_all = True
            self._total = queryset.count() if hasattr(queryset, 'count') else len(queryset)
            # Return full list (no slicing)
            return list(queryset)

        self._show_all = False
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if getattr(self, "_show_all", False):
            return Response({
                "count": self._total,
                "page": 1,
                "page_size": self._total,
                "total_pages": 1,
                "results": data,
            })

        total = self.page.paginator.count
        page_size = self.get_page_size(self.request)
        return Response({
            "count": total,
            "page": self.page.number,
            "page_size": page_size,
            "total_pages": max(1, ceil(total / page_size)),
            "results": data,
        })
