import React, { useState } from "react";
import { Card, CardContent } from "../../../shared/components/Card";
import { Button } from "../../../shared/components/Button";
import AuthorPaymentsTable from "./AuthorPaymentsTable";

function money(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "$0.00";
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export default function AuthorPaymentsGroupCard({ group, onMarkAllPaid, onGoBook, onGoSale }) {
  const { author, rows, unpaidTotal, unpaidCount } = group;
  
  // Per-author pagination state
  const [page, setPage] = useState(1);
  const [showAllRows, setShowAllRows] = useState(false);
  const pageSize = 10;
  
  const totalRows = rows.length;
  const totalPages = Math.ceil(totalRows / pageSize);
  
  // Get paginated rows
  const paginatedRows = showAllRows
    ? rows
    : rows.slice((page - 1) * pageSize, page * pageSize);

  const handlePrev = () => setPage((p) => Math.max(1, p - 1));
  const handleNext = () => setPage((p) => Math.min(totalPages, p + 1));
  const toggleShowAll = () => {
    setShowAllRows((prev) => !prev);
    setPage(1);
  };

  return (
    <Card>
      <CardContent>
        <div className="flex justify-between items-start gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{author.name}</h2>
            <p className="text-slate-600 mt-1">
              Unpaid subtotal:{" "}
              <span className="font-semibold text-slate-900">{money(unpaidTotal)}</span>
              {" "}({unpaidCount} unpaid record{unpaidCount === 1 ? "" : "s"})
            </p>
          </div>

          <Button disabled={unpaidCount === 0} onClick={onMarkAllPaid}>
            Mark all unpaid as paid
          </Button>
        </div>

        <div className="mt-4">
          <AuthorPaymentsTable
            rows={paginatedRows}
            onGoBook={onGoBook}
            onGoSale={onGoSale}
          />
          
          {/* Per-author pagination controls */}
          {totalRows > pageSize && (
            <div className="mt-3 flex items-center justify-between text-sm">
              <span className="text-slate-600">
                {showAllRows
                  ? `Showing all ${totalRows} records`
                  : `Showing ${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, totalRows)} of ${totalRows} records`}
              </span>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={toggleShowAll}
                >
                  {showAllRows ? "Paginate" : "Show all"}
                </Button>
                
                {!showAllRows && (
                  <>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handlePrev}
                      disabled={page <= 1}
                    >
                      ← Prev
                    </Button>
                    <span className="text-slate-600">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleNext}
                      disabled={page >= totalPages}
                    >
                      Next →
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
