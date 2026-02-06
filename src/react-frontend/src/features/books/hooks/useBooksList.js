// src/features/books/hooks/useBooksList.js
import { useEffect, useMemo, useState } from "react";
import { getBooks } from "../api/booksApi";

/**
 * Mirrors your Sales hooks pattern:
 * - owns loading + data
 * - builds querystring
 * - refetches on param changes
 *
 * Supports:
 * - pagination: page, pageSize
 * - sorting: ordering (e.g. "title", "-publication_date")
 * - search: q
 */
export function useBooksList(initial = {}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [resp, setResp] = useState({
    count: 0,
    page: 1,
    page_size: 50,
    total_pages: 0,
    results: [],
  });

  // UI state
  const [page, setPage] = useState(initial.page ?? 1);
  const [pageSize, setPageSize] = useState(initial.pageSize ?? 10);
  const [ordering, setOrdering] = useState(initial.ordering ?? "title");
  const [q, setQ] = useState(initial.q ?? "");

  // Build query params in a stable way
  const queryParams = useMemo(() => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));

    if (ordering) params.set("ordering", ordering);

    const trimmed = (q || "").trim();
    if (trimmed) params.set("q", trimmed);

    return params.toString();
  }, [page, pageSize, ordering, q]);

  const fetchBooks = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getBooks(queryParams);

      // Defensive defaults to avoid UI crashes
      setResp({
        count: data?.count ?? 0,
        page: data?.page ?? page,
        page_size: data?.page_size ?? pageSize,
        total_pages: data?.total_pages ?? 0,
        results: data?.results ?? [],
      });
    } catch (e) {
      console.error("Error fetching books:", e);
      setError(e?.message || "Failed to load books.");
      setResp({
        count: 0,
        page,
        page_size: pageSize,
        total_pages: 0,
        results: [],
      });
    } finally {
      setLoading(false);
    }
  };

  // Refetch when query params change
  useEffect(() => {
    fetchBooks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryParams]);

  // Helpers for table header clicks:
  // toggleOrdering("title") => "title" / "-title"
  const toggleOrdering = (field) => {
    setPage(1); // changing sort should reset to first page
    setOrdering((prev) => {
      const prevField = prev?.startsWith("-") ? prev.slice(1) : prev;
      const prevDesc = prev?.startsWith("-");

      if (prevField !== field) return field; // new field asc
      return prevDesc ? field : `-${field}`; // toggle
    });
  };

  // Searching should usually reset to page 1
  const setSearch = (nextQ) => {
    setPage(1);
    setQ(nextQ);
  };

  return {
    // data
    loading,
    error,
    books: resp.results,
    count: resp.count,
    page: resp.page,
    pageSize: resp.page_size,
    totalPages: resp.total_pages,

    // query state + setters
    q,
    setQ: setSearch,
    ordering,
    setOrdering: (o) => {
      setPage(1);
      setOrdering(o);
    },

    // pagination setters
    setPage,
    setPageSize: (n) => {
      setPage(1);
      setPageSize(n);
    },

    // actions
    refresh: fetchBooks,
    toggleOrdering,
  };
}
