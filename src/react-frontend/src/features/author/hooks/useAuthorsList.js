// src/features/author/hooks/useAuthorsList.js
import { useState, useEffect } from "react";
import { getAllAuthors } from "../api/authorApi";
import { SORT_CONFIG } from "../config/authorsTableConfig";

export function useAuthorsList() {
  const [authors, setAuthors] = useState([]);
  const [loading, setLoading] = useState(true);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [count, setCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [showAll, setShowAll] = useState(false);

  // ✅ keyword filter (covers name + email) -> backend expects `q`
  const [filters, setFilters] = useState({
    q: "",
    ordering: SORT_CONFIG.DEFAULT_ORDER,
  });

  useEffect(() => {
    fetchAuthors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.q, filters.ordering, page, pageSize, showAll]);

  const fetchAuthors = async () => {
    setLoading(true);
    try {
      const activeFilters = {};

      const trimmed = (filters.q || "").trim();
      if (trimmed) activeFilters.q = trimmed;
      if (filters.ordering) activeFilters.ordering = filters.ordering;

      if (showAll) {
        activeFilters.all = "1";
      } else {
        activeFilters.page = String(page);
        activeFilters.page_size = String(pageSize);
      }

      const queryParams = new URLSearchParams(activeFilters).toString();
      const data = await getAllAuthors(queryParams);

      setAuthors(data.results || []);
      setCount(data.count ?? 0);
      setTotalPages(data.total_pages ?? 1);
    } catch (error) {
      console.error("Error fetching authors:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    setPage(1);
    setFilters((prev) => {
      if (prev.ordering === `-${field}`) return { ...prev, ordering: field };
      if (prev.ordering === field) return { ...prev, ordering: `-${field}` };
      if (SORT_CONFIG.DESC_FIELDS.includes(field)) return { ...prev, ordering: `-${field}` };
      return { ...prev, ordering: field };
    });
  };

  const handleSearchChange = (e) => {
    setPage(1);
    setFilters((prev) => ({ ...prev, q: e.target.value }));
  };

  const toggleShowAll = () => {
    setPage(1);
    setShowAll((prev) => !prev);
  };

  return {
    authors,
    loading,
    filters,
    handleSort,
    handleSearchChange,
    refresh: fetchAuthors,

    page,
    pageSize,
    count,
    totalPages,
    setPage,

    showAll,
    toggleShowAll,
  };
}