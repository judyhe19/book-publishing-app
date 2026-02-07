import { useNavigate } from "react-router-dom";
import React from "react";
import { useSalesList } from "../hooks/useSalesList";
import { Button } from "../../../shared/components/Button";
import { Card, CardContent } from "../../../shared/components/Card";

import SalesFilters from "../components/SalesFilters";
import SalesTable from "../components/SalesTable";
import SalesPagination from "../components/SalesPagination"; // ✅ ADDED

export default function SalesListPage() {
  const navigate = useNavigate();
  const {
    sales,
    loading,
    filters,
    handleSort,
    handleDateChange,

    // ✅ pagination + count
    page,
    totalPages,
    setPage,
    count,

    // ✅ show-all toggle
    showAll,
    toggleShowAll,
  } = useSalesList();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Sales Records</h1>
          <p className="text-slate-500 mt-1">Manage and view your book sales.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate("/sales/authors")}>
            Author Payments
          </Button>
          <Button onClick={() => navigate("/sales/input")}>Input New Sales</Button>
        </div>
      </div>

      <Card>
        <CardContent>
          {/* Filters + Show All toggle */}
          <div className="flex items-center justify-between gap-3">
            <SalesFilters filters={filters} onDateChange={handleDateChange} />

            <Button variant="secondary" onClick={toggleShowAll}>
              {showAll ? "Paginate" : "Show all"}
            </Button>
          </div>

          {/* Table */}
          <div className="mt-4">
            <SalesTable
              data={sales}
              loading={loading}
              ordering={filters.ordering}
              onSort={handleSort}
            />
          </div>

          {/* Count + Pagination */}
          <div className="mt-4">
          {!showAll ? (
             <SalesPagination
             page={page}
             totalPages={totalPages}
             onPrev={() => setPage((p) => Math.max(1, p - 1))}
             onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
              />
          ) : null}
          </div>

        </CardContent>
      </Card>
    </div>
  );
}
