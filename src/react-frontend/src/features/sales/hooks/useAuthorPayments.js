import { useEffect, useRef, useState } from "react";
import { getAuthorPaymentsGrouped, payUnpaidSalesForAuthor } from "../api/salesApi";

export function useAuthorPayments() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);

  const [count, setCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [showAll, setShowAll] = useState(false);

  const [confirm, setConfirm] = useState({ open: false, author: null });
  const [paying, setPaying] = useState(false);

  const scrollYRef = useRef(0);

  const captureScroll = () => {
    scrollYRef.current = window.scrollY || 0;
  };

  const restoreScroll = () => {
    const y = scrollYRef.current || 0;
    requestAnimationFrame(() => {
      window.scrollTo({ top: y, left: 0, behavior: "auto" });
    });
  };

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

    captureScroll();
    setPaying(true);

    try {
      await payUnpaidSalesForAuthor(confirm.author.id);

      // Close modal first so layout doesn't change after we restore scroll
      setConfirm({ open: false, author: null });

      await fetchGroups();

      // Restore after DOM updates from refetch
      restoreScroll();
    } catch (e) {
      console.error(e);
      alert("Failed to mark unpaid sales as paid for this author.");
      // if it failed, still restore (user expects to stay put)
      restoreScroll();
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