// src/features/sales/components/AuthorPaymentsGroupCard.jsx
import React, { useState } from "react";
import { Card, CardContent, Button, ShowAllToggle } from "../../../shared/components";
import AuthorPaymentsTable from "./AuthorPaymentsTable";

function money(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "$0.00";
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function paymentAmount(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
}

function buildPayPalLink(username, amount) {
  if (!username) return null;
  return `https://paypal.me/${encodeURIComponent(username)}/${paymentAmount(amount)}USD`;
}

function buildVenmoLink(username, amount, note) {
  if (!username) return null;

  const params = new URLSearchParams();
  params.set("amount", paymentAmount(amount));
  if (note) params.set("note", note);

  return `https://venmo.com/${encodeURIComponent(username)}?${params.toString()}`;
}

export default function AuthorPaymentsGroupCard({ group, onMarkAllPaid, onGoSale }) {
  const { author, rows, unpaidTotal, unpaidCount, projectedTotal, projectedCount } = group;

  const [page, setPage] = useState(1);
  const [showAllRows, setShowAllRows] = useState(false);
  const pageSize = 10;

  const totalRows = rows.length;
  const totalPages = Math.ceil(totalRows / pageSize);

  const paginatedRows = showAllRows
    ? rows
    : rows.slice((page - 1) * pageSize, page * pageSize);

  const handlePrev = () => setPage((p) => Math.max(1, p - 1));
  const handleNext = () => setPage((p) => Math.min(totalPages, p + 1));
  const toggleShowAll = () => {
    setShowAllRows((prev) => !prev);
    setPage(1);
  };

  const payableTotal = unpaidTotal;
  const payableCount = unpaidCount;

  const paypalLink = buildPayPalLink(author.paypal, payableTotal);
  const venmoLink = buildVenmoLink(
    author.venmo,
    payableTotal,
    `Book royalty payment for ${author.name}`
  );

  return (
    <Card>
      <CardContent>
        <div className="flex justify-between items-start gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{author.name}</h2>

            <p className="text-slate-600 mt-1">
              Unpaid subtotal:{" "}
              <span className="font-semibold text-slate-900">{money(payableTotal)}</span>{" "}
              ({payableCount} unpaid record{payableCount === 1 ? "" : "s"})
            </p>

            <p className="text-amber-700 mt-1">
              Projected subtotal:{" "}
              <span className="font-semibold">{money(projectedTotal)}</span>{" "}
              ({projectedCount} projected record{projectedCount === 1 ? "" : "s"}) — not eligible
              for payment yet
            </p>

            {(author.paypal || author.venmo) && payableCount > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {paypalLink && (
                  <a
                    href={paypalLink}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center rounded-lg px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Pay with PayPal
                  </a>
                )}

                {venmoLink && (
                  <a
                    href={venmoLink}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center rounded-lg px-3 py-2 text-sm font-medium text-white bg-slate-800 hover:bg-slate-900 transition"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Pay with Venmo
                  </a>
                )}
              </div>
            )}
          </div>

          <Button disabled={payableCount === 0} onClick={onMarkAllPaid}>
            Mark payable sales as paid
          </Button>
        </div>

        <div className="mt-4">
          <AuthorPaymentsTable rows={paginatedRows} onGoSale={onGoSale} />

          {totalRows > pageSize && (
            <div className="mt-3 flex items-center justify-between text-sm">
              <span className="text-slate-600">
                {showAllRows
                  ? `Showing all ${totalRows} records`
                  : `Showing ${(page - 1) * pageSize + 1}–${Math.min(
                      page * pageSize,
                      totalRows
                    )} of ${totalRows} records`}
              </span>

              <div className="flex items-center gap-2">
                <ShowAllToggle showAll={showAllRows} onToggle={toggleShowAll} />

                {!showAllRows && (
                  <>
                    <Button variant="secondary" onClick={handlePrev} disabled={page <= 1}>
                      ← Prev
                    </Button>
                    <span className="text-slate-600">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="secondary"
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