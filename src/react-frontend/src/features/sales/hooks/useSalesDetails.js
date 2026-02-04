import { useCallback, useEffect, useState } from "react";
import { getSaleDetail, updateSalesRecord, deleteSalesRecord } from "../api/salesApi";

export function useSalesDetail(saleId) {
  const [sale, setSale] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      const data = await getSaleDetail(saleId);
      setSale(data);
    } catch (e) {
      setError(e?.message || "Failed to load sale");
      setSale(null);
    } finally {
      setLoading(false);
    }
  }, [saleId]);

  useEffect(() => {
    if (!saleId) return;
    reload();
  }, [saleId, reload]);

  const save = useCallback(
    async (payload) => {
      try {
        setSaving(true);
        setError("");
        const updated = await updateSalesRecord(saleId, payload);
        setSale(updated);
        return updated;
      } catch (e) {
        setError(e?.message || "Failed to save");
        throw e;
      } finally {
        setSaving(false);
      }
    },
    [saleId]
  );

  const remove = useCallback(async () => {
    try {
      setSaving(true);
      setError("");
      await deleteSalesRecord(saleId);
    } catch (e) {
      setError(e?.message || "Failed to delete");
      throw e;
    } finally {
      setSaving(false);
    }
  }, [saleId]);

  return { sale, loading, saving, error, reload, save, remove };
}
