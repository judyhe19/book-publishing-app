import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../../../shared/components/Button";
import { Spinner } from "../../../shared/components/Spinner";
import { Card, CardContent } from "../../../shared/components/Card";
import SaleEntryRow from "../../../shared/components/SaleEntryRow";
import { formatBookLabel } from "../../../shared/utils/bookUtils";

import { useSalesDetails } from "../hooks/useSalesDetails";
import DeleteSalesRecordDialog from "../components/DeleteSalesRecordDialog";

function saleToRow(sale, bookData) {
  // Use book data from the books API (same source as SalesInputPage)
  const book = {
    value: bookData.id,
    label: formatBookLabel(bookData.title, bookData.isbn_13),
    authors: (bookData.authors || []).map(a => ({
      author_id: a.author_id,
      name: a.name,
      royalty_rate: a.royalty_rate,
    })),
  };

  const author_royalties = {};
  const author_paid = {};
  const overrides = {};

  for (const a of sale.author_details || []) {
    author_royalties[String(a.id)] = String(a.royalty_amount);
    author_paid[String(a.id)] = !!a.paid;
    overrides[String(a.id)] = true;
  }

  return {
    isEdit: true,
    date: sale.date,
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
  return new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric", timeZone: "UTC", }).format(d);
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

  const handleRowChange = (index, field, value) => {
    setRow((prev) => ({ ...prev, [field]: value }));
  };

const payload = useMemo(() => {
  if (!row || !row.book) return null;

    // ensure date is in full date format (YYYY-MM-DD), appending -01 if it's just YYYY-MM
    const dateStr = row.date && row.date.split('-').length === 2 
        ? `${row.date}-01` 
        : row.date;

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
    if (!payload) return;
    console.log('Saving payload:', JSON.stringify(payload, null, 2));
    await save(payload);
    navigate(-1);
  }

  async function onConfirmDelete() {
    await remove();
    navigate("/sales");
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
        <Button variant="secondary" onClick={() => navigate("/sales")}>Back</Button>
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
          <Button variant="secondary" onClick={() => navigate("/sales")}>
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
          <p className="text-sm text-red-700">{error}</p>
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
