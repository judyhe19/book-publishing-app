// src/features/sales/pages/AuthorPaymentsPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  Card,
  CardContent,
  LoadingState,
  PageHeader,
  Pagination,
  ShowAllToggle,
  ConfirmDialog,
} from "../../../shared/components";
import { useAuthorPayments } from "../hooks/useAuthorPayments";
import { AuthorPaymentsGroupList } from "../components";

export default function AuthorPaymentsPage() {
  const navigate = useNavigate();
  const {
    loading,
    authorGroups,
    page,
    totalPages,
    setPage,
    count,
    showAll,
    toggleShowAll,
    confirm,
    paying,
    openConfirm,
    closeConfirm,
    payAllUnpaidForAuthor,
  } = useAuthorPayments();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        title="Author Payments"
        subtitle="Grouped by author. Review unpaid royalties and mark them paid."
      >
        <Button variant="secondary" onClick={() => navigate("/sales")}>
          Sales Records
        </Button>
        <Button onClick={() => navigate("/sales/input")}>Input New Sales</Button>
      </PageHeader>

      {loading ? (
        <LoadingState message="Loading author payment data..." />
      ) : count === 0 ? (
        <Card>
          <CardContent>No author payment rows found.</CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent>
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="text-sm text-slate-600">
                <span className="font-semibold text-slate-900">{count}</span> author
                {count === 1 ? "" : "s"}
              </div>

              <ShowAllToggle showAll={showAll} onToggle={toggleShowAll} />
            </div>

            <AuthorPaymentsGroupList
              groups={authorGroups}
              onMarkAllPaid={openConfirm}
            />

            {!showAll && (
              <div className="mt-4">
                <Pagination
                  page={page}
                  totalPages={totalPages}
                  onPrev={() => setPage((p) => Math.max(1, p - 1))}
                  onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={confirm.open}
        title="Confirm marking payable sales as paid"
        body={
          confirm.author
            ? `This will mark all non-projected unpaid royalty records for ${confirm.author.name} as paid.`
            : ""
        }
        confirming={paying}
        onCancel={closeConfirm}
        onConfirm={payAllUnpaidForAuthor}
      />
    </div>
  );
}
