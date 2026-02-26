// src/features/sales/pages/SalesDetailPage.jsx
import { useState, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Button,
  ErrorAlert,
  LoadingState,
  PageHeader,
  SaleEntryRow,
} from "../../../shared/components";
import { formatBookLabel } from "../../../shared/utils/bookUtils";
import { useSalesDetails } from "../hooks/useSalesDetails";
import { DeleteSalesRecordDialog } from "../components";

function toMonthValue(value) {
  return value ? String(value) : "";
}

function moneyNumber(x) {
  const n = Number(x);
  return Number.isNaN(n) ? 0 : n;
}

function normalizeRate(rate) {
  const r = Number(rate);
  if (Number.isNaN(r)) return 0;
  return r > 1 ? r / 100 : r;
}

function formatMoneyString(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "0";
  return n.toFixed(2);
}

/**
 * Compute auto-calculated royalties for authors whose values aren't overridden.
 * With single-author model, there's only one author per book.
 */
function computeAutoRoyalties({ bookAuthors, publisherRevenue, overrides, existing }) {
  const revenue = moneyNumber(publisherRevenue);
  const next = { ...(existing || {}) };

  for (const a of bookAuthors || []) {
    const key = String(a.author_id);
    const isOverridden = !!(overrides && overrides[key]);

    if (!isOverridden) {
      const rate = normalizeRate(a.royalty_rate);
      next[key] = formatMoneyString(revenue * rate);
    }
  }

  return next;
}

/**
 * Transform a sale record and book data into row format for SaleEntryRow.
 * Adapted for single-author model where royalty_rate comes from book.distributor_author_royalty_rate.
 */
function saleToRow(sale, bookData) {
  // Build authors array from single author (for compatibility with SaleEntryRow)
  const authors = bookData.author_id
    ? [{
        author_id: bookData.author_id,
        name: bookData.author_name,
        royalty_rate: bookData.distributor_author_royalty_rate,
      }]
    : [];

  const book = {
    value: bookData.id,
    label: formatBookLabel(bookData.title, bookData.isbn_13),
    authors,
    publication_date: bookData.publication_date,
    distributor_author_royalty_rate: bookData.distributor_author_royalty_rate,
    hand_sold_author_royalty_rate: bookData.hand_sold_author_royalty_rate,
  };

  const author_royalties = {};
  const author_paid = {};
  const overrides = {};

  // Build rate lookup from authors array
  const rateByAuthorId = {};
  for (const a of authors) {
    rateByAuthorId[String(a.author_id)] = a.royalty_rate;
  }

  // Process author details from the sale
  for (const a of sale.author_details || []) {
    const id = String(a.id);

    author_royalties[id] = String(a.royalty_amount);
    author_paid[id] = !!a.paid;

    // Determine if this royalty was overridden (differs from calculated default)
    const rate = rateByAuthorId[id];
    if (rate === undefined) {
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
    date: toMonthValue(sale.date),
    book,
    quantity: sale.quantity,
    publisher_revenue: sale.publisher_revenue,
    author_royalties,
    author_paid,
    overrides,
  };
}

export default function SalesDetailPage() {
  const { saleId } = useParams();
  const navigate = useNavigate();

  const { sale, book, loading, saving, error, save, remove } = useSalesDetails(saleId);

  const [row, setRow] = useState(null);
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    if (!sale || !book) return;
    setRow(saleToRow(sale, book));
  }, [sale, book]);

  // Auto-recalculate royalties when revenue changes
  useEffect(() => {
    if (!row || !row.book || !row.book.authors) return;

    const nextRoyalties = computeAutoRoyalties({
      bookAuthors: row.book.authors,
      publisherRevenue: row.publisher_revenue,
      overrides: row.overrides,
      existing: row.author_royalties,
    });

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
  }, [row?.publisher_revenue, row?.book?.value]);

  const handleRowChange = (index, field, value) => {
    setRow((prev) => ({ ...prev, [field]: value }));
  };

  const payload = useMemo(() => {
    if (!row || !row.book) return null;

    return {
      date: row.date,
      book: row.book.value,
      quantity: Number(row.quantity),
      publisher_revenue: String(row.publisher_revenue),
      author_royalties: row.author_royalties || {},
      author_paid: row.author_paid || {},
    };
  }, [row]);

  async function onSave() {
    if (!row || !payload) return;
    await save(payload);
    navigate(-1);
  }

  async function onConfirmDelete() {
    await remove();
    navigate(-1);
  }

  if (loading) {
    return <LoadingState message="Loading sales record..." fullPage />;
  }

  if (!sale) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <ErrorAlert>{error || "Sale not found."}</ErrorAlert>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader title="Sales Record" subtitle="View and modify sales record details.">
        <Button variant="danger" onClick={() => setDeleteOpen(true)} disabled={saving}>
          Delete
        </Button>
        <Button onClick={onSave} disabled={saving || !payload}>
          {saving ? "Saving..." : "Save Changes"}
        </Button>
      </PageHeader>

      {error && <ErrorAlert variant="leftBorder" className="mb-4">{error}</ErrorAlert>}

      <div className="space-y-6">
        {row && (
          <SaleEntryRow
            index={0}
            data={row}
            onChange={handleRowChange}
            onRemove={() => {}}
            isFirst={true}
          />
        )}
      </div>

      <DeleteSalesRecordDialog
        open={deleteOpen}
        onConfirm={onConfirmDelete}
        onCancel={() => setDeleteOpen(false)}
        saleId={sale.id}
        disabled={saving}
      />
    </div>
  );
}
