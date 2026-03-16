// src/features/sales/pages/SalesInputPage.jsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { Button, ErrorAlert } from "../../../shared/components";
import { useSalesInputPage } from "../hooks/useSalesInputPage";
import SaleInputRow from "../components/SaleInputRow";

export default function SalesInputPage() {
  const navigate = useNavigate();
  const { rows, isSubmitting, error, handleRowChange, handleRowBlur, handleRemoveRow, handleSubmit } =
    useSalesInputPage();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6 font-display">
        Sales Input Tool
      </h1>

      {error && (
        <ErrorAlert variant="leftBorder" className="mb-4">
          {error}
        </ErrorAlert>
      )}

      <div className="space-y-4">
        {rows.map((row, index) => (
          <SaleInputRow
            key={index}
            index={index}
            row={row}
            onChange={handleRowChange}
            onBlur={handleRowBlur}
            onRemove={handleRemoveRow}
            isFirst={index === 0}
          />
        ))}
      </div>

      <div className="mt-8 flex justify-end gap-4">
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting ? "Submitting..." : "Submit All Sales"}
        </Button>
      </div>
    </div>
  );
}
