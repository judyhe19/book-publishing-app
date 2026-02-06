// src/features/books/pages/BooksListPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";

import { useBooksList } from "../hooks/useBooksList";

import BooksToolbar from "../components/BooksToolbar";
import BooksTable from "../components/BooksTable";
import BooksPagination from "../components/BooksPagination";

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
  } = useBooksList({ pageSize: 10, ordering: "title" });

  const onCreateBook = () => {
    // Placeholder route (implement later)
    navigate("/books/new");
  };

  const onGoBook = (book) => {
    // Placeholder route (implement later)
    navigate(`/books/${book.id}`);
  };

  return (
    <div className="p-6 space-y-4">
      <BooksToolbar
        q={q}
        onChangeQ={setQ}
        onCreateBook={onCreateBook}
      />

      <div className="flex items-center justify-between">
        {error ? (
          <div className="text-sm text-red-600">{error}</div>
        ) : null}
      </div>

      <BooksTable
        books={books}
        ordering={ordering}
        onToggleOrdering={toggleOrdering}
        onGoBook={onGoBook}
      />

      <BooksPagination
        page={page}
        totalPages={totalPages}
        onPrev={() => setPage(Math.max(1, page - 1))}
        onNext={() => setPage(page + 1)}
      />
    </div>
  );
}
