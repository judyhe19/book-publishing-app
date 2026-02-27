// src/features/author/hooks/useAuthorModify.js
import { useCallback, useEffect, useState } from "react";
import { deleteAuthor, getAuthor, updateAuthor } from "../api/authorApi";

export function useAuthorModify(authorId) {
  const [author, setAuthor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const fetchAuthor = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getAuthor(authorId);
      setAuthor(data);
    } catch (e) {
      console.error("Error fetching author:", e);
      setError(e?.message || "Failed to load author.");
      setAuthor(null);
    } finally {
      setLoading(false);
    }
  }, [authorId]);

  useEffect(() => {
    fetchAuthor();
  }, [fetchAuthor]);

  const save = useCallback(
    async (payload) => {
      setSaving(true);
      setError("");
      try {
        const updated = await updateAuthor(authorId, payload);
        setAuthor(updated);
        return updated;
      } catch (e) {
        console.error("Error updating author:", e);
        setError(e?.message || "Failed to save changes.");
        return null;
      } finally {
        setSaving(false);
      }
    },
    [authorId]
  );

  const remove = useCallback(async () => {
    setSaving(true);
    setError("");
    try {
      return await deleteAuthor(authorId);
    } catch (e) {
      console.error("Error deleting author:", e);
      setError(e?.message || "Failed to delete author.");
      return null;
    } finally {
      setSaving(false);
    }
  }, [authorId]);

  return { author, loading, saving, error, save, remove, refresh: fetchAuthor };
}