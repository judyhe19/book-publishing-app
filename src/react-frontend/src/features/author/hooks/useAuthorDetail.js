// src/features/authors/hooks/useAuthorDetail.js
import { useEffect, useMemo, useState } from "react";
import { getAuthor } from "../api/authorApi";
import { apiFetch } from "../../../shared/api/http";
import { sortBooksDefault } from "../../books/components/BooksTable";

function unwrapList(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (typeof data === "object" && Array.isArray(data.results)) return data.results;
  return [];
}

export function useAuthorDetail(authorId) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [author, setAuthor] = useState(null);
  const [books, setBooks] = useState([]);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const authorData = await getAuthor(authorId);

        // fetch books filtered by author
        const booksResp = await apiFetch(
          `/api/books/?all=true&author_id=${authorId}`
        );

        const list = unwrapList(booksResp);
        const sorted = sortBooksDefault(list);

        if (!mounted) return;

        setAuthor(authorData);
        setBooks(sorted);
      } catch (err) {
        if (!mounted) return;
        setError(err?.message || "Failed to load author.");
      } finally {
        if (!mounted) return;
        setLoading(false);
      }
    }

    if (authorId) load();

    return () => {
      mounted = false;
    };
  }, [authorId]);

  const count = useMemo(() => books.length, [books]);

  return {
    loading,
    error,
    author,
    books,
    count,
  };
}