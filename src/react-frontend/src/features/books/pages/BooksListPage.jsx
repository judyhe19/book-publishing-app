// src/features/books/pages/BooksListPage.jsx
import React from "react";

import { useBooksList } from "../hooks/useBooksList";
import { BooksToolbar, BooksTable } from "../components";
import {
  Button,
  Pagination,
  ShowAllToggle,
  DualScrollContainer,
} from "../../../shared/components";

export default function BooksListPage() {
  const {
    loading,
    error,
    books,
    count,
    page,
    totalPages,
    q,
    setQ,
    uiOrdering,
    toggleOrdering,
    setPage,
    showAll,
    setShowAll,
  } = useBooksList({ pageSize: 50, ordering: "first_author_name,series_position,title" });

  return (
    <div className="p-6 space-y-4 max-w-full">
      <BooksToolbar q={q} onChangeQ={setQ} />

      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-600">
          {loading ? "Loading…" : `${count ?? 0} book${count === 1 ? "" : "s"}`}
          {showAll && count != null ? " (showing all)" : ""}
        </div>

        <ShowAllToggle
          showAll={showAll}
          onToggle={() => {
            setShowAll((v) => !v);
            setPage(1);
          }}
        />
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <DualScrollContainer contentWidth={1400}>
        <BooksTable
          books={books}
          ordering={uiOrdering}
          onToggleOrdering={toggleOrdering}
          rowTo={(b) => `/books/${b.id}`}
        />
      </DualScrollContainer>

      {!showAll && (
        <Pagination
          page={page}
          totalPages={totalPages}
          onPrev={() => setPage(Math.max(1, page - 1))}
          onNext={() => setPage(page + 1)}
        />
      )}
    </div>
  );
}
