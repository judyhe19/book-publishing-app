import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../../../shared/api/http";

function unwrapList(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (typeof data === "object" && Array.isArray(data.results)) return data.results;
  return [];
}

export function useAuthorBooks(authorId) {
  const [loadingBooks, setLoadingBooks] = useState(false);
  const [booksError, setBooksError] = useState("");
  const [books, setBooks] = useState([]);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoadingBooks(true);
      setBooksError("");

      try {
        const data = await apiFetch(`/api/books/?all=true&author_id=${authorId}`);
        const list = unwrapList(data);

        if (!mounted) return;
        setBooks(list);
      } catch (e) {
        if (!mounted) return;
        setBooks([]);
        setBooksError(e?.message || "Failed to load books for author.");
      } finally {
        if (!mounted) return;
        setLoadingBooks(false);
      }
    }

    if (!authorId) {
      setBooks([]);
      setBooksError("");
      setLoadingBooks(false);
      return () => {
        mounted = false;
      };
    }

    load();

    return () => {
      mounted = false;
    };
  }, [authorId]);

  // We can compute hasSales using fields you already return:
  // - total_sales_to_date annotation exists on Book list responses
  const hasSales = useMemo(() => {
    return (books || []).some((b) => Number(b?.total_sales_to_date ?? 0) > 0);
  }, [books]);

  return { books, hasSales, loadingBooks, booksError };
}