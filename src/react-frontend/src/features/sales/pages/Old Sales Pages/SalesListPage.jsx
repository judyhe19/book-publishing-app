import { useNavigate } from "react-router-dom";
import React, { useRef, useCallback } from "react";
import { useSalesList } from "../hooks/useSalesList";
import { Button } from "../../../shared/components/Button";
import { Card, CardContent } from "../../../shared/components/Card";

import SalesFilters from "../components/SalesFilters";
import SalesTable from "../components/SalesTable";
import SalesPagination from "../components/SalesPagination";

export default function SalesListPage() {
  const navigate = useNavigate();
  const {
    sales,
    loading,
    filters,
    handleSort,
    handleDateChange,

    // pagination + count
    page,
    totalPages,
    setPage,
    count,

    // show-all toggle
    showAll,
    toggleShowAll,
  } = useSalesList();

  // Synchronized scroll refs for top and bottom scrollbars
  const topScrollRef = useRef(null);
  const bottomScrollRef = useRef(null);

  const handleTopScroll = useCallback(() => {
    if (bottomScrollRef.current && topScrollRef.current) {
      bottomScrollRef.current.scrollLeft = topScrollRef.current.scrollLeft;
    }
  }, []);

  const handleBottomScroll = useCallback(() => {
    if (topScrollRef.current && bottomScrollRef.current) {
      topScrollRef.current.scrollLeft = bottomScrollRef.current.scrollLeft;
    }
  }, []);

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

          {/* Top scrollbar */}
          <div
            ref={topScrollRef}
            onScroll={handleTopScroll}
            className="mt-4 overflow-x-auto"
            style={{ height: "20px" }}
          >
            <div style={{ width: "1800px", height: "1px" }} />
          </div>

          {/* Table with bottom scrollbar */}
          <div
            ref={bottomScrollRef}
            onScroll={handleBottomScroll}
            className="overflow-x-auto"
          >
            <div style={{ minWidth: "1800px" }}>
              <SalesTable
                data={sales}
                loading={loading}
                ordering={filters.ordering}
                onSort={handleSort}
              />
            </div>
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
