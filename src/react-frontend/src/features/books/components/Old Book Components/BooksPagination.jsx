// src/features/books/components/BooksPagination.jsx
import React from "react";
import { Button } from "../../../shared/components/Button";

export default function BooksPagination({
  page,
  totalPages,
  onPrev,
  onNext,
}) {
  const canPrev = page > 1;
  const canNext = totalPages && page < totalPages;

  return (
    <div className="flex items-center justify-between">
      <div className="text-sm text-slate-600">
        Page <span className="font-semibold text-slate-900">{page}</span>
        {totalPages ? (
          <>
            {" "}of <span className="font-semibold text-slate-900">{totalPages}</span>
          </>
        ) : null}
      </div>

      <div className="flex items-center gap-2">
        <Button variant="secondary" disabled={!canPrev} onClick={onPrev}>
          Previous
        </Button>
        <Button variant="secondary" disabled={!canNext} onClick={onNext}>
          Next
        </Button>
      </div>
    </div>
  );
}
