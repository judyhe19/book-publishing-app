// src/features/sales/pages/SalesListPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { useSalesList } from "../hooks/useSalesList";
import { SalesFilters, SalesTable } from "../components";
import {
  Button,
  Card,
  CardContent,
  Pagination,
  ShowAllToggle,
  DualScrollContainer,
} from "../../../shared/components";

export default function SalesListPage() {
  const navigate = useNavigate();
  const {
    sales,
    loading,
    filters,
    handleSort,
    handleDateChange,
    handleFilterChange,
    page,
    totalPages,
    setPage,
    showAll,
    toggleShowAll,
  } = useSalesList();

  return (
    <div className="p-6 max-w-full mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Sales Records</h1>
          <p className="text-slate-500 mt-1">Manage and view your book sales.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate("/sales/authors")}>
            Author Payments
          </Button>
          <Button variant="success" onClick={() => navigate("/sales/import-csv")}>
            Import from CSV
          </Button>
          <Button onClick={() => navigate("/sales/input")}>Input New Sales</Button>
        </div>
      </div>

      <Card>
        <CardContent>
          {/* Filters + Show All toggle */}
          <div className="flex items-center justify-between gap-3">
            <SalesFilters
              filters={filters}
              onDateChange={handleDateChange}
              onFilterChange={handleFilterChange}
            />
            <ShowAllToggle showAll={showAll} onToggle={toggleShowAll} />
          </div>

          <DualScrollContainer contentWidth={2200} className="mt-4">
            <SalesTable
              data={sales}
              loading={loading}
              ordering={filters.ordering}
              onSort={handleSort}
              onRowClick={(sale) => navigate(`/sale/${sale.id}?returnTo=${encodeURIComponent(window.location.pathname + window.location.search)}`)}
            />
          </DualScrollContainer>

          {/* Pagination */}
          <div className="mt-4">
            {!showAll && (
              <Pagination
                page={page}
                totalPages={totalPages}
                onPrev={() => setPage((p) => Math.max(1, p - 1))}
                onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
              />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
