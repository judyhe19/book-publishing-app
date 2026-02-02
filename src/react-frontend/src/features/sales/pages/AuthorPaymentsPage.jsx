import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../../shared/components/Button";
import { Card, CardContent } from "../../../shared/components/Card";
import { Spinner } from "../../../shared/components/Spinner";
import { useAuthorPayments } from "../hooks/useAuthorPayments";
import ConfirmDialog from "../components/ConfirmDialog";
import AuthorPaymentsGroupList from "../components/AuthorPaymentsGroupList";

export default function AuthorPaymentsPage() {
  const navigate = useNavigate();
  const {
    loading,
    authorGroups,
    confirm,
    paying,
    openConfirm,
    closeConfirm,
    payAllUnpaidForAuthor,
  } = useAuthorPayments();

  const onGoBook = (bookId) => navigate(`/books/${bookId}`);
  const onGoSale = (saleId) => navigate(`/sale/${saleId}/edit`);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Author Payments</h1>
          <p className="text-slate-500 mt-1">
            Grouped by author. Review unpaid royalties and mark them paid.
          </p>
        </div>

        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate("/sales")}>
            Sales Records
          </Button>

          <Button onClick={() => { navigate("/sales/input") }}>
            Sales Input Tool
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-slate-500">
          <Spinner />
          <span>Loading author payment data...</span>
        </div>
      ) : authorGroups.length === 0 ? (
        <Card>
          <CardContent>No author payment rows found.</CardContent>
        </Card>
      ) : (
        <AuthorPaymentsGroupList
          groups={authorGroups}
          onMarkAllPaid={openConfirm}
          onGoBook={onGoBook}
          onGoSale={onGoSale}
        />
      )}

      <ConfirmDialog
        open={confirm.open}
        title="Confirm marking unpaid as paid"
        body={
          confirm.author
            ? `This will mark all unpaid royalty records for ${confirm.author.name} as paid.`
            : ""
        }
        onCancel={closeConfirm}
        onConfirm={payAllUnpaidForAuthor}
        confirming={paying}
      />
    </div>
  );
}
