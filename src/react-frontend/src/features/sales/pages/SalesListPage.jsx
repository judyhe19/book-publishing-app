import { useNavigate } from "react-router-dom";
import React from "react";
import { useSalesList } from "../hooks/useSalesList";
import { Button } from "../../../shared/components/Button";
import { Card, CardContent } from "../../../shared/components/Card";

import SalesFilters from "../components/SalesFilters";
import SalesTable from "../components/SalesTable";

export default function SalesListPage() {
    const navigate = useNavigate();
    const {
        sales: sortedSales,
        loading,
        filters,
        handleSort,
        handleDateChange
    } = useSalesList();

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900">Sales Records</h1>
                    <p className="text-slate-500 mt-1">Manage and view your book sales.</p>
                </div>
                <Button onClick={() => navigate("/sales/create")}>
                    Input Sales
                </Button>
            </div>

            <Card>
                <CardContent>
                    <SalesFilters
                        filters={filters}
                        onDateChange={handleDateChange}
                    />
                    <SalesTable
                        data={sortedSales}
                        loading={loading}
                        ordering={filters.ordering}
                        onSort={handleSort}
                    />
                </CardContent>
            </Card>
        </div>
    );
}
