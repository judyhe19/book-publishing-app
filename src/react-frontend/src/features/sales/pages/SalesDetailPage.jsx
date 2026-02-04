import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../../../shared/components/Button";
import { Spinner } from "../../../shared/components/Spinner";
import { Card, CardContent } from "../../../shared/components/Card";

import SalesInputRow from "../components/SalesInputRow";
import { useSalesDetails } from "../hooks/useSalesDetails";
import DeleteSalesRecordDialog from "../components/DeleteSalesRecordDialog";

function saleToRow(sale) {
  const date = sale.date;

  const bookObj = {
    value: sale.book,
    label: sale.book_title,
    authors: (sale.author_details || []).map(a => ({
      author_id: a.author_id,
      name: a.name,
    })),
  };

  const author_royalties = {};
  const author_paid = {};

  for (const a of sale.author_details || []) {
    author_royalties[a.author_id] = a.royalty_amount;
    author_paid[a.author_id] = !!a.author_paid;
  }

  return {
    date,
    book: bookObj,
    quantity: sale.quantity,
    publisher_revenue: sale.publisher_revenue,
    author_royalties,
    author_paid,
  };
}



export default function SalesDetailPage() {
  const { saleId } = useParams();
  const navigate = useNavigate();

  const { sale, loading, saving, error, save, remove } = useSalesDetails(saleId);

  const [row, setRow] = useState(null);
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    if (!sale) return;
    setRow(saleToRow(sale));
  }, [sale]);

  const handleRowChange = (index, field, value) => {
    setRow((prev) => ({ ...prev, [field]: value }));
  };

  const payload = useMemo(() => {
    if (!row) return null;

    const book_id = row.book?.value ?? row.book?.id ?? null;

    return {
      date: row.date,
      book_id,
      quantity: row.quantity,
      publisher_revenue: row.publisher_revenue,
      author_royalties: row.author_royalties || {},
      author_paid: row.author_paid || {},
    };
  }, [row]);

  async function onSave() {
    if (!payload) return;
    await save(payload);
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
            View and modify all fields for record #{sale.id}.
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
        {/* “View all fields” section */}
        <Card>
            <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                <div><span className="text-slate-500">Sale ID:</span> {sale.id}</div>
                <div><span className="text-slate-500">Book:</span> {sale.book_title}</div>
                <div><span className="text-slate-500">Date:</span> {sale.date || `${sale.year}-${sale.month}`}</div>
            </div>
            </CardContent>
        </Card>

        {row ? (
            <SalesInputRow
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
