// src/features/sales/components/SalesTable.jsx
import React from "react";
import { TABLE_COLUMNS } from "../config/salesTableConfig";
import { DataTable } from "../../../shared/components";

export default function SalesTable({ data, loading, ordering, onSort }) {
  return (
    <DataTable
      data={data}
      columns={TABLE_COLUMNS}
      loading={loading}
      ordering={ordering}
      onSort={onSort}
      emptyMessage="No sales found."
      loadingMessage="Loading sales data..."
    />
  );
}
