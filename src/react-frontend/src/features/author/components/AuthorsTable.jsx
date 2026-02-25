// src/features/authors/components/AuthorsTable.jsx
import React from "react";
import { TABLE_COLUMNS } from "../config/authorsTableConfig";
import { DataTable } from "../../../shared/components";

export default function AuthorsTable({ data, loading, ordering, onSort }) {
  return (
    <DataTable
      data={data}
      columns={TABLE_COLUMNS}
      loading={loading}
      ordering={ordering}
      onSort={onSort}
      emptyMessage="No authors found."
      loadingMessage="Loading author data..."
    />
  );
}