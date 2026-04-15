// src/features/sales/pages/SalesListPage.jsx
import React, { useCallback } from "react";
import { useLocation } from "react-router-dom";
import { useSalesList } from "../hooks/useSalesList";
import { exportSalesCSV } from "../api/salesApi";
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
  const location = useLocation();
  const returnToParam = encodeURIComponent(location.pathname + location.search);
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

  const handleExportCSV = useCallback(async () => {
    const activeFilters = {};
    if (filters.start_date) activeFilters.start_date = filters.start_date;
    if (filters.end_date) activeFilters.end_date = filters.end_date;
    if (filters.author_name) activeFilters.author_name = filters.author_name;
    if (filters.sale_source) activeFilters.sale_source = filters.sale_source.toLowerCase();
    if (filters.distributor) activeFilters.distributor = filters.distributor;
    if (filters.format) activeFilters.sale_format = filters.format;
    if (filters.projected) activeFilters.projected = filters.projected;
    if (filters.ordering) activeFilters.ordering = filters.ordering;

    try {
      await exportSalesCSV(new URLSearchParams(activeFilters).toString());
    } catch (err) {
      console.error("CSV export failed:", err);
      alert("Failed to export CSV. Please try again.");
    }
  }, [filters]);

  return (
    <div className="p-6 max-w-full mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Sales Records</h1>
          <p className="text-slate-500 mt-1">Manage and view your book sales.</p>
        </div>
        <div className="flex gap-2">
          <Button
            className="bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-400"
            to="/sales/authors"
          >
            💰 Author Payments
          </Button>
          <Button variant="success" to="/sales/import-csv">
            Import from CSV
          </Button>
          <Button variant="success" to="/sales/import-xlsx">
            Import from XLSX
          </Button>
          <Button variant="success" to="/sales/import-backerkit">
            Import from Backerkit
          </Button>
          <Button variant="warning" onClick={handleExportCSV}>
            Export CSV
          </Button>
          <Button to="/sales/input">Input New Sales</Button>
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

          <DualScrollContainer contentWidth={1100} className="mt-4">
            <SalesTable
              data={sales}
              loading={loading}
              ordering={filters.ordering}
              onSort={handleSort}
              rowTo={(sale) => `/sale/${sale.id}?returnTo=${returnToParam}`}
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
