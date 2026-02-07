import { useEffect, useState } from "react";
import { getAuthorPaymentsGrouped, payUnpaidSalesForAuthor } from "../api/salesApi";

export function useAuthorPayments() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  // ✅ backend pagination state
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  const [count, setCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // ✅ show-all toggle (only time we allow unbounded)
  const [showAll, setShowAll] = useState(false);

  const [confirm, setConfirm] = useState({ open: false, author: null });
  const [paying, setPaying] = useState(false);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();

      if (showAll) {
        params.set("all", "1");
      } else {
        params.set("page", String(page));
        params.set("page_size", String(pageSize));
      }

      const data = await getAuthorPaymentsGrouped(params.toString());

      setGroups(data?.results ?? []);
      setCount(data?.count ?? 0);
      setTotalPages(data?.total_pages ?? 1);
    } catch (e) {
      console.error("Error fetching author payment groups:", e);
      setGroups([]);
      setCount(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, showAll]);

  const toggleShowAll = () => {
    setPage(1);
    setShowAll((prev) => !prev);
  };

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
      await fetchGroups();
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
    authorGroups: groups,

    page,
    pageSize,
    count,
    totalPages,
    setPage,

    showAll,
    toggleShowAll,

    refresh: fetchGroups,

    confirm,
    paying,
    openConfirm,
    closeConfirm,
    payAllUnpaidForAuthor,
  };
}
