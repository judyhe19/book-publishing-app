// src/features/books/hooks/useBookSales.js
import { useState, useEffect } from "react";
import { getAllSales } from "../../sales/api/salesApi";

// Sort configuration for book sales table
export const BOOK_SALES_SORT_CONFIG = {
  DEFAULT_FIELD: "date",
  DEFAULT_ORDER: "-date",
  DESC_FIELDS: ["date", "quantity", "publisher_revenue", "total_royalties"],
};

export function useBookSales(bookId) {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ordering, setOrdering] = useState(BOOK_SALES_SORT_CONFIG.DEFAULT_ORDER);

  // ✅ pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [count, setCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // ✅ show-all toggle (default: paginated)
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (!bookId) return;
    fetchSales();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId, ordering, page, pageSize, showAll]);

  const fetchSales = async () => {
    setLoading(true);
    try {
      const params = {
        book_id: String(bookId),
        ordering: ordering,
      };

      if (showAll) {
        params.all = "1";
      } else {
        params.page = String(page);
        params.page_size = String(pageSize);
      }

      const queryParams = new URLSearchParams(params).toString();
      const data = await getAllSales(queryParams);

      const rows = Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
        ? data.results
        : [];

      setSales(rows);

      const nextTotalPages = data?.total_pages ?? 1;
      setCount(data?.count ?? rows.length);
      setTotalPages(nextTotalPages);

      // clamp if needed (only relevant when paginating)
      if (!showAll && page > nextTotalPages) setPage(nextTotalPages);
    } catch (error) {
      console.error("Error fetching book sales:", error);
      setSales([]);
      setCount(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    setPage(1); // ✅ reset page when sorting changes
    setOrdering((prev) => {
      if (prev === `-${field}`) return field;
      if (prev === field) return `-${field}`;
      if (BOOK_SALES_SORT_CONFIG.DESC_FIELDS.includes(field)) return `-${field}`;
      return field;
    });
  };

  const toggleShowAll = () => {
    setPage(1);
    setShowAll((prev) => !prev);
  };

  return {
    sales,
    loading,
    ordering,
    handleSort,
    refresh: fetchSales,

    page,
    pageSize,
    count,
    totalPages,
    setPage,

    showAll,
    toggleShowAll,
  };
}
