// src/features/sales/pages/SalesDetailPage.jsx
import { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../../../shared/components/Button";
import { Spinner } from "../../../shared/components/Spinner";
import SaleEntryRow from "../../../shared/components/SaleEntryRow";
import { formatBookLabel } from "../../../shared/utils/bookUtils";

import { useSalesDetails } from "../hooks/useSalesDetails";
import DeleteSalesRecordDialog from "../components/DeleteSalesRecordDialog";

function toMonthValue(value) {
  if (!value) return "";
  const s = String(value);
  const yyyyMmDd = s.length >= 10 ? s.slice(0, 10) : s; // handles ISO datetime too
  return yyyyMmDd.split("-").length >= 2 ? yyyyMmDd.slice(0, 7) : yyyyMmDd;
}

function moneyNumber(x) {
  const n = Number(x);
  return Number.isNaN(n) ? 0 : n;
}

// royalty_rate could be "10" (percent) or "0.10" (fraction). Handle both safely.
function normalizeRate(rate) {
  const r = Number(rate);
  if (Number.isNaN(r)) return 0;
  return r > 1 ? r / 100 : r;
}

function formatMoneyString(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "0";
  // keep stable money formatting (string) for inputs
  return n.toFixed(2);
}

function computeAutoRoyalties({
  bookAuthors,
  publisherRevenue,
  overrides,
  existing,
}) {
  const revenue = moneyNumber(publisherRevenue);
  const next = { ...(existing || {}) };

  for (const a of bookAuthors || []) {
    const key = String(a.author_id);
    const isOverridden = !!(overrides && overrides[key]);

    // Only auto-update if this author isn't overridden
    if (!isOverridden) {
      const rate = normalizeRate(a.royalty_rate);
      next[key] = formatMoneyString(revenue * rate);
    }
  }

  return next;
}

function saleToRow(sale, bookData) {
  // Use book data from the books API (same source as SalesInputPage)
  const book = {
    value: bookData.id,
    label: formatBookLabel(bookData.title, bookData.isbn_13),
    authors: (bookData.authors || []).map((a) => ({
      author_id: a.author_id,
      name: a.name,
      royalty_rate: a.royalty_rate,
    })),
    publication_date: bookData.publication_date,
  };

  const author_royalties = {};
  const author_paid = {};
  const overrides = {};

  // ✅ build a lookup so we can determine whether a saved royalty differs from default
  const rateByAuthorId = {};
  for (const a of book.authors || []) {
    rateByAuthorId[String(a.author_id)] = a.royalty_rate;
  }

  for (const a of sale.author_details || []) {
    const id = String(a.id);

    author_royalties[id] = String(a.royalty_amount);
    author_paid[id] = !!a.paid;

    // ✅ If saved royalty differs from the default computed royalty, mark as overridden
    const rate = rateByAuthorId[id];
    if (rate === undefined) {
      // if we can't compute a default, treat as overridden to avoid clobbering
      overrides[id] = true;
    } else {
      const revenue = moneyNumber(sale.publisher_revenue);
      const defaultAmt = revenue * normalizeRate(rate);
      const savedAmt = Number(a.royalty_amount);

      overrides[id] =
        Number.isFinite(savedAmt) && Number.isFinite(defaultAmt)
          ? Math.abs(savedAmt - defaultAmt) > 0.009
          : true;
    }
  }

  return {
    isEdit: true,
    date: toMonthValue(sale.date), // ✅ normalize to YYYY-MM for month inputs
    book,
    quantity: sale.quantity,
    publisher_revenue: sale.publisher_revenue,
    author_royalties,
    author_paid,
    overrides,
  };
}

function formatMonthYear(isoDate) {
  if (!isoDate) return "";

  const [y, m] = isoDate.split("-").map(Number);
  if (!y || !m) return isoDate;

  const d = new Date(Date.UTC(y, m - 1, 1));
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(d);
}

export default function SalesDetailPage() {
  const { saleId } = useParams();
  const navigate = useNavigate();

  const { sale, book, loading, saving, error, save, remove } = useSalesDetails(
    saleId
  );

  const [row, setRow] = useState(null);
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    if (!sale || !book) return;
    setRow(saleToRow(sale, book));
  }, [sale, book]);

  // ✅ Auto-recalculate royalties whenever revenue changes (or book authors load),
  // but ONLY for authors that are not overridden.
  useEffect(() => {
    if (!row || !row.book || !row.book.authors) return;

    const nextRoyalties = computeAutoRoyalties({
      bookAuthors: row.book.authors,
      publisherRevenue: row.publisher_revenue,
      overrides: row.overrides,
      existing: row.author_royalties,
    });

    // Avoid infinite loops: only set if something actually changed.
    const prev = row.author_royalties || {};
    const nextKeys = Object.keys(nextRoyalties);
    let changed = false;

    if (Object.keys(prev).length !== nextKeys.length) {
      changed = true;
    } else {
      for (const k of nextKeys) {
        if (String(prev[k] ?? "") !== String(nextRoyalties[k] ?? "")) {
          changed = true;
          break;
        }
      }
    }

    if (changed) {
      setRow((prevRow) => ({ ...prevRow, author_royalties: nextRoyalties }));
    }
  }, [row?.publisher_revenue, row?.book?.value]); // intentional: recompute on revenue change + when book loads/changes

  const handleRowChange = (index, field, value) => {
    setRow((prev) => ({ ...prev, [field]: value }));
  };

  const payload = useMemo(() => {
    if (!row || !row.book) return null;

    // ensure date is in full date format (YYYY-MM-DD), appending -01 if it's just YYYY-MM
    const dateStr =
      row.date && row.date.split("-").length === 2 ? `${row.date}-01` : row.date;

    return {
      date: dateStr,
      book: row.book.value,
      quantity: Number(row.quantity),
      publisher_revenue: String(row.publisher_revenue),
      author_royalties: row.author_royalties || {},
      author_paid: row.author_paid || {},
    };
  }, [row]);

  async function onSave() {
    if (!row) return;
    if (!payload) return;

    console.log("Saving payload:", JSON.stringify(payload, null, 2));
    await save(payload);
    navigate(-1);
  }

  async function onConfirmDelete() {
    await remove();
    navigate(-1);
  }

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-2 text-slate-500">
          <Spinner />
          <span>Loading sales record...</span>
        </div>
      </div>
    );
  }

  if (!sale) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <p className="text-red-600">{error || "Sale not found."}</p>
        <Button
          variant="secondary"
          onClick={() => {
            navigate(-1);
          }}
        >
          Back
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Sales Record</h1>
          <p className="text-slate-500 mt-1">
            View and modify sales record details.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Back
          </Button>
          <Button
            variant="secondary"
            onClick={() => setDeleteOpen(true)}
            disabled={saving}
          >
            Delete
          </Button>
          <Button onClick={onSave} disabled={saving || !payload}>
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>

      {error ? (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4 rounded-md">
          <p className="text-sm text-red-700 whitespace-pre-wrap">{error}</p>
        </div>
      ) : null}

      <div className="space-y-6">
        {row ? (
          <SaleEntryRow
            index={0}
            data={row}
            onChange={handleRowChange}
            onRemove={() => {}}
            isFirst={true}
          />
        ) : null}
      </div>

      <DeleteSalesRecordDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onConfirm={onConfirmDelete}
        onCancel={() => setDeleteOpen(false)}
        saleId={sale.id}
        disabled={saving}
      />
    </div>
  );
}
