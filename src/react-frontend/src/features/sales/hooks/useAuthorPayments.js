import { useEffect, useMemo, useState } from "react";
import { getAllSales, payUnpaidSalesForAuthor } from "../api/salesApi";

function moneyNumber(x) {
  const n = Number(x);
  return Number.isNaN(n) ? 0 : n;
}

export function useAuthorPayments() {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);

  const [confirm, setConfirm] = useState({ open: false, author: null });
  const [paying, setPaying] = useState(false);

  const fetchSales = async () => {
    setLoading(true);
    try {
      const data = await getAllSales("");

      // ✅ after pagination: backend returns { results: [...] }
      // ✅ keep backward compatibility if it ever returns a raw array
      const results = Array.isArray(data) ? data : (data?.results ?? []);

      setSales(results);
    } catch (e) {
      console.error("Error fetching sales:", e);
      setSales([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSales();
  }, []);

  const authorGroups = useMemo(() => {
    const groups = new Map();

    for (const sale of sales || []) {
      const authors = sale.author_details || [];
      for (const a of authors) {
        if (a?.id == null) continue;

        if (!groups.has(a.id)) {
          groups.set(a.id, {
            author: { id: a.id, name: a.name || `Author ${a.id}` },
            rows: [],
          });
        }

        groups.get(a.id).rows.push({
          sale,
          author: a,
          dateKey: new Date(sale.date).getTime(),
          royalty: moneyNumber(a.royalty_amount),
          paid: Boolean(a.paid),
        });
      }
    }

    const arr = Array.from(groups.values());
    arr.sort((g1, g2) => (g1.author.name || "").localeCompare(g2.author.name || ""));

    for (const g of arr) {
      g.rows.sort((r1, r2) => r2.dateKey - r1.dateKey);
      g.unpaidTotal = g.rows.reduce((sum, r) => sum + (r.paid ? 0 : r.royalty), 0);
      g.unpaidCount = g.rows.reduce((sum, r) => sum + (r.paid ? 0 : 1), 0);
    }

    return arr;
  }, [sales]);

  const openConfirm = (author) => setConfirm({ open: true, author });
  const closeConfirm = () => {
    if (paying) return;
    setConfirm({ open: false, author: null });
  };

  const payAllUnpaidForAuthor = async () => {
    if (!confirm.author) return;
    setPaying(true);
    try {
      await payUnpaidSalesForAuthor(confirm.author.id);
      await fetchSales();
      closeConfirm();
    } catch (e) {
      console.error(e);
      alert("Failed to mark unpaid sales as paid for this author.");
    } finally {
      setPaying(false);
    }
  };

  return {
    loading,
    authorGroups,
    refresh: fetchSales,

    confirm,
    paying,
    openConfirm,
    closeConfirm,
    payAllUnpaidForAuthor,
  };
}
