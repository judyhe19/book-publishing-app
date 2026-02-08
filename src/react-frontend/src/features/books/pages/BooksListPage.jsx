// src/features/books/pages/BooksListPage.jsx
import React, { useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";

import { useBooksList } from "../hooks/useBooksList";

import BooksToolbar from "../components/BooksToolbar";
import BooksTable from "../components/BooksTable";
import BooksPagination from "../components/BooksPagination";
import { Button } from "../../../shared/components/Button";

export default function BooksListPage() {
  const navigate = useNavigate();

  const {
    loading,
    error,
    books,
    count,
    page,
    totalPages,
    q,
    setQ,
    ordering,
    toggleOrdering,
    setPage,
    showAll,
    setShowAll,
  } = useBooksList({ pageSize: 50, ordering: "title" });

  // Synchronized scroll refs for top and bottom scrollbars
  const topScrollRef = useRef(null);
  const bottomScrollRef = useRef(null);

  const handleTopScroll = useCallback(() => {
    if (bottomScrollRef.current && topScrollRef.current) {
      bottomScrollRef.current.scrollLeft = topScrollRef.current.scrollLeft;
    }
  }, []);

  const handleBottomScroll = useCallback(() => {
    if (topScrollRef.current && bottomScrollRef.current) {
      topScrollRef.current.scrollLeft = bottomScrollRef.current.scrollLeft;
    }
  }, []);

  const onCreateBook = () => {
    navigate("/books/input");
  };

  const onGoBook = (book) => {
    navigate(`/books/${book.id}`);
  };

  return (
    <div className="p-6 space-y-4 max-w-full">
      <BooksToolbar q={q} onChangeQ={setQ} onCreateBook={onCreateBook} />

      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-600">
          {loading ? "Loading…" : `${count ?? 0} book${count === 1 ? "" : "s"}`}
          {showAll && count != null ? " (showing all)" : ""}
        </div>

        <Button
          variant="secondary"
          onClick={() => {
            setShowAll((v) => !v);
            setPage(1);
          }}
        >
          {showAll ? "Paginate" : "Show all"}
        </Button>
      </div>

      {error ? <div className="text-sm text-red-600">{error}</div> : null}

      {/* Top scrollbar */}
      <div
        ref={topScrollRef}
        onScroll={handleTopScroll}
        className="overflow-x-auto"
        style={{ height: "20px" }}
      >
        <div style={{ width: "1400px", height: "1px" }} />
      </div>

      {/* Table with bottom scrollbar */}
      <div
        ref={bottomScrollRef}
        onScroll={handleBottomScroll}
        className="overflow-x-auto"
      >
        <div style={{ minWidth: "1400px" }}>
          <BooksTable
            books={books}
            ordering={ordering}
            onToggleOrdering={toggleOrdering}
            onGoBook={onGoBook}
          />
        </div>
      </div>

      {!showAll && (
        <BooksPagination
          page={page}
          totalPages={totalPages}
          onPrev={() => setPage(Math.max(1, page - 1))}
          onNext={() => setPage(page + 1)}
        />
      )}
    </div>
  );
}
