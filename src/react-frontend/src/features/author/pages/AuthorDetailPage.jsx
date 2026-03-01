// src/features/authors/pages/AuthorDetailPage.jsx
import React from "react";
import { useNavigate, useParams } from "react-router-dom";

import BooksTable, {
  buildAuthorRoyaltyColumns,
} from "../../books/components/BooksTable";
import { useAuthorDetail } from "../hooks/useAuthorDetail";
import { DualScrollContainer, Button } from "../../../shared/components";

export default function AuthorDetailPage() {
  const navigate = useNavigate();
  const { authorId } = useParams();

  const { loading, error, author, books, count } = useAuthorDetail(authorId);

  const onGoBook = (book) => {
    navigate(`/books/${book.id}`);
  };

  return (
    <div className="p-6 space-y-4 max-w-full">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            {author?.name || (loading ? "Loading…" : "Author")}
          </h1>
          <div className="text-sm text-slate-600">
            {author?.email || "—"}
          </div>
        </div>

        <Button variant="secondary" onClick={() => navigate("/authors")}>
          Back
        </Button>
      </div>

      <div className="text-sm text-slate-600">
        {loading ? "Loading…" : `${count} book${count === 1 ? "" : "s"}`}
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <DualScrollContainer contentWidth={1600}>
        <BooksTable
          books={books}
          showAuthor={false}
          sortable={false}
          ordering={null}
          onToggleOrdering={null}
          onGoBook={onGoBook}
          extraColumns={buildAuthorRoyaltyColumns()}
        />
      </DualScrollContainer>
    </div>
  );
}